# Zotero Research Workbench

[English](#english) | [简体中文](#简体中文)

Local-first dashboard for reading, categorizing, annotating, and reporting on a
Zotero library. It reads the local Zotero SQLite database, exports structured
notes and metadata, and serves a dependency-free web dashboard.

本地优先的文献工作台：阅读、分类、批注并生成 Zotero 文献库报告。直接读取本地
Zotero SQLite 数据库，导出结构化的笔记与元数据，并提供一个不依赖第三方组件的
网页仪表盘。

---

## English

### Features

- Reads Zotero collection membership, tags, bibliographic metadata, PDF
  annotations, notes, and standalone PDF attachments from the local Zotero data
  directory.
- Groups items by Zotero collections when collections exist, with keyword-based
  fallback categories for ungrouped items.
- Exports one Markdown note per item and preserves user-edited sections across
  resyncs.
- Serves a local dashboard with category navigation, search, filters, literature
  cards, and item-level annotation details.
- Generates structured reports with either the local Codex CLI or an
  OpenAI-compatible HTTP API.
- Writes reports and JSON state under a local output directory.
- Does not write to the Zotero database.

### Requirements

- Python 3.10 or newer
- Zotero desktop with a local data directory
- Optional: Codex CLI for local Codex report generation
- Optional: an OpenAI-compatible API endpoint and key for API report generation

No third-party Python packages are required. The application uses the Python
standard library.

### Installation

```bash
git clone https://github.com/fangfren/Zotero-ai-organization.git
cd Zotero-ai-organization
```

If Python 3.10 or newer is installed, the application is ready to run.

Creating a virtual environment is optional:

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### Quick Start

Windows users can double-click `open-desktop.cmd`; it finds a local Python
installation, starts the server, waits until port `5187` is ready, and opens
the dashboard. `run.cmd` only refreshes the exported data. The scripts first
look for `.venv`, then `python`, then the Windows `py -3` launcher.
Set `RESEARCH_WORKBENCH_PYTHON` to a specific interpreter path if Python is
installed in a non-standard location.

macOS and Linux users can run:

```bash
bash run.sh
bash start-app.sh
```

Manual startup also works:

1. Build the dashboard state from Zotero:

   ```bash
   python sync_zotero.py
   ```

2. Start the local server:

   ```bash
   python app_server.py
   ```

3. Open:

   ```text
   http://127.0.0.1:5187
   ```

The server stays on `127.0.0.1` by default and does not require internet access.

### Zotero Data Directory

The default Zotero path is:

```text
Windows: %USERPROFILE%\Zotero
macOS / Linux: ~/Zotero
```

The application reads these files:

```text
zotero.sqlite
zotero.sqlite-wal
zotero.sqlite-shm
```

It copies them into `.cache/` and queries the snapshot. Zotero can remain open
while the application runs.

Override the data directory for a single sync command:

```bash
python sync_zotero.py --zotero-dir "D:\path\to\Zotero"
```

For the dashboard's **Sync data** button, set the same directory in the
environment before starting the server:

```powershell
# Windows PowerShell
$env:ZOTERO_DATA_DIR = "D:\path\to\Zotero"
.\start-app.cmd
```

```bash
# macOS / Linux
export ZOTERO_DATA_DIR="/path/to/Zotero"
bash start-app.sh
```

`ZOTERO_DATA_DIR` is inherited by `app_server.py` and by every resync it starts.

### Synchronization

Run `sync_zotero.py` after changing Zotero data:

```bash
python sync_zotero.py
```

The dashboard reads the generated `output/data/library.json`. The resync process
does not modify Zotero.

### Configuration

Copy example configuration files to local files:

Windows PowerShell:

```powershell
Copy-Item config\categories.example.json config\categories.json
Copy-Item config\ai.example.json config\ai.json
```

macOS / Linux:

```bash
cp config/categories.example.json config/categories.json
cp config/ai.example.json config/ai.json
```

#### Categories

`config/categories.json` defines fallback categories:

```json
{
  "default_category_id": "unsorted",
  "categories": [
    {
      "id": "overview",
      "name": "Overview",
      "description": "Optional description",
      "color": "#3f7f76",
      "keywords": ["review", "overview"],
      "item_ids": [],
      "item_keys": []
    }
  ]
}
```

Fields:

- `id`: stable unique identifier
- `name`: display name
- `description`: optional category description
- `color`: hex color used by the dashboard
- `keywords`: substrings or lowercase tokens used for automatic assignment
- `item_ids`: explicit Zotero item IDs assigned to this category
- `item_keys`: explicit Zotero item keys assigned to this category

When Zotero collections exist, collection membership takes precedence over
keyword matching.

#### AI Reports

`config/ai.json` selects the report provider:

```json
{
  "provider": "codex",
  "base_url": "https://api.openai.com/v1/chat/completions",
  "model": "",
  "api_key": ""
}
```

`provider` accepts:

- `codex`: runs the local Codex CLI
- `api`: calls an OpenAI-compatible chat completions endpoint

For API mode, set `base_url`, `model`, and `api_key`. The API key can also be
provided through `OPENAI_API_KEY` or `AI_API_KEY`.

### Command Line Options

`sync_zotero.py`:

```text
--zotero-dir PATH       Zotero data directory
--output PATH           Output directory
--library-id ID         Zotero library ID (default: 1)
--categories PATH       Category configuration JSON
```

`app_server.py`:

```text
--port PORT             Server port (default: 5187)
```

### REST API

The local server exposes:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/state` | Library, categories, and AI status |
| GET | `/api/categories` | Current categories |
| PUT | `/api/categories` | Save local category rules and resync |
| GET | `/api/note/{id}` | Manual note sections for one item |
| PUT | `/api/note/{id}` | Save manual note sections |
| PUT | `/api/items/{id}/categories` | Assign local categories and resync |
| POST | `/api/sync` | Resync from Zotero |
| GET | `/api/ai/config` | AI provider status |
| PUT | `/api/ai/config` | Save AI settings |
| POST | `/api/ai/report` | Generate a report |
| POST | `/api/report/export` | Export a report to the output directory |

### Output Layout

```text
output/
├── README.md
├── literature-map.md
├── questions.md
├── glossary.md
├── notes/
│   └── *.md
├── dashboard/
│   └── index.html
├── data/
│   ├── library.json
│   └── categories.runtime.json
└── reports/
```

`output/`, `.cache/`, and local configuration files are excluded from version
control to prevent private Zotero annotations and API keys from being published.

### Privacy

- Zotero data is read from a local snapshot.
- Generated notes, annotations, and reports stay in the local output directory.
- API or Codex report generation sends only the material referenced by the
  selected report scope and the instruction supplied in the request.
- The application does not upload Zotero data.

### Limitations

- Classification follows Zotero collections but does not write back to Zotero.
- Moving an item between categories requires changing its Zotero collection and
  resyncing.
- The application is not a replacement for Zotero's own note editing or backup
  tools.
- Codex CLI requires access to the user's Codex configuration directory. When
  that access is unavailable, API mode can be used instead.

### Troubleshooting

- `Python 3.10 or newer was not found`: install Python from
  <https://www.python.org/downloads/> and enable **Add Python to PATH** during
  installation. Reopen the terminal after installing.
- The server starts but the dashboard reports a Zotero database error: confirm
  that `%USERPROFILE%\Zotero\zotero.sqlite` or `~/Zotero/zotero.sqlite`
  exists, or set `ZOTERO_DATA_DIR`.
- Port `5187` is already occupied by another application: run
  `python app_server.py --port 5190`, then open
  `http://127.0.0.1:5190`; on macOS/Linux you can also use
  `PORT=5190 bash start-app.sh`.

### License

Released under the [MIT License](LICENSE).

---

## 简体中文

### 简介

本项目读取本地 Zotero SQLite 数据库，导出结构化的笔记与元数据，并提供一个不依赖
第三方组件的本地网页仪表盘。全部数据都在你自己的电脑上处理。

### 功能特性

- 读取本地 Zotero 数据目录中的集合归属、标签、书目元数据、PDF 批注、笔记和
  独立 PDF 附件。
- 存在 Zotero 集合时按集合分组；未归入集合的条目使用基于关键词的兜底分类。
- 每条文献导出一个 Markdown 笔记，重新同步时会保留你手写的段落。
- 本地仪表盘提供分类导航、搜索、筛选、文献卡片和单条文献的批注详情。
- 支持用本地 Codex CLI 或兼容 OpenAI 的 HTTP API 生成结构化报告。
- 报告与 JSON 状态写入本地输出目录。
- 不会向 Zotero 数据库写入任何内容。

### 运行要求

- Python 3.10 或更高版本
- 已安装 Zotero 桌面端，并存在本地数据目录
- 可选：本地 Codex CLI，用于生成 Codex 报告
- 可选：兼容 OpenAI 的 API 地址与密钥，用于 API 报告

不需要任何第三方 Python 包，程序只使用标准库。

### 安装

```bash
git clone https://github.com/fangfren/Zotero-ai-organization.git
cd Zotero-ai-organization
```

只要已安装 Python 3.10 或更高版本，就可以直接运行。

创建虚拟环境是可选的：

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 快速开始

Windows 用户可直接双击 `open-desktop.cmd`：脚本会自动查找本机 Python、启动服务、
等待 `5187` 端口就绪，然后打开仪表盘。`run.cmd` 只用于刷新导出数据。脚本按
`.venv`、`python`、Windows `py -3` 的顺序查找解释器；如果 Python 装在非标准
位置，可用 `RESEARCH_WORKBENCH_PYTHON` 指定完整路径。

macOS 和 Linux 用户执行：

```bash
bash run.sh
bash start-app.sh
```

也可以手动启动：

1. 先根据 Zotero 生成仪表盘数据：

   ```bash
   python sync_zotero.py
   ```

2. 启动本地服务：

   ```bash
   python app_server.py
   ```

3. 打开浏览器访问：

   ```text
   http://127.0.0.1:5187
   ```

服务默认只监听 `127.0.0.1`，不需要联网。

### Zotero 数据目录

默认的 Zotero 路径为：

```text
Windows: %USERPROFILE%\Zotero
macOS / Linux: ~/Zotero
```

程序会读取以下文件：

```text
zotero.sqlite
zotero.sqlite-wal
zotero.sqlite-shm
```

它们会被复制到 `.cache/` 后查询快照，因此运行期间 Zotero 可以保持打开。

单次同步时指定数据目录：

```bash
python sync_zotero.py --zotero-dir "D:\path\to\Zotero"
```

仪表盘上的 **同步数据** 按钮由服务端触发重新同步，需要在启动服务前设置环境变量：

```powershell
# Windows PowerShell
$env:ZOTERO_DATA_DIR = "D:\path\to\Zotero"
.\start-app.cmd
```

```bash
# macOS / Linux
export ZOTERO_DATA_DIR="/path/to/Zotero"
bash start-app.sh
```

`app_server.py` 会继承 `ZOTERO_DATA_DIR`，它启动的每次重新同步也会继续使用该目录。

### 同步

Zotero 数据变化后重新运行：

```bash
python sync_zotero.py
```

仪表盘读取生成的 `output/data/library.json`。同步过程不会修改 Zotero。

### 配置

先把示例配置复制为本地配置：

Windows PowerShell：

```powershell
Copy-Item config\categories.example.json config\categories.json
Copy-Item config\ai.example.json config\ai.json
```

macOS / Linux：

```bash
cp config/categories.example.json config/categories.json
cp config/ai.example.json config/ai.json
```

#### 分类配置

`config/categories.json` 用于定义兜底分类：

```json
{
  "default_category_id": "unsorted",
  "categories": [
    {
      "id": "overview",
      "name": "综述与入门",
      "description": "可选说明",
      "color": "#3f7f76",
      "keywords": ["review", "overview"],
      "item_ids": [],
      "item_keys": []
    }
  ]
}
```

字段说明：

- `id`：稳定且唯一的标识符
- `name`：显示名称
- `description`：可选的分类说明
- `color`：仪表盘使用的十六进制颜色
- `keywords`：用于自动归类的子串或小写词元
- `item_ids`：显式归入该分类的 Zotero 条目 ID
- `item_keys`：显式归入该分类的 Zotero 条目 key

当条目已属于 Zotero 集合时，集合归属优先于关键词匹配。

#### AI 报告

`config/ai.json` 用于选择报告来源：

```json
{
  "provider": "codex",
  "base_url": "https://api.openai.com/v1/chat/completions",
  "model": "",
  "api_key": ""
}
```

`provider` 可选值：

- `codex`：调用本地 Codex CLI
- `api`：调用兼容 OpenAI 的 chat completions 接口

使用 API 模式时需填写 `base_url`、`model` 和 `api_key`；密钥也可以通过
`OPENAI_API_KEY` 或 `AI_API_KEY` 环境变量提供。

### 命令行参数

`sync_zotero.py`：

```text
--zotero-dir PATH       Zotero 数据目录
--output PATH           输出目录
--library-id ID         Zotero 文献库 ID（默认 1）
--categories PATH       分类配置文件
```

`app_server.py`：

```text
--port PORT             服务端口（默认 5187）
```

### REST 接口

本地服务提供以下接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/state` | 文献库、分类和 AI 状态 |
| GET | `/api/categories` | 当前分类 |
| PUT | `/api/categories` | 保存本地分类规则并重新同步 |
| GET | `/api/note/{id}` | 单条文献的手写笔记段落 |
| PUT | `/api/note/{id}` | 保存手写笔记段落 |
| PUT | `/api/items/{id}/categories` | 设置本地分类并重新同步 |
| POST | `/api/sync` | 从 Zotero 重新同步 |
| GET | `/api/ai/config` | AI 配置状态 |
| PUT | `/api/ai/config` | 保存 AI 设置 |
| POST | `/api/ai/report` | 生成报告 |
| POST | `/api/report/export` | 把报告导出到输出目录 |

### 输出目录结构

```text
output/
├── README.md
├── literature-map.md
├── questions.md
├── glossary.md
├── notes/
│   └── *.md
├── dashboard/
│   └── index.html
├── data/
│   ├── library.json
│   └── categories.runtime.json
└── reports/
```

`output/`、`.cache/` 和本地配置文件都已排除在版本控制之外，避免把私人批注和
API 密钥发布出去。

### 隐私

- Zotero 数据从本地快照读取。
- 生成的笔记、批注和报告只保存在本地输出目录。
- 生成报告时只会发送所选报告范围引用的内容，以及你在请求中填写的指令。
- 程序不会上传 Zotero 数据。

### 已知限制

- 分类依据 Zotero 集合，但不会写回 Zotero。
- 想把条目移动到别的分类，需要先修改它的 Zotero 集合再重新同步。
- 本项目不能替代 Zotero 自带的笔记编辑和备份工具。
- Codex CLI 需要访问用户的 Codex 配置目录；若无法访问，可以改用 API 模式。

### 常见问题排查

- 提示 `Python 3.10 or newer was not found`：从
  <https://www.python.org/downloads/> 安装 Python，安装时勾选
  **Add Python to PATH**，安装完成后重新打开终端。
- 服务能启动但仪表盘报 Zotero 数据库错误：确认
  `%USERPROFILE%\Zotero\zotero.sqlite` 或 `~/Zotero/zotero.sqlite` 存在，
  或设置 `ZOTERO_DATA_DIR`。
- `5187` 端口被其他程序占用：改用
  `python app_server.py --port 5190`，然后访问
  `http://127.0.0.1:5190`；macOS/Linux 也可执行
  `PORT=5190 bash start-app.sh`。

### 许可证

基于 [MIT License](LICENSE) 发布。
