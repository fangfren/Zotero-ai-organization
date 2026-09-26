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
- Imports supporting documents in one click: paste a GitHub repository, raw
  file, or plain text link (the `owner/repo` shorthand works too), drag in local
  files, or paste text, then link each document to one or more Zotero items.
- Generates reports with a Codex subscription login instead of an API key: the
  server calls the locally installed `codex` CLI and reuses the ChatGPT session
  you already logged in with.
- Ships report templates, including research question / method / conclusion,
  multi-paper comparison, quick digest, and free-form custom instructions.
- Writes reports and JSON state under a local output directory.
- Does not write to the Zotero database.

### Requirements

- Python 3.10 or newer
- Zotero desktop with a local data directory
- Optional: Codex CLI with a ChatGPT subscription login for report generation
  (no API key needed)
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

### Imported Material

The dashboard's **Import documents** dialog keeps supporting documents next to
the literature itself:

- **One-click README**: paste `owner/repo`, `https://github.com/owner/repo`, a
  `raw.githubusercontent.com` link, or any plain text/Markdown URL. A repository
  link is resolved to `README.md`, `README.rst`, `README.txt`, `readme.md`, or
  `README` on the default branch (`main`, then `master`).
- **Local files**: drop or select `.md`, `.markdown`, `.txt`, `.rst`, `.json`,
  `.yml`, `.yaml`, or `.csv` files, several at a time.
- **Pasted text**: give the document a name and paste the content.
- **Linking**: tick the Zotero items a document belongs to before importing, or
  edit the links later. Linked material appears in the item detail panel and is
  sent to the AI together with that item's notes and annotations.

Imports are stored as Markdown:

```text
output/imports/<id>.md      imported content
output/data/imports.json    index: name, links, size, source, timestamp
```

Nothing is written back to Zotero. Deleting an import removes both the file and
its index entry.

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
  "api_key": "",
  "codex_command": "",
  "codex_model": "",
  "codex_extra_args": "",
  "codex_timeout": 600,
  "report_template": "research"
}
```

`provider` accepts:

- `codex` (default): runs the local Codex CLI and reuses your ChatGPT
  subscription login. No API key is required or used.
- `api`: calls an OpenAI-compatible chat completions endpoint

**Codex subscription mode**

1. Install the Codex CLI and log in once in a terminal:

   ```bash
   codex login
   ```

2. Open **AI settings** in the dashboard. The status row shows the detected
   executable, its version, the login state, and how many imported documents are
   linked to items.
3. Click **Test Codex** to run a real self-check before generating a report.

The executable is resolved in this order:

1. `codex_command` in `config/ai.json`, set through the AI settings dialog
2. the `RESEARCH_WORKBENCH_CODEX` environment variable
3. the `CODEX_BIN` environment variable
4. `codex`, `codex.cmd`, or `codex.exe` on `PATH`
5. common install locations, such as the Codex desktop app bundle and
   `~/.local/bin`

Optional Codex settings:

- `codex_model`: model passed to the CLI; empty means the CLI default
- `codex_extra_args`: extra CLI flags, for example `--sandbox read-only`
- `codex_timeout`: seconds before a report call is aborted (60-3600, default
  600)

For API mode, set `base_url`, `model`, and `api_key`. The API key can also be
provided through `OPENAI_API_KEY` or `AI_API_KEY`.

Report templates, chosen in the report dialog or through `report_template`:

| Template | Sections |
|---|---|
| `research` (default) | 要解决什么问题 / 提出的方法 / 关键发现与证据 / 数据、实验或仿真设置 / 局限、假设与未解决问题 / 对我研究方向的意义 / 可复现要点 / 相关文献关联 |
| `comparison` | 主题与检索范围 / 各文献要解决的问题 / 方法路线对比 / 指标、数据与结论对比 / 共识与分歧 / 研究空白与机会 / 建议的下一步工作 |
| `quick` | 一句话结论 / 要解决什么问题 / 提出的方法 / 关键结果 / 局限 / 可以直接复用的点 |
| `custom` | No fixed sections; the report follows your instructions only |

Section headings are written in the language stored in `app_server.py`, so the
generated report keeps the same structure for every user.

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
| GET | `/api/ai/config` | AI provider status (`?probe=1` adds a live Codex probe) |
| PUT | `/api/ai/config` | Save AI settings |
| POST | `/api/ai/test` | Run a Codex self-check |
| POST | `/api/ai/report` | Generate a report |
| POST | `/api/report/export` | Export a report to the output directory |
| GET | `/api/imports` | Imported documents; filter with `?item_id=` or `?item_key=` |
| POST | `/api/imports` | Save imported documents and their item links |
| POST | `/api/imports/readme` | Fetch and import a README by URL or `owner/repo` |
| GET | `/api/imports/{id}` | One imported document, including its content |
| PUT | `/api/imports/{id}` | Update the linked items of an import |
| DELETE | `/api/imports/{id}` | Delete an imported document |

### Output Layout

```text
output/
├── README.md
├── literature-map.md
├── questions.md
├── glossary.md
├── notes/
│   └── *.md
├── imports/
│   └── *.md
├── dashboard/
│   └── index.html
├── data/
│   ├── library.json
│   ├── categories.runtime.json
│   └── imports.json
├── logs/
│   └── codex-*.log
└── reports/
```

`output/`, `.cache/`, and local configuration files are excluded from version
control to prevent private Zotero annotations and API keys from being published.

### Privacy

- Zotero data is read from a local snapshot.
- Generated notes, annotations, and reports stay in the local output directory.
- API or Codex report generation sends only the material referenced by the
  selected report scope (item notes, annotations, and linked imports) plus the
  instruction supplied in the request.
- The application does not upload Zotero data.

### Limitations

- Classification follows Zotero collections but does not write back to Zotero.
- Moving an item between categories requires changing its Zotero collection and
  resyncing.
- The application is not a replacement for Zotero's own note editing or backup
  tools.
- Imported documents and their item links live in `output/` only; Zotero itself
  is never modified.
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
- The AI settings dialog reports **Codex not found**: install the Codex CLI,
  then paste the full path to the executable into **AI settings → Codex
  command**, or set `RESEARCH_WORKBENCH_CODEX`.
- The AI settings dialog reports **Codex not logged in**: run `codex login` in a
  terminal, finish the browser login, and reopen the dialog. The workbench reuses
  that session and never asks for an API key in Codex mode.
- Codex reports time out on a large library: raise `codex_timeout` in AI settings
  (up to 3600 seconds) or narrow the report scope to a single item.
- Codex exits with a permission error for `~/.codex`: run the server with the
  same user account that ran `codex login`, and make sure that account can read
  the Codex configuration directory.
- A README link fails to import: the workbench only follows public URLs and
  downloads up to 1.5 MB of text. Private repositories need a raw URL that
  already contains a token.

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
- 一键导入补充资料：粘贴 GitHub 仓库、raw 文件或纯文本链接（支持 `owner/repo`
  简写）、拖入本地文件、或直接粘贴文本，再把资料关联到一篇或多篇文献。
- 支持用 Codex 订阅登录生成报告，不需要 API 密钥：服务调用本机 `codex` 命令，
  直接复用你已经登录的 ChatGPT 订阅会话。
- 内置报告模板：研究问题—方法—结论、多篇对比综述、快速摘要，以及完全自定义。
- 报告与 JSON 状态写入本地输出目录。
- 不会向 Zotero 数据库写入任何内容。

### 运行要求

- Python 3.10 或更高版本
- 已安装 Zotero 桌面端，并存在本地数据目录
- 可选：本地 Codex CLI（用 ChatGPT 订阅登录即可，不需要 API 密钥），用于生成
  报告
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

### 导入资料（README 与文档）

仪表盘的**导入文档**弹窗用来把补充资料和文献放在一起管理：

- **一键导入 README**：可以粘贴 `owner/repo`、`https://github.com/owner/repo`、
  `raw.githubusercontent.com` 链接，或其他纯文本 / Markdown 链接。仓库地址会按
  `README.md`、`README.rst`、`README.txt`、`readme.md`、`README` 的顺序，在默认
  分支（先 `main`，再 `master`）上自动抓取。
- **本地文件**：拖入或选择 `.md`、`.markdown`、`.txt`、`.rst`、`.json`、`.yml`、
  `.yaml`、`.csv` 文件，支持一次选多个。
- **粘贴文本**：填写资料名称后直接粘贴内容。
- **关联文献**：导入前勾选这份资料属于哪些文献，之后也可以随时修改。已关联的
  资料会显示在文献详情里，并在生成报告时连同该文献的笔记和批注一起发送给 AI。

导入内容按 Markdown 保存：

```text
output/imports/<id>.md      导入的正文
output/data/imports.json    索引：名称、关联文献、大小、来源、时间
```

不会向 Zotero 写入任何内容；删除导入资料时，正文文件和索引记录会一起删除。

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
  "api_key": "",
  "codex_command": "",
  "codex_model": "",
  "codex_extra_args": "",
  "codex_timeout": 600,
  "report_template": "research"
}
```

`provider` 可选值：

- `codex`（默认）：调用本地 Codex CLI，复用你的 ChatGPT 订阅登录，不需要也不
  会使用 API 密钥
- `api`：调用兼容 OpenAI 的 chat completions 接口

**Codex 订阅登录模式**

1. 安装 Codex CLI，并在终端里登录一次：

   ```bash
   codex login
   ```

2. 打开仪表盘的 **AI 设置**。状态区会显示检测到的可执行文件、版本、登录状态，
   以及当前关联了多少份导入资料。
3. 点 **测试 Codex** 先跑一次真实自检，再生成报告。

`codex` 可执行文件按以下顺序查找：

1. `config/ai.json` 里的 `codex_command`（在 AI 设置里填写）
2. 环境变量 `RESEARCH_WORKBENCH_CODEX`
3. 环境变量 `CODEX_BIN`
4. `PATH` 中的 `codex`、`codex.cmd` 或 `codex.exe`
5. 常见安装位置，例如 Codex 桌面端安装目录和 `~/.local/bin`

Codex 相关可选设置：

- `codex_model`：传给 CLI 的模型；留空表示使用 CLI 默认值
- `codex_extra_args`：额外的命令行参数，例如 `--sandbox read-only`
- `codex_timeout`：生成报告的等待秒数，超时即中断（60-3600，默认 600）

使用 API 模式时需填写 `base_url`、`model` 和 `api_key`；密钥也可以通过
`OPENAI_API_KEY` 或 `AI_API_KEY` 环境变量提供。

报告模板可在报告弹窗中选择，也可用 `report_template` 指定：

| 模板 | 章节 |
|---|---|
| `research`（默认） | 要解决什么问题 / 提出的方法 / 关键发现与证据 / 数据、实验或仿真设置 / 局限、假设与未解决问题 / 对我研究方向的意义 / 可复现要点 / 相关文献关联 |
| `comparison` | 主题与检索范围 / 各文献要解决的问题 / 方法路线对比 / 指标、数据与结论对比 / 共识与分歧 / 研究空白与机会 / 建议的下一步工作 |
| `quick` | 一句话结论 / 要解决什么问题 / 提出的方法 / 关键结果 / 局限 / 可以直接复用的点 |
| `custom` | 不使用固定章节，完全按你填写的补充要求组织报告 |

章节名称取自 `app_server.py`，所以每个人生成的报告结构一致。

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
| GET | `/api/ai/config` | AI 配置状态（加 `?probe=1` 会实时探测 Codex） |
| PUT | `/api/ai/config` | 保存 AI 设置 |
| POST | `/api/ai/test` | 运行一次 Codex 自检 |
| POST | `/api/ai/report` | 生成报告 |
| POST | `/api/report/export` | 把报告导出到输出目录 |
| GET | `/api/imports` | 导入资料列表，可用 `?item_id=` 或 `?item_key=` 过滤 |
| POST | `/api/imports` | 保存导入资料及其关联文献 |
| POST | `/api/imports/readme` | 用链接或 `owner/repo` 抓取并导入 README |
| GET | `/api/imports/{id}` | 单份导入资料，含正文 |
| PUT | `/api/imports/{id}` | 修改这份资料的关联文献 |
| DELETE | `/api/imports/{id}` | 删除这份导入资料 |

### 输出目录结构

```text
output/
├── README.md
├── literature-map.md
├── questions.md
├── glossary.md
├── notes/
│   └── *.md
├── imports/
│   └── *.md
├── dashboard/
│   └── index.html
├── data/
│   ├── library.json
│   ├── categories.runtime.json
│   └── imports.json
├── logs/
│   └── codex-*.log
└── reports/
```

`output/`、`.cache/` 和本地配置文件都已排除在版本控制之外，避免把私人批注和
API 密钥发布出去。

### 隐私

- Zotero 数据从本地快照读取。
- 生成的笔记、批注和报告只保存在本地输出目录。
- 生成报告时只会发送所选报告范围引用的内容（文献笔记、批注和已关联的导入资料）
  以及你在请求中填写的指令。
- 程序不会上传 Zotero 数据。

### 已知限制

- 分类依据 Zotero 集合，但不会写回 Zotero。
- 想把条目移动到别的分类，需要先修改它的 Zotero 集合再重新同步。
- 本项目不能替代 Zotero 自带的笔记编辑和备份工具。
- 导入的资料和关联关系只保存在 `output/` 里，不会修改 Zotero。
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
- AI 设置里提示**未找到 Codex**：安装 Codex CLI，然后把可执行文件的完整路径填到
  **AI 设置 → Codex 命令**，或设置环境变量 `RESEARCH_WORKBENCH_CODEX`。
- AI 设置里提示 **Codex 未登录**：先在终端执行 `codex login`，在浏览器里完成登录，
  再重新打开弹窗。Codex 模式下工作台复用这个登录，不会索要 API 密钥。
- 文献库较大时报告超时：在 AI 设置里调大 `codex_timeout`（最大 3600 秒），或把
  报告范围缩小到单篇文献。
- Codex 报 `~/.codex` 权限错误：请用执行过 `codex login` 的同一个系统账号运行
  服务，并确认该账号能读取 Codex 配置目录。
- README 抓取失败：工作台只抓取公开链接，且最多下载 1.5 MB 文本；私有仓库需要
  使用带 token 的 raw 链接。

### 许可证

基于 [MIT License](LICENSE) 发布。
