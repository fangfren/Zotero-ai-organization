#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / "output"
DEFAULT_ZOTERO_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Zotero"
DEFAULT_CATEGORY_CONFIG = PROJECT_ROOT / "config" / "categories.json"
NON_BIBLIOGRAPHIC_TYPES = {"attachment", "note", "annotation"}

ITEM_TYPE_LABELS = {
    "journalArticle": "期刊论文",
    "conferencePaper": "会议论文",
    "book": "书籍",
    "bookSection": "书籍章节",
    "report": "报告",
    "thesis": "学位论文",
    "webpage": "网页",
    "preprint": "预印本",
    "manuscript": "手稿",
    "patent": "专利",
    "document": "文档",
    "standalonePdf": "独立 PDF",
}

ANNOTATION_TYPE_LABELS = {
    1: "高亮",
    2: "注释",
    3: "图片",
    4: "墨迹",
    5: "下划线",
}

COMMON_ACRONYMS = {
    "AI",
    "DOI",
    "FIG",
    "HTTP",
    "HTTPS",
    "IEEE",
    "ISSN",
    "PDF",
    "TABLE",
    "URL",
}


@dataclass(slots=True)
class Attachment:
    item_id: int
    parent_item_id: int
    key: str
    content_type: str
    path: str
    date_added: str
    date_modified: str


@dataclass(slots=True)
class Annotation:
    item_id: int
    paper_item_id: int
    parent_item_id: int
    key: str
    annotation_type: int
    author_name: str
    text: str
    comment: str
    color: str
    page_label: str
    sort_index: str
    position: str


@dataclass(slots=True)
class Note:
    item_id: int
    paper_item_id: int
    title: str
    content: str
    date_added: str
    date_modified: str


@dataclass(slots=True)
class Item:
    item_id: int
    key: str
    item_type: str
    date_added: str
    date_modified: str
    fields: dict[str, str] = field(default_factory=dict)
    creators: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.fields.get("title") or self.fields.get("name") or "未命名条目"

    @property
    def year(self) -> str:
        value = self.fields.get("date", "")
        match = re.search(r"\b(18|19|20)\d{2}\b", value)
        return match.group(0) if match else ""

    @property
    def item_type_label(self) -> str:
        return ITEM_TYPE_LABELS.get(self.item_type, self.item_type)


@dataclass(slots=True)
class Category:
    id: str
    name: str
    description: str
    color: str
    keywords: list[str] = field(default_factory=list)
    item_ids: set[int] = field(default_factory=set)
    item_keys: set[str] = field(default_factory=set)
    source: str = "config"


ZOTERO_CATEGORY_COLORS = [
    "#3f7f76",
    "#b8792f",
    "#426da8",
    "#a24f70",
    "#5d7f39",
    "#7a5aa6",
    "#a5502f",
]


def zotero_category_color(name: str) -> str:
    total = sum(ord(char) for char in name)
    return ZOTERO_CATEGORY_COLORS[total % len(ZOTERO_CATEGORY_COLORS)]


def build_zotero_categories(items: dict[int, Item]) -> list[Category]:
    collection_names = sorted(
        {collection for item in items.values() for collection in item.collections}
    )
    return [
        Category(
            id=f"zotero:{name}",
            name=name,
            description="该分类直接来自 Zotero 集合。",
            color=zotero_category_color(name),
            source="zotero",
        )
        for name in collection_names
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a local Zotero library into a read-only research workbench."
    )
    parser.add_argument(
        "--zotero-dir",
        type=Path,
        default=DEFAULT_ZOTERO_DIR,
        help=f"Zotero data directory. Default: {DEFAULT_ZOTERO_DIR}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--library-id",
        type=int,
        default=1,
        help="Zotero library ID. The personal library is normally 1.",
    )
    parser.add_argument(
        "--categories",
        type=Path,
        default=DEFAULT_CATEGORY_CONFIG,
        help=f"Category configuration JSON. Default: {DEFAULT_CATEGORY_CONFIG}",
    )
    return parser.parse_args()


def load_categories(path: Path) -> tuple[list[Category], str]:
    if not path.is_file():
        example = path.with_name("categories.example.json")
        if example.is_file():
            path = example
        else:
            raise FileNotFoundError(f"Category configuration not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    categories = [
        Category(
            id=entry["id"],
            name=entry["name"],
            description=entry.get("description", ""),
            color=entry.get("color", "#6b7280"),
            keywords=[str(value) for value in entry.get("keywords", [])],
            item_ids={int(value) for value in entry.get("item_ids", [])},
            item_keys={str(value) for value in entry.get("item_keys", [])},
        )
        for entry in payload.get("categories", [])
    ]
    default_category_id = payload.get("default_category_id", "unsorted")
    if not categories:
        categories = [
            Category(
                id=default_category_id,
                name="待整理",
                description="尚未归类的条目",
                color="#6b7280",
            )
        ]
    return categories, default_category_id


def category_scores(item: Item, categories: list[Category]) -> dict[str, int]:
    text = " ".join(
        [
            item.title,
            item.fields.get("abstractNote", ""),
            *item.tags,
            *item.collections,
            *(annotation.comment for annotation in item.annotations),
        ]
    ).lower()
    scores: dict[str, int] = {}
    for category in categories:
        explicit = item.item_id in category.item_ids or item.key in category.item_keys
        score = sum(1 for keyword in category.keywords if keyword.lower() in text)
        if explicit:
            score += 100
        if score:
            scores[category.id] = score
    return scores


def assign_item_categories(
    items: dict[int, Item], categories: list[Category], default_category_id: str
) -> dict[int, list[str]]:
    category_ids = {category.id for category in categories}
    zotero_category_by_name = {
        category.name: category.id
        for category in categories
        if category.source == "zotero"
    }
    assignments: dict[int, list[str]] = {}
    for item in items.values():
        scores = category_scores(item, categories)
        zotero_ids = [
            zotero_category_by_name[collection]
            for collection in item.collections
            if collection in zotero_category_by_name
        ]
        regular_ids = [
            category_id
            for category_id, _ in sorted(
                scores.items(), key=lambda pair: (-pair[1], pair[0])
            )
            if category_id not in zotero_ids
        ]
        ordered = zotero_ids + regular_ids
        if not ordered:
            ordered = [
                default_category_id if default_category_id in category_ids else categories[0].id
            ]
        assignments[item.item_id] = ordered
    return assignments


def create_snapshot(zotero_dir: Path, cache_dir: Path) -> Path:
    source_path = zotero_dir / "zotero.sqlite"
    if not source_path.is_file():
        raise FileNotFoundError(f"Zotero database not found: {source_path}")

    cache_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = cache_dir / "zotero.snapshot.sqlite"
    for suffix in ("", "-wal", "-shm"):
        target = Path(str(snapshot_path) + suffix)
        if target.exists():
            target.unlink()
        candidate = Path(str(source_path) + suffix)
        if candidate.is_file():
            shutil.copy2(candidate, target)
    return snapshot_path


def fetch_rows(
    connection: sqlite3.Connection, query: str, parameters: tuple[object, ...] = ()
) -> list[sqlite3.Row]:
    return list(connection.execute(query, parameters))


def load_items(connection: sqlite3.Connection, library_id: int) -> dict[int, Item]:
    rows = fetch_rows(
        connection,
        """
        SELECT i.itemID, i.key, i.dateAdded, i.dateModified, it.typeName
        FROM items AS i
        JOIN itemTypes AS it ON it.itemTypeID = i.itemTypeID
        WHERE i.libraryID = ?
          AND it.typeName NOT IN ('attachment', 'note', 'annotation')
          AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
        ORDER BY i.itemID
        """,
        (library_id,),
    )
    items = {
        row["itemID"]: Item(
            item_id=row["itemID"],
            key=row["key"],
            item_type=row["typeName"],
            date_added=row["dateAdded"] or "",
            date_modified=row["dateModified"] or "",
        )
        for row in rows
    }
    if not items:
        return items

    item_ids = tuple(items)
    placeholders = ",".join("?" for _ in item_ids)

    for row in fetch_rows(
        connection,
        f"""
        SELECT id.itemID, f.fieldName, v.value
        FROM itemData AS id
        JOIN fields AS f ON f.fieldID = id.fieldID
        JOIN itemDataValues AS v ON v.valueID = id.valueID
        WHERE id.itemID IN ({placeholders})
        """,
        item_ids,
    ):
        items[row["itemID"]].fields[row["fieldName"]] = row["value"] or ""

    for row in fetch_rows(
        connection,
        f"""
        SELECT ic.itemID, c.firstName, c.lastName, ct.creatorType, ic.orderIndex
        FROM itemCreators AS ic
        JOIN creators AS c ON c.creatorID = ic.creatorID
        JOIN creatorTypes AS ct ON ct.creatorTypeID = ic.creatorTypeID
        WHERE ic.itemID IN ({placeholders})
        ORDER BY ic.itemID, ic.orderIndex
        """,
        item_ids,
    ):
        name = " ".join(
            part for part in (row["firstName"], row["lastName"]) if part
        ).strip()
        if name:
            items[row["itemID"]].creators.append(name)

    for row in fetch_rows(
        connection,
        f"""
        SELECT it.itemID, t.name
        FROM itemTags AS it
        JOIN tags AS t ON t.tagID = it.tagID
        WHERE it.itemID IN ({placeholders})
        ORDER BY t.name
        """,
        item_ids,
    ):
        items[row["itemID"]].tags.append(row["name"])

    collection_rows = fetch_rows(
        connection,
        """
        SELECT collectionID, collectionName, parentCollectionID
        FROM collections
        WHERE libraryID = ?
        """,
        (library_id,),
    )
    collections = {
        row["collectionID"]: (row["collectionName"], row["parentCollectionID"])
        for row in collection_rows
    }

    def collection_path(collection_id: int) -> str:
        parts: list[str] = []
        seen: set[int] = set()
        current: int | None = collection_id
        while current is not None and current not in seen:
            seen.add(current)
            value = collections.get(current)
            if value is None:
                break
            name, parent_id = value
            parts.append(name)
            current = parent_id
        return " / ".join(reversed(parts))

    attachments_by_parent: dict[int, list[Attachment]] = {}
    for row in fetch_rows(
        connection,
        f"""
        SELECT a.itemID, a.parentItemID, a.contentType, a.path, i.key,
               i.dateAdded, i.dateModified
        FROM itemAttachments AS a
        JOIN items AS i ON i.itemID = a.itemID
        WHERE a.parentItemID IN ({placeholders})
          AND a.itemID NOT IN (SELECT itemID FROM deletedItems)
        ORDER BY a.itemID
        """,
        item_ids,
    ):
        attachment = Attachment(
            item_id=row["itemID"],
            parent_item_id=row["parentItemID"],
            key=row["key"],
            content_type=row["contentType"] or "",
            path=row["path"] or "",
            date_added=row["dateAdded"] or "",
            date_modified=row["dateModified"] or "",
        )
        if attachment.parent_item_id not in items:
            continue
        attachments_by_parent.setdefault(attachment.parent_item_id, []).append(attachment)
        items[attachment.parent_item_id].attachments.append(attachment)

    attachment_to_paper = {
        attachment.item_id: attachment.parent_item_id
        for attachments in attachments_by_parent.values()
        for attachment in attachments
    }
    for row in fetch_rows(
        connection,
        """
        SELECT a.itemID, a.parentItemID, a.contentType, a.path, i.key,
               i.dateAdded, i.dateModified
        FROM itemAttachments AS a
        JOIN items AS i ON i.itemID = a.itemID
        WHERE (a.parentItemID IS NULL OR a.parentItemID = 0)
          AND a.itemID NOT IN (SELECT itemID FROM deletedItems)
          AND a.contentType = 'application/pdf'
        ORDER BY a.itemID
        """,
    ):
        standalone = Attachment(
            item_id=row["itemID"],
            parent_item_id=0,
            key=row["key"],
            content_type=row["contentType"] or "",
            path=row["path"] or "",
            date_added=row["dateAdded"] or "",
            date_modified=row["dateModified"] or "",
        )
        items[standalone.item_id] = Item(
            item_id=standalone.item_id,
            key=standalone.key,
            item_type="standalonePdf",
            date_added=standalone.date_added,
            date_modified=standalone.date_modified,
            fields={"title": attachment_title(standalone.path, standalone.key)},
        )
        attachment_to_paper[standalone.item_id] = standalone.item_id

    attachment_ids = tuple(attachment_to_paper)

    all_item_ids = tuple(items)
    all_placeholders = ",".join("?" for _ in all_item_ids)
    for row in fetch_rows(
        connection,
        f"""
        SELECT ci.itemID, c.collectionID
        FROM collectionItems AS ci
        JOIN collections AS c ON c.collectionID = ci.collectionID
        WHERE ci.itemID IN ({all_placeholders})
        ORDER BY c.collectionName
        """,
        all_item_ids,
    ):
        path = collection_path(row["collectionID"])
        if path:
            items[row["itemID"]].collections.append(path)

    if attachment_ids:
        attachment_placeholders = ",".join("?" for _ in attachment_ids)
        for row in fetch_rows(
            connection,
            f"""
            SELECT a.itemID, a.parentItemID, a.type, a.authorName, a.text, a.comment,
                   a.color, a.pageLabel, a.sortIndex, a.position, i.key
            FROM itemAnnotations AS a
            JOIN items AS i ON i.itemID = a.itemID
            WHERE a.parentItemID IN ({attachment_placeholders})
              AND a.itemID NOT IN (SELECT itemID FROM deletedItems)
            ORDER BY a.parentItemID, a.pageLabel, a.sortIndex
            """,
            attachment_ids,
        ):
            paper_id = attachment_to_paper.get(row["parentItemID"])
            if paper_id not in items:
                continue
            annotation = Annotation(
                item_id=row["itemID"],
                paper_item_id=paper_id,
                parent_item_id=row["parentItemID"],
                key=row["key"],
                annotation_type=row["type"] or 0,
                author_name=row["authorName"] or "",
                text=row["text"] or "",
                comment=row["comment"] or "",
                color=row["color"] or "",
                page_label=row["pageLabel"] or "",
                sort_index=row["sortIndex"] or "",
                position=row["position"] or "",
            )
            items[paper_id].annotations.append(annotation)

    parent_ids = item_ids + attachment_ids
    if parent_ids:
        parent_placeholders = ",".join("?" for _ in parent_ids)
        for row in fetch_rows(
            connection,
            f"""
            SELECT n.itemID, n.parentItemID, n.title, n.note, i.dateAdded, i.dateModified
            FROM itemNotes AS n
            JOIN items AS i ON i.itemID = n.itemID
            WHERE n.parentItemID IN ({parent_placeholders})
              AND n.itemID NOT IN (SELECT itemID FROM deletedItems)
            ORDER BY i.dateAdded
            """,
            parent_ids,
        ):
            parent_id = row["parentItemID"]
            paper_id = attachment_to_paper.get(parent_id, parent_id)
            if paper_id not in items:
                continue
            note = Note(
                item_id=row["itemID"],
                paper_item_id=paper_id,
                title=row["title"] or "",
                content=row["note"] or "",
                date_added=row["dateAdded"] or "",
                date_modified=row["dateModified"] or "",
            )
            items[paper_id].notes.append(note)

    return items


def clean_filename(value: str, fallback: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", value)
    value = re.sub(r"\s+", "-", value.strip())
    value = value.strip(".-_")
    if not value:
        value = fallback
    return value[:96]


def note_filename(item: Item) -> str:
    return f"{item.item_id:04d}-{clean_filename(item.title, item.key)}.md"


def quote_yaml(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_yaml_list(name: str, values: Iterable[str]) -> list[str]:
    values = list(values)
    if not values:
        return [f"{name}: []"]
    return [f"{name}:"] + [f"  - {quote_yaml(value)}" for value in values]


def annotation_label(annotation: Annotation) -> str:
    return ANNOTATION_TYPE_LABELS.get(annotation.annotation_type, "批注")


def attachment_title(path: str, key: str) -> str:
    value = re.sub(r"^(storage|attachments):", "", path or "").strip()
    filename = Path(value.replace("/", os.sep)).name if value else ""
    title = Path(filename).stem.strip()
    return title or f"独立 PDF {key}"


def render_markdown_block(value: str) -> list[str]:
    lines = value.strip().splitlines()
    if not lines:
        return []
    return ["> " + line if line else ">" for line in lines]


def render_manual_block(key: str, value: str) -> list[str]:
    return [
        f"<!-- manual:{key}:start -->",
        value,
        f"<!-- manual:{key}:end -->",
        "",
    ]


def read_manual_sections(note_path: Path) -> dict[str, str]:
    if not note_path.is_file():
        return {}
    content = note_path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    for key in ("understanding", "conclusions", "questions", "relevance"):
        match = re.search(
            rf"<!-- manual:{key}:start -->\n(.*?)\n<!-- manual:{key}:end -->",
            content,
            flags=re.DOTALL,
        )
        if match:
            sections[key] = match.group(1).strip()
    return sections


def render_note(item: Item, manual_sections: dict[str, str] | None = None) -> str:
    manual_sections = manual_sections or {}
    lines = [
        "---",
        f"zotero_item_id: {item.item_id}",
        f"zotero_key: {quote_yaml(item.key)}",
        f"item_type: {quote_yaml(item.item_type)}",
        f"year: {quote_yaml(item.year)}",
    ]
    lines.extend(render_yaml_list("authors", item.creators))
    lines.extend(render_yaml_list("tags", item.tags))
    lines.extend(render_yaml_list("collections", item.collections))
    lines.extend(
        [
            "---",
            "",
            f"# {item.title}",
            "",
            f"- 类型：{item.item_type_label}",
            f"- 作者：{', '.join(item.creators) if item.creators else '未记录'}",
            f"- 年份：{item.year or '未记录'}",
            f"- Zotero：[打开条目](zotero://select/library/items/{item.key})",
            f"- 附件数量：{len(item.attachments)}",
            f"- 批注数量：{len(item.annotations)}",
            "",
        ]
    )

    if item.tags:
        lines.extend(["标签：" + "、".join(f"`{tag}`" for tag in item.tags), ""])
    if item.collections:
        lines.extend(
            ["分类：" + "、".join(f"`{collection}`" for collection in item.collections), ""]
        )

    abstract = item.fields.get("abstractNote", "").strip()
    if abstract:
        lines.extend(["## 摘要", "", abstract, ""])

    lines.extend(["## Zotero 批注", ""])
    sorted_annotations = sorted(
        item.annotations,
        key=lambda annotation: (
            int(annotation.page_label)
            if annotation.page_label.isdigit()
            else 10**9,
            annotation.sort_index,
        ),
    )
    if not sorted_annotations:
        lines.extend(["_暂无批注_", ""])
    for annotation in sorted_annotations:
        page = f"第 {annotation.page_label} 页" if annotation.page_label else "未标页码"
        lines.extend([f"### {page} · {annotation_label(annotation)}", ""])
        if annotation.text:
            lines.extend(render_markdown_block(annotation.text))
            lines.append("")
        if annotation.comment:
            lines.extend([f"**批注：** {annotation.comment}", ""])

    if item.notes:
        lines.extend(["## Zotero 笔记", ""])
        for note in item.notes:
            if note.title:
                lines.extend([f"### {note.title}", ""])
            lines.extend([note.content.strip() or "_空笔记_", ""])

    lines.extend(
        [
            "## 我的理解",
            "",
            *render_manual_block(
                "understanding",
                manual_sections.get(
                    "understanding", "> 用自己的话解释这篇文献解决的问题。"
                ),
            ),
            "## 关键结论",
            "",
            *render_manual_block(
                "conclusions",
                manual_sections.get(
                    "conclusions", "> 只记录你能够复述并判断依据的结论。"
                ),
            ),
            "## 疑问",
            "",
            *render_manual_block(
                "questions",
                manual_sections.get(
                    "questions", "> 记录术语、公式、实验设计或结论中没看懂的地方。"
                ),
            ),
            "## 与研究方向的关系",
            "",
            *render_manual_block(
                "relevance",
                manual_sections.get(
                    "relevance",
                    "> 记录它可能如何影响 DFB 可靠性、光电测试或后续学习。",
                ),
            ),
        ]
    )
    return "\n".join(lines)


def render_literature_map(
    items: list[Item],
    categories: list[Category],
    item_categories: dict[int, list[str]],
) -> str:
    lines = [
        "# 文献地图",
        "",
        "该文件按 Zotero 集合与本地分类配置整理。",
        "",
    ]
    for category in categories:
        grouped = [
            item
            for item in items
            if item_categories.get(item.item_id, [category.id])[0] == category.id
        ]
        if not grouped:
            continue
        lines.extend([f"## {category.name}", "", category.description, ""])
        for item in sorted(grouped, key=lambda value: (value.year, value.title), reverse=True):
            note_path = f"notes/{note_filename(item)}"
            title = f"[{item.title}]({note_path})"
            lines.append(
                f"- {item.year or '年份未记录'} · **{title}** · "
                f"{len(item.annotations)} 条批注 · {item.item_type_label}"
            )
        lines.append("")
    if not items:
        lines.append("_暂无文献。_")
    return "\n".join(lines)


def extract_questions(items: list[Item]) -> str:
    lines = [
        "# 问题清单",
        "",
        "这里先自动收集批注中包含问号的文本，之后可以在下方补充自己的问题。",
        "",
        "## 来自 PDF 批注的候选问题",
        "",
    ]
    found = False
    for item in sorted(items, key=lambda value: value.title):
        for annotation in item.annotations:
            candidate = annotation.comment or annotation.text
            if "?" not in candidate and "？" not in candidate:
                continue
            found = True
            page = f"第 {annotation.page_label} 页" if annotation.page_label else "未标页码"
            lines.append(f"- [{item.title}](notes/{note_filename(item)})，{page}：{candidate}")
    if not found:
        lines.append("_暂未从批注中发现带问号的文本。_")
    lines.extend(
        [
            "",
            "## 我的问题",
            "",
            "- ",
            "",
            "## 可以询问导师的问题",
            "",
            "- ",
            "",
        ]
    )
    return "\n".join(lines)


def extract_acronyms(items: list[Item]) -> dict[str, dict[str, object]]:
    pattern = re.compile(r"\b[A-Z][A-Z0-9-]{1,7}\b")
    terms: dict[str, dict[str, object]] = {}
    for item in items:
        text_blocks = [item.title, item.fields.get("abstractNote", "")]
        text_blocks.extend(annotation.comment for annotation in item.annotations)
        for block in text_blocks:
            for term in pattern.findall(block or ""):
                term = term.strip("-")
                if term in COMMON_ACRONYMS or len(term) < 2:
                    continue
                entry = terms.setdefault(term, {"count": 0, "items": {}})
                entry["count"] = int(entry["count"]) + 1
                item_map = entry["items"]
                assert isinstance(item_map, dict)
                item_map[item.item_id] = item.title
    return terms


def render_glossary(items: list[Item]) -> str:
    terms = extract_acronyms(items)
    lines = [
        "# 术语表",
        "",
        "下面是当前摘要和批注中出现的候选缩写。定义必须由你核对文献后填写，工具不会自动编造解释。",
        "",
        "| 缩写 | 出现次数 | 出现文献 | 中文名称 | 我的解释 |",
        "|---|---:|---|---|---|",
    ]
    for term, data in sorted(
        terms.items(), key=lambda pair: (-int(pair[1]["count"]), pair[0])
    ):
        item_map = data["items"]
        assert isinstance(item_map, dict)
        sources = "、".join(item_map.values())
        lines.append(f"| {term} | {data['count']} | {sources} |  |  |")
    if not terms:
        lines.append("|  |  |  |  |  |")
    lines.append("")
    return "\n".join(lines)


def render_dashboard(
    items: list[Item],
    categories: list[Category],
    item_categories: dict[int, list[str]],
) -> str:
    category_by_id = {category.id: category for category in categories}
    default_category_id = categories[-1].id
    payload_items: list[dict[str, object]] = []
    category_counts = {category.id: 0 for category in categories}

    for item in items:
        assigned = [
            category_id
            for category_id in item_categories.get(item.item_id, [])
            if category_id in category_by_id
        ]
        if not assigned:
            assigned = [default_category_id]
        primary_id = assigned[0]
        primary = category_by_id[primary_id]
        category_counts[primary_id] += 1

        annotations = [
            {
                "page": annotation.page_label,
                "type": annotation_label(annotation),
                "text": annotation.text,
                "comment": annotation.comment,
                "color": annotation.color or "#d7a928",
            }
            for annotation in item.annotations
        ]
        search_text = " ".join(
            [
                item.title,
                *item.creators,
                item.year,
                primary.name,
                *(category_by_id[value].name for value in assigned),
                *item.tags,
                *item.collections,
                *(annotation.text for annotation in item.annotations),
                *(annotation.comment for annotation in item.annotations),
            ]
        ).lower()

        if item.annotations:
            status = "已批注"
        elif item.attachments or item.item_type == "standalonePdf":
            status = "待阅读"
        else:
            status = "待整理"

        payload_items.append(
            {
                "id": item.item_id,
                "key": item.key,
                "title": item.title,
                "authors": item.creators,
                "year": item.year,
                "type": item.item_type_label,
                "status": status,
                "primaryCategoryId": primary_id,
                "primaryCategoryName": primary.name,
                "primaryCategoryColor": primary.color,
                "categoryIds": assigned,
                "categoryNames": [category_by_id[value].name for value in assigned],
                "tags": item.tags,
                "collections": item.collections,
                "abstract": item.fields.get("abstractNote", ""),
                "url": item.fields.get("url", ""),
                "doi": item.fields.get("DOI", ""),
                "annotationCount": len(item.annotations),
                "annotations": annotations,
                "search": search_text,
            }
        )

    payload = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "items": payload_items,
        "categories": [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "source": category.source,
                "count": category_counts[category.id],
            }
            for category in categories
        ],
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Zotero 文献工作台</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f3f5f4;
      --sidebar: #e9eeeb;
      --surface: #ffffff;
      --surface-soft: #f8faf9;
      --text: #202624;
      --muted: #66716c;
      --line: #d7ded9;
      --accent: #276f5f;
      --accent-soft: #dcece7;
      --danger: #9b4b4b;
      --shadow: 0 10px 28px rgba(28, 43, 37, 0.08);
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #171b19;
        --sidebar: #1d2421;
        --surface: #222925;
        --surface-soft: #1c221f;
        --text: #edf2ef;
        --muted: #a7b2ad;
        --line: #39423e;
        --accent: #75c6ae;
        --accent-soft: #243c34;
        --danger: #e09090;
        --shadow: 0 14px 34px rgba(0, 0, 0, 0.28);
      }
    }
    * { box-sizing: border-box; }
    html { background: var(--bg); }
    body {
      margin: 0;
      min-width: 320px;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.6 system-ui, "Segoe UI", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }
    button, input, select { font: inherit; }
    button { color: inherit; }
    .app {
      display: grid;
      grid-template-columns: 272px minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 24px 18px;
      border-right: 1px solid var(--line);
      background: var(--sidebar);
    }
    .brand h1 {
      margin: 0;
      font-size: 21px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    .brand p {
      margin: 6px 0 20px;
      color: var(--muted);
      font-size: 13px;
    }
    .sidebar-label {
      margin: 22px 10px 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
      text-transform: uppercase;
    }
    .category-list {
      display: grid;
      gap: 5px;
    }
    .category-button {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      min-height: 42px;
      padding: 9px 10px;
      border: 1px solid transparent;
      border-radius: 8px;
      background: transparent;
      text-align: left;
      cursor: pointer;
    }
    .category-button:hover {
      background: color-mix(in srgb, var(--surface) 65%, transparent);
    }
    .category-button.active {
      border-color: var(--line);
      background: var(--surface);
      box-shadow: 0 3px 12px rgba(28, 43, 37, 0.06);
    }
    .category-dot {
      width: 9px;
      height: 9px;
      flex: 0 0 9px;
      border-radius: 50%;
      background: var(--category-color);
    }
    .category-name {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .category-count {
      margin-left: auto;
      color: var(--muted);
      font-size: 12px;
    }
    .main {
      min-width: 0;
      padding: 30px clamp(18px, 4vw, 52px) 56px;
    }
    .page-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 22px;
    }
    .page-header h1 {
      margin: 0 0 4px;
      font-size: 28px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    .page-header p {
      margin: 0;
      color: var(--muted);
    }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto auto auto;
      gap: 10px;
      align-items: center;
      margin-bottom: 18px;
    }
    .search {
      width: 100%;
      min-height: 42px;
      padding: 9px 13px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--text);
    }
    select {
      min-height: 42px;
      padding: 8px 32px 8px 11px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--text);
    }
    .toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      white-space: nowrap;
    }
    .toggle input {
      width: 16px;
      height: 16px;
      accent-color: var(--accent);
    }
    .result-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 13px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      gap: 14px;
    }
    .paper-card {
      display: flex;
      min-width: 0;
      min-height: 238px;
      flex-direction: column;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: 0 2px 8px rgba(28, 43, 37, 0.03);
      cursor: pointer;
      transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
    }
    .paper-card:hover {
      border-color: var(--primary-color);
      box-shadow: var(--shadow);
      transform: translateY(-1px);
    }
    .paper-card:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }
    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .category-chip,
    .status-chip,
    .type-chip {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      white-space: nowrap;
    }
    .category-chip {
      border: 1px solid color-mix(in srgb, var(--primary-color) 45%, var(--line));
      color: var(--primary-color);
      background: color-mix(in srgb, var(--primary-color) 9%, transparent);
    }
    .status-chip {
      border: 1px solid var(--line);
      color: var(--muted);
    }
    .type-chip {
      border: 1px solid var(--line);
      color: var(--muted);
    }
    .paper-card h2 {
      margin: 0;
      font-size: 18px;
      line-height: 1.38;
      letter-spacing: 0;
      overflow-wrap: anywhere;
    }
    .card-meta {
      margin-top: 7px;
      color: var(--muted);
      font-size: 13px;
    }
    .card-abstract {
      display: -webkit-box;
      margin: 12px 0 0;
      overflow: hidden;
      color: var(--muted);
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
    }
    .annotation-preview {
      display: grid;
      gap: 7px;
      margin-top: 14px;
    }
    .preview-block {
      min-width: 0;
      padding-left: 9px;
      border-left: 3px solid var(--annotation-color);
      color: var(--muted);
      font-size: 13px;
    }
    .preview-block p {
      display: -webkit-box;
      margin: 0;
      overflow: hidden;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }
    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: auto;
      padding-top: 15px;
      color: var(--muted);
      font-size: 12px;
    }
    .detail-button {
      min-height: 32px;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: var(--surface-soft);
      cursor: pointer;
    }
    .detail-button:hover {
      border-color: var(--accent);
      color: var(--accent);
    }
    .empty-state {
      grid-column: 1 / -1;
      padding: 46px 20px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      text-align: center;
    }
    dialog {
      width: min(940px, calc(100% - 28px));
      max-height: min(86vh, 900px);
      padding: 0;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--surface);
      color: var(--text);
      box-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
    }
    dialog::backdrop {
      background: rgba(11, 17, 15, 0.62);
      backdrop-filter: blur(3px);
    }
    .dialog-shell {
      display: flex;
      max-height: min(86vh, 900px);
      flex-direction: column;
    }
    .dialog-header {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      padding: 22px 24px 17px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
    }
    .dialog-header h2 {
      margin: 0;
      font-size: 23px;
      line-height: 1.35;
      letter-spacing: 0;
      overflow-wrap: anywhere;
    }
    .dialog-close {
      width: 34px;
      height: 34px;
      flex: 0 0 34px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      cursor: pointer;
    }
    .dialog-body {
      overflow: auto;
      padding: 22px 24px 30px;
    }
    .detail-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }
    .detail-section {
      margin-top: 24px;
    }
    .detail-section h3 {
      margin: 0 0 10px;
      font-size: 16px;
      letter-spacing: 0;
    }
    .abstract {
      margin: 0;
      color: var(--muted);
      white-space: pre-wrap;
    }
    .annotation-group {
      margin-top: 18px;
    }
    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }
    .annotation {
      padding: 13px 0 15px;
      border-top: 1px solid var(--line);
    }
    .annotation:first-of-type {
      border-top: 0;
    }
    .annotation-head {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .annotation-type {
      color: var(--annotation-color);
      font-weight: 650;
    }
    .annotation-highlight {
      margin: 0;
      padding: 11px 13px;
      border-left: 4px solid var(--annotation-color);
      background: var(--surface-soft);
      white-space: pre-wrap;
    }
    .annotation-comment {
      margin: 9px 0 0;
      color: var(--muted);
      white-space: pre-wrap;
    }
    .detail-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 18px;
    }
    .action-link {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 6px 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      color: var(--text);
      text-decoration: none;
    }
    .action-link:hover {
      border-color: var(--accent);
      color: var(--accent);
    }
    @media (max-width: 900px) {
      .app { display: block; }
      .sidebar {
        position: static;
        width: 100%;
        height: auto;
        padding: 18px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .brand p { margin-bottom: 14px; }
      .sidebar-label { margin-top: 14px; }
      .category-list {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 4px;
      }
      .category-button {
        width: auto;
        min-width: max-content;
      }
      .main { padding: 22px 16px 44px; }
      .page-header h1 { font-size: 24px; }
      .toolbar { grid-template-columns: 1fr 1fr; }
      .search { grid-column: 1 / -1; }
      .toggle { justify-content: center; }
    }
    @media (max-width: 560px) {
      .toolbar { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .dialog-header,
      .dialog-body { padding-left: 17px; padding-right: 17px; }
      .dialog-header h2 { font-size: 20px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>文献工作台</h1>
        <p>最后同步：__GENERATED_AT__</p>
      </div>
      <div class="sidebar-label">分类</div>
      <nav class="category-list" id="category-list" aria-label="文献分类"></nav>
    </aside>
    <main class="main">
      <div class="page-header">
        <div>
          <h1 id="page-title">全部文献</h1>
          <p id="page-description">按分类浏览、搜索和查看批注。</p>
        </div>
      </div>
      <div class="toolbar">
        <input id="search" class="search" type="search" placeholder="搜索标题、作者、批注或分类">
        <select id="type-filter" aria-label="文献类型"></select>
        <select id="sort-order" aria-label="排序方式">
          <option value="category">按分类排序</option>
          <option value="year">按年份排序</option>
          <option value="annotations">按批注数量排序</option>
          <option value="title">按标题排序</option>
        </select>
        <label class="toggle">
          <input id="annotated-only" type="checkbox">
          只看已批注
        </label>
      </div>
      <div class="result-line">
        <span id="result-count"></span>
        <span id="active-filter"></span>
      </div>
      <section class="grid" id="paper-grid" aria-live="polite"></section>
    </main>
  </div>

  <dialog id="detail-dialog">
    <div class="dialog-shell">
      <div class="dialog-header">
        <h2 id="detail-title"></h2>
        <button class="dialog-close" id="dialog-close" type="button" aria-label="关闭详情">×</button>
      </div>
      <div class="dialog-body" id="detail-body"></div>
    </div>
  </dialog>

  <script>
    const DATA = __DATA__;
    const state = {
      category: "all",
      type: "all",
      sort: "category",
      annotatedOnly: false,
      query: ""
    };

    const categoryOrder = Object.fromEntries(
      DATA.categories.map((category, index) => [category.id, index])
    );
    const grid = document.querySelector("#paper-grid");
    const categoryList = document.querySelector("#category-list");
    const searchInput = document.querySelector("#search");
    const typeFilter = document.querySelector("#type-filter");
    const sortOrder = document.querySelector("#sort-order");
    const annotatedOnly = document.querySelector("#annotated-only");
    const pageTitle = document.querySelector("#page-title");
    const pageDescription = document.querySelector("#page-description");
    const resultCount = document.querySelector("#result-count");
    const activeFilter = document.querySelector("#active-filter");
    const dialog = document.querySelector("#detail-dialog");
    const detailTitle = document.querySelector("#detail-title");
    const detailBody = document.querySelector("#detail-body");

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function categoryById(id) {
      return DATA.categories.find((category) => category.id === id);
    }

    function renderCategories() {
      const allCount = DATA.items.length;
      const buttons = [
        `<button class="category-button" type="button" data-category="all">
          <span class="category-dot" style="--category-color:#52645d"></span>
          <span class="category-name">全部文献</span>
          <span class="category-count">${allCount}</span>
        </button>`
      ];
      for (const category of DATA.categories) {
        buttons.push(
          `<button class="category-button" type="button" data-category="${escapeHtml(category.id)}" title="${escapeHtml(category.description)}">
            <span class="category-dot" style="--category-color:${escapeHtml(category.color)}"></span>
            <span class="category-name">${escapeHtml(category.name)}</span>
            <span class="category-count">${category.count}</span>
          </button>`
        );
      }
      categoryList.innerHTML = buttons.join("");
    }

    function renderTypeFilter() {
      const types = [...new Set(DATA.items.map((item) => item.type))].sort();
      typeFilter.innerHTML = [
        `<option value="all">全部类型</option>`,
        ...types.map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`)
      ].join("");
    }

    function setActiveCategoryButton() {
      for (const button of categoryList.querySelectorAll(".category-button")) {
        button.classList.toggle("active", button.dataset.category === state.category);
      }
    }

    function previewText(annotation) {
      return annotation.comment || annotation.text || "无文字内容";
    }

    function paperCard(item) {
      const previews = item.annotations.slice(0, 2).map((annotation) => `
        <div class="preview-block" style="--annotation-color:${escapeHtml(annotation.color)}">
          <p>${escapeHtml(previewText(annotation))}</p>
        </div>
      `).join("");
      const authors = item.authors.length ? item.authors.join("、") : "作者未记录";
      return `
        <article class="paper-card" tabindex="0" role="button" data-id="${item.id}" style="--primary-color:${escapeHtml(item.primaryCategoryColor)}">
          <div class="card-top">
            <span class="category-chip">${escapeHtml(item.primaryCategoryName)}</span>
            <span class="status-chip">${escapeHtml(item.status)}</span>
          </div>
          <h2>${escapeHtml(item.title)}</h2>
          <div class="card-meta">${escapeHtml(item.year || "年份未记录")} · ${escapeHtml(authors)} · ${escapeHtml(item.type)}</div>
          ${item.abstract ? `<p class="card-abstract">${escapeHtml(item.abstract)}</p>` : ""}
          ${previews ? `<div class="annotation-preview">${previews}</div>` : ""}
          <div class="card-footer">
            <span>${item.annotationCount} 条批注</span>
            <button class="detail-button" type="button" data-open="${item.id}">查看详情</button>
          </div>
        </article>
      `;
    }

    function matches(item) {
      if (state.category !== "all" && !item.categoryIds.includes(state.category)) return false;
      if (state.type !== "all" && item.type !== state.type) return false;
      if (state.annotatedOnly && item.annotationCount === 0) return false;
      if (state.query && !item.search.includes(state.query)) return false;
      return true;
    }

    function sortItems(items) {
      return [...items].sort((left, right) => {
        if (state.sort === "year") {
          return (right.year || "0000").localeCompare(left.year || "0000");
        }
        if (state.sort === "annotations") {
          return right.annotationCount - left.annotationCount || left.title.localeCompare(right.title);
        }
        if (state.sort === "title") {
          return left.title.localeCompare(right.title, "zh-CN");
        }
        const categoryDelta =
          (categoryOrder[left.primaryCategoryId] ?? 999) -
          (categoryOrder[right.primaryCategoryId] ?? 999);
        return categoryDelta || (right.year || "0000").localeCompare(left.year || "0000");
      });
    }

    function updateHeader(filteredItems) {
      const category = state.category === "all" ? null : categoryById(state.category);
      pageTitle.textContent = category ? category.name : "全部文献";
      pageDescription.textContent = category
        ? category.description
        : "按分类浏览、搜索和查看批注。";
      resultCount.textContent = `${filteredItems.length} / ${DATA.items.length} 篇文献`;
      const active = [];
      if (state.type !== "all") active.push(state.type);
      if (state.annotatedOnly) active.push("已批注");
      if (state.query) active.push(`搜索：${state.query}`);
      activeFilter.textContent = active.join(" · ");
      setActiveCategoryButton();
    }

    function render() {
      const filtered = sortItems(DATA.items.filter(matches));
      updateHeader(filtered);
      grid.innerHTML = filtered.length
        ? filtered.map(paperCard).join("")
        : `<div class="empty-state">没有符合当前条件的文献。</div>`;
    }

    function annotationGroups(item) {
      const groups = new Map();
      for (const annotation of item.annotations) {
        const page = annotation.page || "未标页码";
        if (!groups.has(page)) groups.set(page, []);
        groups.get(page).push(annotation);
      }
      return groups;
    }

    function openDetail(item) {
      detailTitle.textContent = item.title;
      const authors = item.authors.length ? item.authors.join("、") : "作者未记录";
      const groups = annotationGroups(item);
      const annotationHtml = groups.size
        ? [...groups.entries()].map(([page, annotations]) => `
            <section class="annotation-group">
              <h3 class="page-title">第 ${escapeHtml(page)} 页</h3>
              ${annotations.map((annotation) => `
                <article class="annotation" style="--annotation-color:${escapeHtml(annotation.color)}">
                  <div class="annotation-head">
                    <span class="annotation-type">${escapeHtml(annotation.type)}</span>
                  </div>
                  ${annotation.text ? `<p class="annotation-highlight">${escapeHtml(annotation.text)}</p>` : ""}
                  ${annotation.comment ? `<p class="annotation-comment">批注：${escapeHtml(annotation.comment)}</p>` : ""}
                </article>
              `).join("")}
            </section>
          `).join("")
        : `<p class="abstract">暂无 PDF 批注。</p>`;

      detailBody.innerHTML = `
        <div class="detail-meta">
          <span class="category-chip" style="--primary-color:${escapeHtml(item.primaryCategoryColor)}">${escapeHtml(item.primaryCategoryName)}</span>
          <span class="type-chip">${escapeHtml(item.year || "年份未记录")}</span>
          <span class="type-chip">${escapeHtml(item.type)}</span>
          <span class="type-chip">${item.annotationCount} 条批注</span>
        </div>
        <p class="abstract">${escapeHtml(authors)}</p>
        ${item.abstract ? `<section class="detail-section"><h3>摘要</h3><p class="abstract">${escapeHtml(item.abstract)}</p></section>` : ""}
        <section class="detail-section">
          <h3>PDF 批注</h3>
          ${annotationHtml}
        </section>
        <div class="detail-actions">
          <a class="action-link" href="zotero://select/library/items/${encodeURIComponent(item.key)}">在 Zotero 中打开</a>
          ${item.url ? `<a class="action-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">打开原文</a>` : ""}
          ${item.doi ? `<a class="action-link" href="https://doi.org/${encodeURIComponent(item.doi)}" target="_blank" rel="noopener noreferrer">DOI</a>` : ""}
        </div>
      `;
      dialog.showModal();
    }

    categoryList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-category]");
      if (!button) return;
      state.category = button.dataset.category;
      render();
    });

    grid.addEventListener("click", (event) => {
      const button = event.target.closest("[data-open]");
      const card = event.target.closest("[data-id]");
      const id = Number(button?.dataset.open || card?.dataset.id);
      if (id) openDetail(DATA.items.find((item) => item.id === id));
    });

    grid.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const card = event.target.closest("[data-id]");
      if (!card) return;
      event.preventDefault();
      openDetail(DATA.items.find((item) => item.id === Number(card.dataset.id)));
    });

    searchInput.addEventListener("input", () => {
      state.query = searchInput.value.trim().toLowerCase();
      render();
    });
    typeFilter.addEventListener("change", () => {
      state.type = typeFilter.value;
      render();
    });
    sortOrder.addEventListener("change", () => {
      state.sort = sortOrder.value;
      render();
    });
    annotatedOnly.addEventListener("change", () => {
      state.annotatedOnly = annotatedOnly.checked;
      render();
    });
    document.querySelector("#dialog-close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });

    renderCategories();
    renderTypeFilter();
    render();
  </script>
</body>
</html>
"""
    return template.replace("__DATA__", data_json).replace(
        "__GENERATED_AT__", payload["generatedAt"]
    )


def render_output_readme(output_dir: Path, items: list[Item]) -> str:
    annotation_count = sum(len(item.annotations) for item in items)
    return f"""# Research Workbench Output

Generated from the local Zotero library.

- Items: {len(items)}
- PDF annotations: {annotation_count}
- Output directory: `{output_dir}`

## Start here

- `dashboard/index.html`: primary interface with categories, search, filters, and full annotations
- `literature-map.md`: category-grouped literature overview
- `notes/`: Markdown archive and editable manual notes
- `glossary.md`: candidate terms collected from abstracts and annotations
- `questions.md`: candidate questions and manual question sections

Edit `config/categories.json` to change categories, descriptions, colors, keywords, or item assignments.
The manual sections in `notes/*.md` are preserved when this command is run again.
"""


def item_json(
    item: Item,
    note_path: str,
    categories: list[Category],
    item_categories: dict[int, list[str]],
) -> dict[str, object]:
    category_by_id = {category.id: category for category in categories}
    assigned = item_categories.get(item.item_id, [])
    return {
        "zotero_item_id": item.item_id,
        "zotero_key": item.key,
        "title": item.title,
        "item_type": item.item_type,
        "authors": item.creators,
        "year": item.year,
        "tags": item.tags,
        "collections": item.collections,
        "abstract": item.fields.get("abstractNote", ""),
        "url": item.fields.get("url", ""),
        "doi": item.fields.get("DOI", ""),
        "note_file": note_path,
        "category_ids": assigned,
        "category_names": [
            category_by_id[value].name for value in assigned if value in category_by_id
        ],
        "attachment_count": len(item.attachments),
        "annotation_count": len(item.annotations),
        "annotations": [
            {
                "type": annotation.annotation_type,
                "page": annotation.page_label,
                "text": annotation.text,
                "comment": annotation.comment,
                "color": annotation.color,
            }
            for annotation in item.annotations
        ],
    }


def category_dict(category: Category) -> dict[str, Any]:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "keywords": list(category.keywords),
        "item_ids": sorted(category.item_ids),
        "item_keys": sorted(category.item_keys),
        "source": category.source,
    }


def write_output(
    output_dir: Path,
    items: list[Item],
    snapshot_path: Path,
    categories: list[Category],
    item_categories: dict[int, list[str]],
    default_category_id: str,
) -> None:
    notes_dir = output_dir / "notes"
    dashboard_dir = output_dir / "dashboard"
    data_dir = output_dir / "data"
    for directory in (notes_dir, dashboard_dir, data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for item in items:
        note_path = notes_dir / note_filename(item)
        manual_sections = read_manual_sections(note_path)
        note_path.write_text(
            render_note(item, manual_sections), encoding="utf-8"
        )

    (output_dir / "literature-map.md").write_text(
        render_literature_map(items, categories, item_categories), encoding="utf-8"
    )
    (output_dir / "questions.md").write_text(
        extract_questions(items), encoding="utf-8"
    )
    (output_dir / "glossary.md").write_text(
        render_glossary(items), encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        render_output_readme(output_dir, items), encoding="utf-8"
    )
    (dashboard_dir / "index.html").write_text(
        render_dashboard(items, categories, item_categories), encoding="utf-8"
    )

    library_json = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "snapshot": str(snapshot_path),
        "item_count": len(items),
        "annotation_count": sum(len(item.annotations) for item in items),
        "note_count": sum(len(item.notes) for item in items),
        "categories": [category_dict(category) for category in categories],
        "items": [
            item_json(
                item,
                f"notes/{note_filename(item)}",
                categories,
                item_categories,
            )
            for item in sorted(items, key=lambda value: value.item_id)
        ],
    }
    (data_dir / "library.json").write_text(
        json.dumps(library_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    runtime_categories = {
        "default_category_id": default_category_id,
        "source_mode": "zotero"
        if any(category.source == "zotero" for category in categories)
        else "config",
        "categories": [category_dict(category) for category in categories],
    }
    (data_dir / "categories.runtime.json").write_text(
        json.dumps(runtime_categories, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output.resolve()
    cache_dir = PROJECT_ROOT / ".cache"

    snapshot_path = create_snapshot(args.zotero_dir.resolve(), cache_dir)
    connection = sqlite3.connect(snapshot_path)
    connection.row_factory = sqlite3.Row
    try:
        items_by_id = load_items(connection, args.library_id)
    finally:
        connection.close()

    items = list(items_by_id.values())
    config_categories, default_category_id = load_categories(
        args.categories.resolve()
    )
    zotero_categories = build_zotero_categories(items_by_id)
    categories = zotero_categories + config_categories
    item_categories = assign_item_categories(
        items_by_id, categories, default_category_id
    )
    write_output(
        output_dir,
        items,
        snapshot_path,
        categories,
        item_categories,
        default_category_id,
    )

    annotation_count = sum(len(item.annotations) for item in items)
    note_count = sum(len(item.notes) for item in items)
    print(f"Exported {len(items)} items, {annotation_count} annotations, {note_count} notes.")
    print(f"Output: {output_dir}")
    print(f"Dashboard: {output_dir / 'dashboard' / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
