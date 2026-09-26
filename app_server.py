#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
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
IMPORTS_DIR = OUTPUT_DIR / "imports"
IMPORTS_INDEX = OUTPUT_DIR / "data" / "imports.json"
LOG_DIR = OUTPUT_DIR / "logs"
HOST = "127.0.0.1"
PORT = 5187

CODEX_ENV_KEYS = ("RESEARCH_WORKBENCH_CODEX", "CODEX_BIN")
CODEX_EXECUTABLE_NAMES = ("codex", "codex.exe", "codex.cmd", "codex.bat", "codex.ps1")
DEFAULT_CODEX_TIMEOUT = 600
DEFAULT_REPORT_TEMPLATE = "research"
IMPORT_CONTENT_LIMIT = 20000

REPORT_TEMPLATES: dict[str, dict[str, Any]] = {
    "research": {
        "label": "研究问题—方法—结论",
        "sections": [
            "要解决什么问题",
            "提出的方法 / 技术路线",
            "关键发现与证据",
            "数据、实验或仿真设置",
            "局限、假设与未解决问题",
            "对我研究方向的意义",
            "可复现要点",
            "相关文献关联",
        ],
        "guide": (
            "逐篇说明这篇文献要解决什么问题、提出了什么方法、得到什么结果，"
            "再给出对你研究方向的启示。凡是原文没有交代的内容，统一写“文献未说明”。"
        ),
    },
    "comparison": {
        "label": "多篇对比综述",
        "sections": [
            "主题与检索范围",
            "各文献要解决的问题",
            "方法路线对比",
            "指标、数据与结论对比",
            "共识与分歧",
            "研究空白与机会",
            "建议的下一步工作",
        ],
        "guide": (
            "以对比表格为主线，横向比较各文献的问题、方法、指标与结论，"
            "明确指出哪些结论有原文证据、哪些只是推断。"
        ),
    },
    "quick": {
        "label": "快速摘要",
        "sections": [
            "一句话结论",
            "要解决什么问题",
            "提出的方法",
            "关键结果",
            "局限",
            "可以直接复用的点",
        ],
        "guide": "用尽量短的篇幅给出要点，每条不超过三句话，便于快速浏览。",
    },
    "custom": {
        "label": "自定义（仅按我的要求）",
        "sections": [],
        "guide": "不要套用固定模板，完全按照用户填写的要求组织报告。",
    },
}

_CODEX_PROBE_CACHE: dict[str, Any] = {"executable": "", "time": 0.0, "value": {}}


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


def _existing_file(value: Any) -> str | None:
    text = str(value or "").strip().strip('"')
    if not text:
        return None
    candidate = Path(text).expanduser()
    return str(candidate) if candidate.is_file() else None


def _directory_codex_candidates(directory: Path) -> list[str]:
    """Find codex inside a bin directory, including versioned subdirectories."""
    if not directory.is_dir():
        return []
    found: list[tuple[float, str]] = []
    try:
        entries = list(directory.iterdir())
    except OSError:
        return []
    for entry in entries:
        try:
            if entry.is_file() and entry.name.lower().startswith("codex"):
                found.append((entry.stat().st_mtime, str(entry)))
            elif entry.is_dir():
                for child in entry.glob("codex*"):
                    if child.is_file():
                        found.append((child.stat().st_mtime, str(child)))
        except OSError:
            continue
    found.sort(reverse=True)
    return [path for _, path in found]


def candidate_codex_paths() -> list[str]:
    """Ordered Codex CLI candidates: explicit overrides first, then PATH, then known installs."""
    candidates: list[str] = []
    for key in CODEX_ENV_KEYS:
        resolved = _existing_file(os.environ.get(key, ""))
        if resolved:
            candidates.append(resolved)
    configured = _existing_file(load_ai_config().get("codex_command", ""))
    if configured:
        candidates.append(configured)
    for name in CODEX_EXECUTABLE_NAMES:
        resolved = shutil.which(name)
        if resolved:
            candidates.append(resolved)
    home = Path.home()
    search_dirs = [
        home / "AppData" / "Local" / "OpenAI" / "Codex" / "bin",
        home / "AppData" / "Roaming" / "npm",
        home / "AppData" / "Local" / "Programs" / "codex",
        home / ".bun" / "bin",
        home / ".local" / "bin",
        home / ".npm-global" / "bin",
        Path("/usr/local/bin"),
        Path("/opt/homebrew/bin"),
    ]
    for directory in search_dirs:
        candidates.extend(_directory_codex_candidates(directory))
    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        marker = os.path.normcase(os.path.abspath(candidate))
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(candidate)
    return unique


def find_codex() -> str | None:
    candidates = candidate_codex_paths()
    return candidates[0] if candidates else None


def launch_command(executable: str, args: list[str]) -> list[str]:
    """Wrap launchers so Windows .cmd/.bat/.ps1 wrappers can be executed safely."""
    suffix = Path(executable).suffix.lower()
    if suffix in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC") or "cmd.exe"
        inner = subprocess.list2cmdline([executable, *args])
        return [comspec, "/d", "/s", "/c", f'"{inner}"']
    if suffix == ".ps1":
        shell = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
        return [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            executable,
            *args,
        ]
    return [executable, *args]


def _run_quiet(command: list[str], timeout: int = 25) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return None


def codex_probe(executable: str, force: bool = False, max_age: float = 300.0) -> dict[str, Any]:
    """Inspect a Codex CLI: version, login state and the exec flags it supports."""
    cache = _CODEX_PROBE_CACHE
    if (
        not force
        and cache.get("executable") == executable
        and cache.get("value")
        and time.time() - float(cache.get("time", 0.0)) < max_age
    ):
        return dict(cache["value"])

    info: dict[str, Any] = {
        "path": executable,
        "version": "",
        "logged_in": None,
        "login": "",
        "flags": [],
        "error": "",
    }

    version_result = _run_quiet(launch_command(executable, ["--version"]), timeout=20)
    version_text = ""
    if version_result:
        version_text = (version_result.stdout or version_result.stderr or "").strip()
    match = re.search(r"\d+\.\d+\.\d+[^\s]*", version_text)
    if match:
        info["version"] = match.group(0)
    elif version_text:
        info["version"] = version_text.splitlines()[-1][:80]

    help_result = _run_quiet(launch_command(executable, ["exec", "--help"]), timeout=25)
    help_text = ""
    if help_result:
        help_text = f"{help_result.stdout or ''}\n{help_result.stderr or ''}"
    for flag in (
        "--ephemeral",
        "--skip-git-repo-check",
        "--color",
        "--output-last-message",
        "--sandbox",
        "--json",
        "--model",
        "--cd",
    ):
        if flag in help_text:
            info["flags"].append(flag)

    login_result = _run_quiet(launch_command(executable, ["login", "status"]), timeout=25)
    login_text = ""
    if login_result:
        login_text = f"{login_result.stdout or ''}{login_result.stderr or ''}".strip()
    info["login"] = login_text[-400:]
    lowered = login_text.lower()
    if login_result is not None:
        if "not logged in" in lowered or "no credentials" in lowered or "未登录" in login_text:
            info["logged_in"] = False
        elif "logged in" in lowered or "已登录" in login_text:
            info["logged_in"] = True

    if not info["version"] and not help_text:
        info["error"] = (
            "Codex CLI 无法执行。请在“AI 设置”中填写完整路径，"
            "或确认该命令可以在终端中直接运行。"
        )

    _CODEX_PROBE_CACHE.update(
        {"executable": executable, "time": time.time(), "value": dict(info)}
    )
    return info


def cached_codex_probe(executable: str | None) -> dict[str, Any]:
    if not executable or _CODEX_PROBE_CACHE.get("executable") != executable:
        return {}
    return dict(_CODEX_PROBE_CACHE.get("value") or {})


def ai_status(probe: bool = False) -> dict[str, Any]:
    config = load_ai_config()
    provider = str(config.get("provider", "codex"))
    key = config.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "") or os.environ.get(
        "AI_API_KEY", ""
    )
    codex_path = find_codex()
    if probe and codex_path:
        codex_info = codex_probe(codex_path, force=True)
    else:
        codex_info = cached_codex_probe(codex_path)
    codex_configured = provider == "codex" and codex_path is not None
    api_configured = provider == "api" and bool(
        config.get("base_url") and config.get("model") and key
    )
    return {
        "configured": codex_configured or api_configured,
        "provider": provider,
        "codex_available": codex_configured,
        "codex_candidates": candidate_codex_paths()[:5],
        "codex_path": codex_path or "",
        "codex_version": codex_info.get("version", ""),
        "codex_logged_in": codex_info.get("logged_in"),
        "codex_login": codex_info.get("login", ""),
        "codex_error": codex_info.get("error", ""),
        "codex_command": str(config.get("codex_command", "")),
        "codex_model": str(config.get("codex_model", "")),
        "codex_extra_args": str(config.get("codex_extra_args", "")),
        "codex_timeout": int(
            config.get("codex_timeout", DEFAULT_CODEX_TIMEOUT) or DEFAULT_CODEX_TIMEOUT
        ),
        "opencode_available": shutil.which("opencode") is not None,
        "base_url": config.get("base_url", ""),
        "model": config.get("model", ""),
        "has_key": bool(key),
        "api_key_env": bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("AI_API_KEY")
        ),
        "report_template": str(config.get("report_template", DEFAULT_REPORT_TEMPLATE)),
        "templates": [
            {"id": template_id, "label": template["label"], "sections": template["sections"]}
            for template_id, template in REPORT_TEMPLATES.items()
        ],
        "import_count": len(load_imports().get("imports", [])),
    }


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


def slugify_name(value: str, fallback: str = "import") -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", str(value or "").strip())
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    return text[:48] or fallback


def load_imports() -> dict[str, Any]:
    return read_json_file(IMPORTS_INDEX, {"imports": []})


def save_imports_index(payload: dict[str, Any]) -> None:
    write_json_file(IMPORTS_INDEX, payload)


def normalize_item_ids(values: Any) -> list[int]:
    result: set[int] = set()
    for value in values or []:
        try:
            result.add(int(value))
        except (TypeError, ValueError):
            continue
    return sorted(result)


def normalize_item_keys(values: Any) -> list[str]:
    return sorted({str(value).strip() for value in values or [] if str(value).strip()})


def import_record_path(record: dict[str, Any]) -> Path:
    return IMPORTS_DIR / str(record.get("file", ""))


def read_import_content(record: dict[str, Any]) -> str:
    path = import_record_path(record)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def import_summary(record: dict[str, Any], include_content: bool = False) -> dict[str, Any]:
    summary = {
        "id": record.get("id", ""),
        "name": record.get("name", ""),
        "file": record.get("file", ""),
        "item_ids": record.get("item_ids", []),
        "item_keys": record.get("item_keys", []),
        "source": record.get("source", ""),
        "size": record.get("size", 0),
        "imported_at": record.get("imported_at", ""),
        "preview": record.get("preview", ""),
    }
    if include_content:
        summary["content"] = read_import_content(record)
    return summary


def imports_summary(include_content: bool = False) -> list[dict[str, Any]]:
    records = load_imports().get("imports", [])
    return [
        import_summary(record, include_content)
        for record in records
        if isinstance(record, dict) and record.get("id")
    ]


def find_import(import_id: str) -> dict[str, Any] | None:
    for record in load_imports().get("imports", []):
        if isinstance(record, dict) and str(record.get("id")) == str(import_id):
            return record
    return None


def save_import_entries(
    entries: list[dict[str, Any]],
    item_ids: Any,
    item_keys: Any,
    source: str = "",
) -> list[dict[str, Any]]:
    if not entries:
        raise ValueError("没有可导入的内容。")
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = load_imports()
    records = [record for record in payload.get("imports", []) if isinstance(record, dict)]
    ids = normalize_item_ids(item_ids)
    keys = normalize_item_keys(item_keys)
    saved: list[dict[str, Any]] = []
    for entry in entries:
        name = str(entry.get("name") or "").strip() or "未命名资料"
        content = str(entry.get("content") or "")
        if not content.strip():
            continue
        if len(content) > 2_000_000:
            raise ValueError(f"{name} 超过 2 MB，请拆分后再导入。")
        imported_at = datetime.now()
        suffix = datetime.now().strftime("%H%M%S%f")[:10]
        import_id = f"{imported_at.strftime('%Y%m%d')}-{slugify_name(name)}-{suffix}"
        filename = f"{import_id}.md"
        (IMPORTS_DIR / filename).write_text(content, encoding="utf-8")
        record = {
            "id": import_id,
            "name": name,
            "file": filename,
            "item_ids": ids,
            "item_keys": keys,
            "source": source,
            "size": len(content.encode("utf-8")),
            "imported_at": imported_at.strftime("%Y-%m-%d %H:%M"),
            "preview": re.sub(r"\s+", " ", content.strip())[:240],
        }
        records.append(record)
        saved.append(record)
    if not saved:
        raise ValueError("导入内容为空。")
    payload["imports"] = records
    save_imports_index(payload)
    return saved


def update_import_links(
    import_id: str, item_ids: Any, item_keys: Any
) -> dict[str, Any]:
    payload = load_imports()
    ids = normalize_item_ids(item_ids)
    keys = normalize_item_keys(item_keys)
    for record in payload.get("imports", []):
        if isinstance(record, dict) and str(record.get("id")) == str(import_id):
            record["item_ids"] = ids
            record["item_keys"] = keys
            save_imports_index(payload)
            return import_summary(record)
    raise ValueError("未找到该导入资料。")


def delete_import(import_id: str) -> dict[str, Any]:
    payload = load_imports()
    records = [
        record
        for record in payload.get("imports", [])
        if isinstance(record, dict) and str(record.get("id")) != str(import_id)
    ]
    if len(records) == len(payload.get("imports", [])):
        raise ValueError("未找到该导入资料。")
    payload["imports"] = records
    save_imports_index(payload)
    path = IMPORTS_DIR / f"{import_id}.md"
    if path.is_file():
        path.unlink()
    return {"id": import_id}


def imports_for_item(item_id: Any, item_key: Any) -> list[dict[str, Any]]:
    try:
        target_id = int(item_id)
    except (TypeError, ValueError):
        target_id = None
    target_key = str(item_key or "").strip()
    matched: list[dict[str, Any]] = []
    for record in load_imports().get("imports", []):
        if not isinstance(record, dict):
            continue
        if target_id is not None and target_id in record.get("item_ids", []):
            matched.append(import_summary(record))
        elif target_key and target_key in record.get("item_keys", []):
            matched.append(import_summary(record))
    return matched


README_FILENAMES = ("README.md", "readme.md", "README.markdown", "README.rst", "README.txt")
README_BRANCHES = ("HEAD", "main", "master")
README_MAX_BYTES = 1_500_000
HTTP_HEADERS = {
    "User-Agent": "Zotero-Research-Workbench/1.0 (+https://github.com/fangfren/Zotero-ai-organization)",
    "Accept": "text/plain, text/markdown, text/x-markdown, */*",
}


def github_readme_urls(url: str) -> list[str]:
    """Expand a GitHub link into candidate raw README URLs."""
    match = re.match(
        r"^https?://(?:www\.)?github\.com/([^/]+)/([^/?#]+)(.*)$",
        url.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return []
    owner, repo = match.group(1), re.sub(r"\.git$", "", match.group(2))
    rest = match.group(3) or ""
    blob = re.match(r"^/blob/([^/]+)/(.+)$", rest)
    if blob:
        return [
            f"https://raw.githubusercontent.com/{owner}/{repo}/{blob.group(1)}/{blob.group(2)}"
        ]
    candidates: list[str] = []
    for branch in README_BRANCHES:
        for filename in README_FILENAMES:
            candidates.append(
                f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
            )
    return candidates


def fetch_text_url(url: str, timeout: int = 20) -> tuple[str, str]:
    """Return (text, resolved_url). Raises ValueError with a readable reason."""
    request = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(README_MAX_BYTES + 1)
        resolved = response.geturl()
        content_type = (response.headers.get("Content-Type") or "").lower()
        charset = response.headers.get_content_charset() or "utf-8"
    if len(raw) > README_MAX_BYTES:
        raise ValueError("文件超过 1.5 MB，请下载后手动导入。")
    if "text/html" in content_type:
        raise ValueError(
            "这个链接返回的是网页而不是 README 文本。请使用 GitHub 仓库地址或 raw 文件地址。"
        )
    text = raw.decode(charset, errors="replace")
    if not text.strip():
        raise ValueError("抓取到的内容是空的。")
    return text, resolved


def normalize_readme_url(url: str) -> str:
    target = url.strip()
    if not target:
        raise ValueError("请填写仓库地址或 README 链接。")
    if re.match(r"^[\w.-]+/[\w.-]+$", target):
        target = "https://github.com/" + target
    if not re.match(r"^https?://", target, flags=re.IGNORECASE):
        target = "https://" + target
    return target


def fetch_readme(url: str) -> tuple[str, str]:
    """Fetch README text from a GitHub repo URL, a raw URL or a plain text URL."""
    target = normalize_readme_url(url)

    errors: list[str] = []
    for candidate in github_readme_urls(target) or [target]:
        try:
            return fetch_text_url(candidate)
        except urllib.error.HTTPError as error:
            errors.append(f"{candidate} -> HTTP {error.code}")
        except urllib.error.URLError as error:
            errors.append(f"{candidate} -> {error.reason}")
        except ValueError as error:
            errors.append(f"{candidate} -> {error}")
    raise ValueError("抓取失败：" + "；".join(errors[-3:]))


def import_readme(
    url: str,
    item_ids: Any = None,
    item_keys: Any = None,
    name: str = "",
) -> dict[str, Any]:
    text, resolved = fetch_readme(url)
    target = normalize_readme_url(url)
    label = name.strip()
    if not label:
        match = re.match(
            r"^https?://(?:www\.)?github\.com/([^/]+)/([^/?#]+)", target, re.I
        )
        if match:
            repo_name = re.sub(r"\.git$", "", match.group(2))
            label = f"{match.group(1)}/{repo_name} README"
        else:
            label = resolved
    display_name = label if "readme" in label.lower() else f"{label}（README）"
    saved = save_import_entries(
        [{"name": display_name, "content": text}],
        item_ids or [],
        item_keys or [],
        source="readme",
    )
    return {"import": import_summary(saved[0]), "url": resolved}


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
    template_key: str = DEFAULT_REPORT_TEMPLATE,
) -> str:
    library = load_library()
    items = library.get("items", [])
    selected = [
        item for item in items if not item_ids or item.get("zotero_item_id") in item_ids
    ]
    template = REPORT_TEMPLATES.get(template_key) or REPORT_TEMPLATES[DEFAULT_REPORT_TEMPLATE]
    lines = [
        "# DFB 文献研究报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"报告模板：{template['label']}",
        "",
    ]
    if instruction.strip():
        lines.extend(["## 报告要求", "", instruction.strip(), ""])

    if template["sections"]:
        lines.extend(["## 报告模板结构", ""])
        lines.extend(
            f"{index}. {section}" for index, section in enumerate(template["sections"], start=1)
        )
        lines.extend(
            [
                "",
                "> 每节都要写清楚：问题是什么、方法是什么、证据来自哪篇文献；"
                "原文未交代的内容统一写“文献未说明”。",
                "",
            ]
        )

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
        linked = imports_for_item(item.get("zotero_item_id"), item.get("zotero_key"))
        if linked:
            lines.extend(["### 关联导入资料", ""])
            for record in linked:
                content = read_import_content(record).strip()
                lines.append(f"#### {record.get('name') or record.get('id')}")
                lines.append("")
                if len(content) > IMPORT_CONTENT_LIMIT:
                    lines.append(
                        f"{content[:IMPORT_CONTENT_LIMIT]}\n\n> （内容过长，已截断，完整文件见 "
                        f"output/imports/{record.get('file')}）"
                    )
                else:
                    lines.append(content or "（文件为空）")
                lines.append("")

    if not item_ids:
        unlinked = [
            record
            for record in imports_summary()
            if not record.get("item_ids") and not record.get("item_keys")
        ]
        if unlinked:
            lines.extend(["## 未关联文献的导入资料", ""])
            for record in unlinked:
                content = read_import_content(record).strip()
                lines.append(f"### {record.get('name') or record.get('id')}")
                lines.append("")
                lines.append(
                    content[:IMPORT_CONTENT_LIMIT] or "（文件为空）"
                )
                lines.append("")
    return "\n".join(lines)


def prompt_guide(template_key: str) -> str:
    template = REPORT_TEMPLATES.get(template_key) or REPORT_TEMPLATES[DEFAULT_REPORT_TEMPLATE]
    sections = "、".join(template["sections"]) or "按用户要求组织"
    return (
        f"{template['guide']}\n"
        f"报告需要覆盖的章节：{sections}。\n"
        "输出 Markdown。每篇文献都要能看出“要解决什么问题”和“提出了什么方法”；"
        "凡原始材料没有提供的信息，写“文献未说明”，不要补充想象的数据。"
    )


def call_ai(
    report_markdown: str,
    instruction: str,
    template_key: str = DEFAULT_REPORT_TEMPLATE,
) -> dict[str, Any]:
    config = load_ai_config()
    provider = str(config.get("provider", "codex"))
    if provider == "codex":
        return call_codex(report_markdown, instruction, template_key)
    return call_api(report_markdown, instruction, template_key)


def write_codex_log(kind: str, executable: str, command: list[str], payload: str) -> str:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"codex-{kind}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    header = [
        f"time: {datetime.now().isoformat(timespec='seconds')}",
        f"executable: {executable}",
        f"command: {subprocess.list2cmdline(command)}",
        "",
    ]
    try:
        path.write_text("\n".join(header) + payload, encoding="utf-8")
        return str(path)
    except OSError:
        return ""


def codex_error_message(error_text: str, executable: str, log_path: str) -> str:
    lowered = error_text.lower()
    hint = ""
    if "not logged in" in lowered or "401" in lowered or "unauthorized" in lowered:
        hint = "Codex 未登录：请在终端执行 `codex login` 完成订阅登录后再试。"
    elif "readonly database" in lowered or "read-only" in lowered:
        hint = (
            "Codex 无法写入自己的状态目录（通常是权限或杀毒软件拦截）："
            "请确认当前用户对 `%USERPROFILE%\\.codex`（macOS/Linux 为 `~/.codex`）有写权限。"
        )
    elif "database is locked" in lowered:
        hint = "Codex 状态数据库被占用：请关闭其它正在运行的 Codex 会话后重试。"
    elif "winerror 193" in lowered or "not a valid win32" in lowered:
        hint = "启动器解析失败：请在“AI 设置”里把 Codex 命令改成 `codex.cmd` 的完整路径。"
    elif "winerror 5" in lowered or "access is denied" in lowered or "拒绝访问" in error_text:
        hint = "系统拒绝执行 Codex：请检查杀毒软件拦截或改用完整路径。"
    elif "timed out" in lowered or "timeout" in lowered:
        hint = "调用超时：可以在“AI 设置”里提高超时时间，或缩小报告范围。"
    elif "connection" in lowered or "network" in lowered or "tls" in lowered:
        hint = "网络连接失败：Codex 需要联网访问模型服务，请检查代理设置。"
    detail = error_text.strip()[-1500:] or "（无输出）"
    parts = [f"Codex 返回错误（{Path(executable).name}）：", detail]
    if hint:
        parts.append(hint)
    if log_path:
        parts.append(f"完整日志：{log_path}")
    return "\n".join(parts)


def build_codex_command(
    executable: str,
    output_path: Path,
    info: dict[str, Any],
    config: dict[str, Any],
) -> list[str]:
    flags = set(info.get("flags") or [])
    args = ["exec"]
    if "--skip-git-repo-check" in flags or not flags:
        args.append("--skip-git-repo-check")
    if "--ephemeral" in flags:
        args.append("--ephemeral")
    if "--color" in flags:
        args.extend(["--color", "never"])
    if "--sandbox" in flags:
        args.extend(["-s", "read-only"])
    if "--output-last-message" in flags:
        args.extend(["-o", str(output_path)])
    model = str(config.get("codex_model", "") or "").strip()
    if model and ("--model" in flags or not flags):
        args.extend(["-m", model])
    extra_args = str(config.get("codex_extra_args", "") or "").strip()
    if extra_args:
        try:
            args.extend(shlex.split(extra_args, posix=False))
        except ValueError:
            args.extend(extra_args.split())
    args.append("-")
    return launch_command(executable, args)


def call_codex(
    report_markdown: str,
    instruction: str,
    template_key: str = DEFAULT_REPORT_TEMPLATE,
) -> dict[str, Any]:
    config = load_ai_config()
    executable = find_codex()
    if not executable:
        hints = []
        if shutil.which("opencode"):
            hints.append(
                "检测到 opencode，但本工作台通过 Codex CLI 使用订阅登录；"
                "若你的 codex 命令不在 PATH 中，请把完整路径填入“AI 设置 → Codex 命令”。"
            )
        return {
            "configured": False,
            "ai_used": False,
            "message": "未找到 Codex CLI。请在“AI 设置”里填写 codex 可执行文件的完整路径，"
            "或先安装并登录 Codex CLI（无需 API 密钥）。"
            + ("\n" + "\n".join(hints) if hints else ""),
            "report": report_markdown,
        }

    info = codex_probe(executable)
    if info.get("logged_in") is False:
        return {
            "configured": True,
            "ai_used": False,
            "message": (
                f"Codex CLI（{executable}）尚未登录。请在终端执行 `codex login` "
                "完成订阅登录，然后回到“AI 设置”点击“测试 Codex”。"
            ),
            "codex_path": executable,
            "codex_login": info.get("login", ""),
            "report": report_markdown,
        }

    system_prompt = (
        "你是科研文献整理助手，负责把 Zotero 元数据、摘要、批注、用户笔记和关联资料"
        "整理成逻辑清晰、可复述、区分事实与推断的中文研究报告。"
        "不得编造文献中没有的数据；信息缺失时明确写“文献未说明”。"
    )
    user_prompt = (
        f"{prompt_guide(template_key)}\n\n"
        f"用户补充要求：{instruction or '无'}\n\n"
        f"原始材料（含模板骨架）：\n{report_markdown}"
    )
    prompt = f"{system_prompt}\n\n{user_prompt}"

    output_dir = OUTPUT_DIR / "codex-tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S%f')}.md"
    command = build_codex_command(executable, output_path, info, config)
    try:
        timeout = int(config.get("codex_timeout", DEFAULT_CODEX_TIMEOUT) or DEFAULT_CODEX_TIMEOUT)
    except (TypeError, ValueError):
        timeout = DEFAULT_CODEX_TIMEOUT
    timeout = max(60, min(timeout, 3600))

    started = time.time()
    try:
        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        payload = (
            f"exit_code: {result.returncode}\n\n--- stdout ---\n{result.stdout or ''}\n"
            f"\n--- stderr ---\n{result.stderr or ''}\n"
        )
        if result.returncode != 0:
            log_path = write_codex_log("error", executable, command, payload)
            return {
                "configured": True,
                "ai_used": False,
                "message": codex_error_message(
                    (result.stderr or "") or (result.stdout or ""), executable, log_path
                ),
                "codex_path": executable,
                "duration": round(time.time() - started, 1),
                "report": report_markdown,
            }
        content = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
        content = content.strip()
        if not content:
            content = (result.stdout or "").strip()
        if not content:
            log_path = write_codex_log("empty", executable, command, payload)
            return {
                "configured": True,
                "ai_used": False,
                "message": f"Codex 没有返回内容，日志：{log_path}" if log_path else "Codex 没有返回内容。",
                "codex_path": executable,
                "report": report_markdown,
            }
        write_codex_log("run", executable, command, payload)
        return {
            "configured": True,
            "ai_used": True,
            "message": f"Codex 报告生成完成（{round(time.time() - started, 1)} 秒）。",
            "codex_path": executable,
            "codex_version": info.get("version", ""),
            "duration": round(time.time() - started, 1),
            "report": content,
        }
    except subprocess.TimeoutExpired:
        return {
            "configured": True,
            "ai_used": False,
            "message": (
                f"Codex 生成超时（超过 {timeout} 秒）。可以在“AI 设置”里提高超时时间，"
                "或把报告范围缩小到单篇文献。"
            ),
            "codex_path": executable,
            "report": report_markdown,
        }
    except Exception as error:
        log_path = write_codex_log("exception", executable, command, f"{type(error).__name__}: {error}")
        return {
            "configured": True,
            "ai_used": False,
            "message": codex_error_message(str(error), executable, log_path),
            "codex_path": executable,
            "report": report_markdown,
        }
    finally:
        if output_path.exists():
            output_path.unlink()


def run_codex_self_check(model_override: str = "") -> dict[str, Any]:
    """Run a tiny Codex prompt so the user can verify subscription login end to end."""
    config = load_ai_config()
    if model_override:
        config["codex_model"] = model_override
    executable = find_codex()
    if not executable:
        return {
            "ok": False,
            "message": "未找到 Codex CLI。请安装 Codex 并登录，或在“AI 设置”中填写完整路径。",
            "path": "",
        }
    info = codex_probe(executable, force=True)
    result = call_codex(
        "# 自检\n\n这是一次调用自检，没有真实文献数据。",
        "只回复一句“连接正常”，不要输出其它内容。",
        "quick",
    )
    return {
        "ok": bool(result.get("ai_used")),
        "message": result.get("message", ""),
        "path": executable,
        "version": info.get("version", ""),
        "logged_in": info.get("logged_in"),
        "login": info.get("login", ""),
        "preview": str(result.get("report", ""))[:400],
        "duration": result.get("duration"),
    }


def call_api(
    report_markdown: str,
    instruction: str,
    template_key: str = DEFAULT_REPORT_TEMPLATE,
) -> dict[str, Any]:
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
        f"{prompt_guide(template_key)}\n\n"
        f"用户补充要求：{instruction or '无'}\n\n"
        f"原始材料（含模板骨架）：\n{report_markdown}"
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

    def query_value(self, name: str, default: str = "") -> str:
        if "?" not in self.path:
            return default
        query = self.path.split("?", 1)[1]
        for chunk in query.split("&"):
            key, _, value = chunk.partition("=")
            if key == name:
                return urllib.request.unquote(value)
        return default

    def do_GET(self) -> None:
        try:
            self.route_get()
        except Exception as error:  # keep every failure JSON so the UI can show it
            self.send_error_json(f"{type(error).__name__}: {error}", 500)

    def route_get(self) -> None:
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
                    "imports": imports_summary(),
                    "ai": ai_status(),
                }
            )
        elif parsed_path == "/api/categories":
            self.send_json({"ok": True, **load_categories()})
        elif parsed_path == "/api/ai/config":
            self.send_json({"ok": True, **ai_status(probe=self.query_value("probe") == "1")})
        elif parsed_path == "/api/imports":
            item_id = self.query_value("item_id")
            if item_id:
                self.send_json({"ok": True, "imports": imports_for_item(item_id, self.query_value("item_key"))})
                return
            include_content = self.query_value("content") == "1"
            self.send_json({"ok": True, "imports": imports_summary(include_content)})
        elif parsed_path.startswith("/api/imports/"):
            import_id = urllib.request.unquote(parsed_path.rsplit("/", 1)[-1])
            record = find_import(import_id)
            if not record:
                self.send_error_json("未找到该导入资料。", 404)
                return
            self.send_json({"ok": True, "import": import_summary(record, include_content=True)})
        elif parsed_path.startswith("/api/note/"):
            self.handle_get_note()
        else:
            self.send_error_json("Not found", 404)

    def do_POST(self) -> None:
        try:
            self.route_post()
        except Exception as error:
            self.send_error_json(f"{type(error).__name__}: {error}", 500)

    def route_post(self) -> None:
        parsed_path = self.path.split("?", 1)[0]
        if parsed_path == "/api/sync":
            result = run_sync()
            self.send_json(result, 200 if result["ok"] else 500)
        elif parsed_path == "/api/imports":
            self.handle_save_imports()
        elif parsed_path == "/api/imports/readme":
            self.handle_import_readme()
        elif parsed_path == "/api/ai/report":
            self.handle_ai_report()
        elif parsed_path == "/api/ai/test":
            self.handle_ai_test()
        elif parsed_path == "/api/report/export":
            self.handle_report_export()
        else:
            self.send_error_json("Not found", 404)

    def do_PUT(self) -> None:
        try:
            self.route_put()
        except Exception as error:
            self.send_error_json(f"{type(error).__name__}: {error}", 500)

    def route_put(self) -> None:
        parsed_path = self.path.split("?", 1)[0]
        if parsed_path == "/api/categories":
            self.handle_save_categories()
        elif parsed_path == "/api/ai/config":
            self.handle_save_ai_config()
        elif parsed_path.startswith("/api/imports/"):
            self.handle_update_import()
        elif parsed_path.startswith("/api/note/"):
            self.handle_save_note()
        elif parsed_path.startswith("/api/items/"):
            self.handle_save_item_categories()
        else:
            self.send_error_json("Not found", 404)

    def do_DELETE(self) -> None:
        try:
            parsed_path = self.path.split("?", 1)[0]
            if parsed_path.startswith("/api/imports/"):
                import_id = urllib.request.unquote(parsed_path.rsplit("/", 1)[-1])
                payload = delete_import(import_id)
                self.send_json({"ok": True, "message": "导入资料已删除。", **payload})
            else:
                self.send_error_json("Not found", 404)
        except Exception as error:
            self.send_error_json(str(error))

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
        for key in (
            "provider",
            "base_url",
            "model",
            "api_key",
            "codex_command",
            "codex_model",
            "codex_extra_args",
            "report_template",
        ):
            if key in body:
                config[key] = str(body[key]).strip()
        if "codex_timeout" in body:
            try:
                timeout = int(body["codex_timeout"])
            except (TypeError, ValueError):
                timeout = DEFAULT_CODEX_TIMEOUT
            config["codex_timeout"] = max(60, min(timeout, 3600))
        write_json_file(AI_CONFIG_FILE, config)
        _CODEX_PROBE_CACHE.update({"executable": "", "time": 0.0, "value": {}})
        self.send_json({"ok": True, "message": "AI 设置已保存。", **ai_status(probe=True)})

    def handle_ai_test(self) -> None:
        body = self.read_body()
        model = str(body.get("model", "") or "").strip()
        result = run_codex_self_check(model)
        self.send_json({"ok": True, **result})

    def handle_save_imports(self) -> None:
        try:
            body = self.read_body()
            entries = body.get("entries")
            if not isinstance(entries, list):
                entries = [{"name": body.get("name", ""), "content": body.get("content", "")}]
            cleaned = [
                {"name": str(entry.get("name", "")), "content": str(entry.get("content", ""))}
                for entry in entries
                if isinstance(entry, dict)
            ]
            saved = save_import_entries(
                cleaned,
                body.get("item_ids", []),
                body.get("item_keys", []),
                source=str(body.get("source", "upload")),
            )
            self.send_json(
                {
                    "ok": True,
                    "message": f"已导入 {len(saved)} 份资料。",
                    "imports": [import_summary(record) for record in saved],
                }
            )
        except Exception as error:
            self.send_error_json(str(error))

    def handle_update_import(self) -> None:
        try:
            import_id = urllib.request.unquote(self.path.split("?", 1)[0].rsplit("/", 1)[-1])
            body = self.read_body()
            record = update_import_links(
                import_id, body.get("item_ids", []), body.get("item_keys", [])
            )
            self.send_json({"ok": True, "message": "关联文献已更新。", "import": record})
        except Exception as error:
            self.send_error_json(str(error))

    def handle_import_readme(self) -> None:
        try:
            body = self.read_body()
            result = import_readme(
                str(body.get("url", "")),
                body.get("item_ids", []),
                body.get("item_keys", []),
                str(body.get("name", "")),
            )
            self.send_json(
                {
                    "ok": True,
                    "message": f"已抓取并导入：{result['import']['name']}",
                    **result,
                }
            )
        except ValueError as error:
            self.send_error_json(str(error))
        except Exception as error:
            self.send_error_json(f"导入 README 失败：{type(error).__name__}: {error}")

    def handle_ai_report(self) -> None:
        body = self.read_body()
        item_ids = body.get("item_ids")
        if item_ids is not None:
            item_ids = [int(value) for value in item_ids]
        template_key = str(body.get("template", "") or "").strip()
        if template_key not in REPORT_TEMPLATES:
            template_key = str(load_ai_config().get("report_template", DEFAULT_REPORT_TEMPLATE))
        if template_key not in REPORT_TEMPLATES:
            template_key = DEFAULT_REPORT_TEMPLATE
        markdown = build_report_markdown(
            item_ids, str(body.get("instruction", "")), template_key
        )
        result = call_ai(markdown, str(body.get("instruction", "")), template_key)
        self.send_json({"ok": True, "template": template_key, **result})

    def handle_report_export(self) -> None:
        body = self.read_body()
        item_ids = body.get("item_ids")
        if item_ids is not None:
            item_ids = [int(value) for value in item_ids]
        report_text = str(body.get("report", "") or "").strip()
        if report_text:
            markdown = report_text
        else:
            template_key = str(body.get("template", "") or "").strip()
            if template_key not in REPORT_TEMPLATES:
                template_key = DEFAULT_REPORT_TEMPLATE
            markdown = build_report_markdown(
                item_ids, str(body.get("instruction", "")), template_key
            )
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("report-%Y%m%d-%H%M%S.md")
        report_path = REPORTS_DIR / filename
        report_path.write_text(markdown, encoding="utf-8")
        self.send_json(
            {
                "ok": True,
                "message": "报告已保存"
                + ("（AI 生成内容）" if report_text else "（模板素材）")
                + "：",
                "path": str(report_path),
            }
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
