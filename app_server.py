#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import sync_zotero


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_FILE = OUTPUT_DIR / "data" / "library.json"
RUNTIME_CATEGORY_FILE = OUTPUT_DIR / "data" / "categories.runtime.json"
DASHBOARD_FILE = OUTPUT_DIR / "dashboard" / "index.html"
APP_DIR = PROJECT_ROOT / "app"
CATEGORY_FILE = PROJECT_ROOT / "config" / "categories.json"
AI_CONFIG_FILE = PROJECT_ROOT / "config" / "ai.json"
REPORTS_DIR = OUTPUT_DIR / "reports"
HOST = "127.0.0.1"
PORT = 5187


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.is_file():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_library() -> dict[str, Any]:
    return read_json_file(DATA_FILE, {})


def load_categories() -> dict[str, Any]:
    if RUNTIME_CATEGORY_FILE.is_file():
        return read_json_file(
            RUNTIME_CATEGORY_FILE,
            {"default_category_id": "unsorted", "categories": []},
        )
    category_file = (
        CATEGORY_FILE
        if CATEGORY_FILE.is_file()
        else CATEGORY_FILE.with_name("categories.example.json")
    )
    return read_json_file(
        category_file,
        {"default_category_id": "unsorted", "categories": []},
    )


def load_ai_config() -> dict[str, Any]:
    ai_file = (
        AI_CONFIG_FILE
        if AI_CONFIG_FILE.is_file()
        else AI_CONFIG_FILE.with_name("ai.example.json")
    )
    return read_json_file(
        ai_file,
        {
            "provider": "codex",
            "base_url": "https://api.openai.com/v1/chat/completions",
            "model": "",
            "api_key": "",
        },
    )


def ai_status() -> dict[str, Any]:
    config = load_ai_config()
    provider = str(config.get("provider", "codex"))
    key = config.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "") or os.environ.get(
        "AI_API_KEY", ""
    )
    codex_configured = provider == "codex" and find_codex() is not None
    api_configured = provider == "api" and bool(
        config.get("base_url") and config.get("model") and key
    )
    return {
        "configured": codex_configured or api_configured,
        "provider": provider,
        "codex_available": codex_configured,
        "base_url": config.get("base_url", ""),
        "model": config.get("model", ""),
        "has_key": bool(key),
        "api_key_env": bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("AI_API_KEY")
        ),
    }


def find_codex() -> str | None:
    executable = shutil.which("codex")
    if executable:
        return executable
    codex_dir = Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin"
    if codex_dir.is_dir():
        candidates = sorted(codex_dir.glob("codex.exe"))
        if candidates:
            return str(candidates[-1])
    return None


def run_sync() -> dict[str, Any]:
    command = [sys.executable, str(PROJECT_ROOT / "sync_zotero.py")]
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "Zotero sync timed out."}


def find_item(item_id: int) -> dict[str, Any] | None:
    library = load_library()
    for item in library.get("items", []):
        if item.get("zotero_item_id") == item_id:
            return item
    return None


def get_note_path(item_id: int) -> Path | None:
    item = find_item(item_id)
    if not item:
        return None
    return OUTPUT_DIR / str(item.get("note_file", ""))


def get_manual_sections(item_id: int) -> dict[str, str]:
    note_path = get_note_path(item_id)
    if not note_path or not note_path.is_file():
        return {}
    return sync_zotero.read_manual_sections(note_path)


def update_manual_sections(
    note_path: Path, manual_sections: dict[str, str]
) -> None:
    if not note_path.is_file():
        raise FileNotFoundError(f"Note not found: {note_path}")
    content = note_path.read_text(encoding="utf-8")
    for key, value in manual_sections.items():
        pattern = re.compile(
            rf"<!-- manual:{key}:start -->\n.*?\n<!-- manual:{key}:end -->",
            flags=re.DOTALL,
        )
        replacement = (
            f"<!-- manual:{key}:start -->\n{value.strip()}\n"
            f"<!-- manual:{key}:end -->"
        )
        if pattern.search(content):
            content = pattern.sub(replacement, content)
    note_path.write_text(content, encoding="utf-8")


def save_categories(payload: dict[str, Any]) -> dict[str, Any]:
    categories = payload.get("categories", [])
    seen: set[str] = set()
    for category in categories:
        category_id = str(category.get("id", "")).strip()
        if not category_id or category_id in seen:
            raise ValueError("Category ids must be unique and non-empty.")
        seen.add(category_id)
        category["item_ids"] = sorted(
            {
                int(value)
                for value in category.get("item_ids", [])
                if str(value).strip()
            }
        )
        category["item_keys"] = sorted(
            {
                str(value).strip()
                for value in category.get("item_keys", [])
                if str(value).strip()
            }
        )
        category["keywords"] = [
            str(value).strip()
            for value in category.get("keywords", [])
            if str(value).strip()
        ]
    normalized = {
        "default_category_id": str(
            payload.get("default_category_id", "unsorted")
        ).strip(),
        "categories": categories,
    }
    if normalized["default_category_id"] not in seen:
        raise ValueError("default_category_id must be one of the category ids.")
    write_json_file(CATEGORY_FILE, normalized)
    return normalized


def update_item_categories(
    item_id: int, category_ids: list[str]
) -> dict[str, Any]:
    payload = load_categories()
    valid_ids = {str(category["id"]) for category in payload["categories"]}
    selected = [category_id for category_id in category_ids if category_id in valid_ids]
    for category in payload["categories"]:
        category_id = str(category["id"])
        item_ids = {int(value) for value in category.get("item_ids", [])}
        if category_id in selected:
            item_ids.add(item_id)
        else:
            item_ids.discard(item_id)
        category["item_ids"] = sorted(item_ids)
    write_json_file(CATEGORY_FILE, payload)
    return payload


def item_category_names(item: dict[str, Any]) -> list[str]:
    return list(item.get("category_names", []))


def annotation_blocks(item: dict[str, Any]) -> list[str]:
    blocks: list[str] = []
    for annotation in item.get("annotations", []):
        page = annotation.get("page", "") or "未标页码"
        text = (annotation.get("text") or "").strip()
        comment = (annotation.get("comment") or "").strip()
        parts = [f"第 {page} 页"]
        if text:
            parts.append(text)
        if comment:
            parts.append(f"批注：{comment}")
        blocks.append("；".join(parts))
    return blocks


def build_report_markdown(
    item_ids: list[int] | None,
    instruction: str,
) -> str:
    library = load_library()
    items = library.get("items", [])
    selected = [
        item for item in items if not item_ids or item.get("zotero_item_id") in item_ids
    ]
    lines = [
        "# DFB 文献研究报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    if instruction.strip():
        lines.extend(["## 报告要求", "", instruction.strip(), ""])

    categories = load_categories().get("categories", [])
    lines.extend(["## 分类概览", "", "| 分类 | 文献数 | 批注数 |", "|---:|---:|---:|"])
    for category in categories:
        category_id = str(category["id"])
        category_items = [
            item
            for item in selected
            if item.get("category_ids") and item["category_ids"][0] == category_id
        ]
        annotation_count = sum(
            item.get("annotation_count", 0) for item in category_items
        )
        lines.append(
            f"| {category['name']} | {len(category_items)} | {annotation_count} |"
        )
    lines.append("")

    for item in sorted(
        selected,
        key=lambda value: (
            str(value.get("year", "")) or "0000",
            str(value.get("title", "")),
        ),
        reverse=True,
    ):
        lines.extend(
            [
                f"## {item.get('title', '未命名条目')}",
                "",
                f"- 年份：{item.get('year') or '未记录'}",
                f"- 分类：{'、'.join(item_category_names(item)) or '待整理'}",
                f"- 类型：{item.get('item_type', '')}",
                f"- 批注：{item.get('annotation_count', 0)} 条",
                "",
            ]
        )
        abstract = (item.get("abstract") or "").strip()
        if abstract:
            lines.extend(["### 摘要", "", abstract, ""])
        annotations = annotation_blocks(item)
        if annotations:
            lines.extend(["### 批注摘要", ""])
            lines.extend(f"- {block}" for block in annotations)
            lines.append("")
        manual = get_manual_sections(int(item["zotero_item_id"]))
        if manual:
            lines.extend(["### 整理笔记", ""])
            for label, key in [
                ("我的理解", "understanding"),
                ("关键结论", "conclusions"),
                ("疑问", "questions"),
                ("与研究方向的关系", "relevance"),
            ]:
                value = manual.get(key, "").strip()
                if value:
                    lines.extend([f"**{label}**", "", value, ""])
    return "\n".join(lines)


def call_ai(report_markdown: str, instruction: str) -> dict[str, Any]:
    config = load_ai_config()
    provider = str(config.get("provider", "codex"))
    if provider == "codex":
        return call_codex(report_markdown, instruction)
    return call_api(report_markdown, instruction)


def call_codex(report_markdown: str, instruction: str) -> dict[str, Any]:
    executable = find_codex()
    if not executable:
        return {
            "configured": False,
            "ai_used": False,
            "message": "未找到 Codex CLI，请检查 Codex 是否安装，或切换到 API 模式。",
            "report": report_markdown,
        }

    system_prompt = (
        "你是科研文献整理助手，负责把 Zotero 元数据、摘要、批注和用户笔记整理成"
        "逻辑清晰、可复述、区分事实与推断的中文研究报告。不得编造文献中没有的数据。"
    )
    user_prompt = (
        f"请按照以下要求改进报告质量：{instruction or '整理为结构清晰的中文研究报告'}\n\n"
        f"原始材料：\n{report_markdown}"
    )
    prompt = f"{system_prompt}\n\n{user_prompt}"
    output_dir = OUTPUT_DIR / "codex-tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S%f')}.md"
    command = [
        executable,
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--color",
        "never",
        "-s",
        "read-only",
        "-o",
        str(output_path),
        "-",
    ]
    try:
        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "Codex 执行失败").strip()
            if "readonly database" in message:
                message = (
                    "Codex CLI 没有权限访问 Codex 状态目录。请通过 open-desktop.cmd "
                    "启动应用后再试，或改用 API 模式。"
                )
            return {
                "configured": True,
                "ai_used": False,
                "message": f"Codex 返回错误：{message[:2000]}",
                "report": report_markdown,
            }
        content = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
        content = content.strip()
        if not content:
            content = result.stdout.strip()
        if not content:
            return {
                "configured": True,
                "ai_used": False,
                "message": "Codex 没有生成内容。",
                "report": report_markdown,
            }
        return {
            "configured": True,
            "ai_used": True,
            "message": "Codex 报告生成完成。",
            "report": content,
        }
    except subprocess.TimeoutExpired:
        return {
            "configured": True,
            "ai_used": False,
            "message": "Codex 生成超时。",
            "report": report_markdown,
        }
    except Exception as error:
        return {
            "configured": True,
            "ai_used": False,
            "message": f"Codex 请求失败：{error}",
            "report": report_markdown,
        }
    finally:
        if output_path.exists():
            output_path.unlink()


def call_api(report_markdown: str, instruction: str) -> dict[str, Any]:
    config = load_ai_config()
    key = config.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "") or os.environ.get(
        "AI_API_KEY", ""
    )
    base_url = config.get("base_url", "").strip()
    model = config.get("model", "").strip()
    if not base_url or not model or not key:
        return {
            "configured": False,
            "ai_used": False,
            "message": "API 尚未配置：请打开“AI 设置”选择 API 模式并填写模型、接口地址和密钥。",
            "report": report_markdown,
        }

    system_prompt = (
        "你是一个 DFB 激光器、光电传感与科研文献整理助手。"
        "根据用户提供的 Zotero 文献数据和整理笔记，生成逻辑清晰、区分事实与推断的中文报告。"
        "不要编造文献中没有的实验数据和结论。"
    )
    user_prompt = (
        f"请按照以下要求改进报告质量：{instruction or '整理为结构清晰的中文研究报告'}\n\n"
        f"原始材料：\n{report_markdown}"
    )
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        base_url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        return {
            "configured": True,
            "ai_used": True,
            "message": "AI 报告生成完成。",
            "report": content,
        }
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:2000]
        return {
            "configured": True,
            "ai_used": False,
            "message": f"AI 接口返回 {error.code}：{detail}",
            "report": report_markdown,
        }
    except Exception as error:
        return {
            "configured": True,
            "ai_used": False,
            "message": f"AI 请求失败：{error}",
            "report": report_markdown,
        }


class AppRequestHandler(BaseHTTPRequestHandler):
    server_version = "ZoteroWorkbench/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400) -> None:
        self.send_json({"ok": False, "message": message}, status)

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        parsed_path = self.path.split("?", 1)[0]
        if parsed_path == "/":
            self.serve_dashboard()
        elif parsed_path == "/app.js":
            self.serve_static("app.js", "text/javascript; charset=utf-8")
        elif parsed_path == "/app.css":
            self.serve_static("app.css", "text/css; charset=utf-8")
        elif parsed_path == "/api/state":
            self.send_json(
                {
                    "ok": True,
                    "library": load_library(),
                    "categories": load_categories(),
                    "ai": ai_status(),
                }
            )
        elif parsed_path == "/api/categories":
            self.send_json({"ok": True, **load_categories()})
        elif parsed_path == "/api/ai/config":
            self.send_json({"ok": True, **ai_status()})
        elif parsed_path.startswith("/api/note/"):
            self.handle_get_note()
        else:
            self.send_error_json("Not found", 404)

    def do_POST(self) -> None:
        parsed_path = self.path.split("?", 1)[0]
        if parsed_path == "/api/sync":
            result = run_sync()
            self.send_json(result, 200 if result["ok"] else 500)
        elif parsed_path == "/api/ai/report":
            self.handle_ai_report()
        elif parsed_path == "/api/report/export":
            self.handle_report_export()
        else:
            self.send_error_json("Not found", 404)

    def do_PUT(self) -> None:
        parsed_path = self.path.split("?", 1)[0]
        if parsed_path == "/api/categories":
            self.handle_save_categories()
        elif parsed_path == "/api/ai/config":
            self.handle_save_ai_config()
        elif parsed_path.startswith("/api/note/"):
            self.handle_save_note()
        elif parsed_path.startswith("/api/items/"):
            self.handle_save_item_categories()
        else:
            self.send_error_json("Not found", 404)

    def serve_dashboard(self) -> None:
        if not DASHBOARD_FILE.is_file():
            sync_result = run_sync()
            if not sync_result["ok"]:
                self.send_error_json(
                    f"Initial sync failed: {sync_result['stderr']}", 500
                )
                return
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        if "/app.css" not in html:
            html = html.replace(
                "</head>",
                '<link rel="stylesheet" href="/app.css">\n</head>',
            )
        if "/app.js" not in html:
            html = html.replace(
                "</body>",
                '<script src="/app.js"></script>\n</body>',
            )
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, filename: str, content_type: str) -> None:
        path = APP_DIR / filename
        if not path.is_file():
            self.send_error_json("Not found", 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_get_note(self) -> None:
        item_id = int(self.path.rsplit("/", 1)[-1])
        item = find_item(item_id)
        if not item:
            self.send_error_json("Item not found", 404)
            return
        note_path = get_note_path(item_id)
        self.send_json(
            {
                "ok": True,
                "item_id": item_id,
                "note_file": item.get("note_file", ""),
                "manual": get_manual_sections(item_id),
                "exists": bool(note_path and note_path.is_file()),
            }
        )

    def handle_save_note(self) -> None:
        try:
            item_id = int(self.path.rsplit("/", 1)[-1])
            body = self.read_body()
            note_path = get_note_path(item_id)
            if not note_path:
                self.send_error_json("Item not found", 404)
                return
            update_manual_sections(
                note_path,
                {str(key): str(value) for key, value in body.get("manual", {}).items()},
            )
            self.send_json({"ok": True, "message": "笔记已保存。"})
        except Exception as error:
            self.send_error_json(str(error))

    def handle_save_categories(self) -> None:
        try:
            payload = save_categories(self.read_body())
            run_sync()
            self.send_json({"ok": True, "message": "分类已保存并重新同步。", **payload})
        except Exception as error:
            self.send_error_json(str(error))

    def handle_save_item_categories(self) -> None:
        try:
            parts = self.path.split("/")
            item_id = int(parts[-2])
            body = self.read_body()
            payload = update_item_categories(item_id, body.get("category_ids", []))
            run_sync()
            self.send_json({"ok": True, "message": "文献分类已更新。", **payload})
        except Exception as error:
            self.send_error_json(str(error))

    def handle_save_ai_config(self) -> None:
        body = self.read_body()
        config = load_ai_config()
        for key in ("provider", "base_url", "model", "api_key"):
            if key in body:
                config[key] = str(body[key]).strip()
        write_json_file(AI_CONFIG_FILE, config)
        self.send_json({"ok": True, "message": "AI 设置已保存。", **ai_status()})

    def handle_ai_report(self) -> None:
        body = self.read_body()
        item_ids = body.get("item_ids")
        if item_ids is not None:
            item_ids = [int(value) for value in item_ids]
        markdown = build_report_markdown(item_ids, str(body.get("instruction", "")))
        result = call_ai(markdown, str(body.get("instruction", "")))
        self.send_json({"ok": True, **result})

    def handle_report_export(self) -> None:
        body = self.read_body()
        item_ids = body.get("item_ids")
        if item_ids is not None:
            item_ids = [int(value) for value in item_ids]
        markdown = build_report_markdown(item_ids, str(body.get("instruction", "")))
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("report-%Y%m%d-%H%M%S.md")
        report_path = REPORTS_DIR / filename
        report_path.write_text(markdown, encoding="utf-8")
        self.send_json(
            {"ok": True, "message": "报告已保存。", "path": str(report_path)}
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Zotero Research Workbench")
    parser.add_argument("--host", default=HOST, help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to bind (default: {PORT})")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), AppRequestHandler)
    print(f"Zotero 研究工作台已启动：http://{args.host}:{args.port}")
    print("按 Ctrl+C 停止服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.server_close()


if __name__ == "__main__":
    main()
