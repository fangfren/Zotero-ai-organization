# Zotero Research Workbench

[English](#english) | [简体中文](#简体中文)

Research Workbench is a standalone Zotero plugin that imports README or
documentation files, links them to Zotero literature items, and generates
structured research reports through the Codex CLI that is already installed
and signed in on your computer.

研究助手是一个独立的 Zotero 插件，可以导入 README 或说明文档、把文档与 Zotero
文献关联，并通过电脑上已经安装且已登录的 Codex CLI 生成结构化研究报告。

The plugin does **not** require an API key, a Python installation, a local web
server, or an extra model service. The only AI runtime it calls is `codex`.

插件**不需要 API Key、不需要安装 Python、不需要本地服务器，也不需要额外配置模型
服务**。它唯一调用的 AI 运行时是 `codex`。

---

## English

### What You Get

- A real Zotero `.xpi` plugin that can be installed from a single file.
- README import from `owner/repo`, a GitHub repository URL, a GitHub file URL,
  a direct Markdown or text URL, or a local file path.
- Automatic attachment linking:
  - One selected item: the README is added as a child attachment.
  - Multiple selected items: the README is added once as a standalone
    attachment and connected through Zotero related items.
- Reports generated from Zotero metadata, abstracts, notes, PDF annotations,
  PDF full text, attachment lists, and imported README files.
- Four built-in report modes:
  - Problem, method and findings
  - Multi-paper comparison
  - Quick digest
  - Custom instruction only
- A default research report template with these sections:
  1. Problem being solved
  2. Proposed method and technical route
  3. Key findings and evidence
  4. Data, experiment or simulation setup
  5. Limitations, assumptions and open questions
  6. Relevance to my research
  7. Reproducibility checklist
  8. Links to related material
- Reports saved as native Zotero notes instead of files outside your library.
- A visible Research Workbench button in the Zotero item toolbar, with direct
  entries for README import, report generation, and settings.
- A native Zotero preferences pane with a built-in Codex connection test.
- English and Simplified Chinese localization.

### Requirements

- Zotero desktop 7 or newer. Zotero 10 is supported.
- Codex CLI installed on the same computer.
- A working Codex login. A ChatGPT subscription login is enough. No API key is
  needed for this plugin.
- Internet access when Codex sends the assembled context to the service using
  your signed-in account.

Before using the plugin, verify Codex in a terminal:

```powershell
codex --version
codex login status
```

If `codex login status` does not report a login, run:

```powershell
codex login
```

### Install the Plugin

1. Download the release file:

   ```text
   release/zotero-research-workbench-1.0.1.xpi
   ```

   Download it from the repository
   [release folder](https://github.com/fangfren/Zotero-ai-organization/tree/main/release),
   or build it locally with the command in "Build the XPI" below.

2. Open Zotero.
3. Go to `Tools -> Add-ons`.
4. Click the gear button and choose `Install Add-on From File...`.
5. Select `zotero-research-workbench-1.0.1.xpi`.
6. Confirm the installation and restart Zotero if requested.

The XPI contains only the plugin. No Python installation, local server, or
extra runtime is required. The plugin is published with an `update_url`, so
future versions installed from this repository can be updated from Zotero's
add-on manager.

### First Run

1. Open `Edit -> Settings -> Research Workbench`.
2. Leave `Codex executable` blank for automatic detection, or enter the full
   path to `codex.exe`, `codex.cmd`, or your Codex installation directory.
3. Click `Detect Codex`.
4. A successful check reports the detected path and the version reported by
   Codex. It also performs a real `codex exec` call using your current login.

The plugin searches `PATH` and common Codex install locations. On Windows this
includes the versioned folders under:

```text
%LOCALAPPDATA%\OpenAI\Codex\bin
%APPDATA%\npm
%USERPROFILE%\.codex\bin
```

### Where to Click

After the plugin is enabled, look at the toolbar directly above the Zotero item
list. A Research Workbench icon appears next to the attachment and note buttons.
Click it to open this menu:

- `Import README for Selected Items`
- `Generate AI Report`
- `Research Workbench Settings`

The same actions are also available from `Tools`, the item right-click menu,
and the `Research Workbench` section on the right side of the item pane.

If the icon is missing, restart Zotero once. If it is still missing, open
`Tools -> Add-ons`, disable Research Workbench, enable it again, and restart
Zotero. Updating from an older XPI requires Zotero to reload the plugin before
the new toolbar button appears.

### Import a README and Link It to Literature

1. Select one or more regular literature items in Zotero.
2. Use one of these entry points:
   - Item toolbar: click the Research Workbench icon and choose
     `Import README for Selected Items`
   - Item pane: `Research Workbench -> Import README`
   - Right-click menu: `Import README and Link to This Item`
   - Main menu: `Tools -> Import README for Selected Items`
3. Enter one of the supported inputs:
   - `owner/repo`
   - `https://github.com/owner/repo`
   - `https://github.com/owner/repo/blob/main/README.md`
   - A direct `raw.githubusercontent.com` or other direct text URL
   - A local path such as `C:\projects\demo\README.md`
   - A UNC path, `file://` URL, or a path beginning with `~/`

The imported attachment receives the tag `research-workbench:readme`, which
makes it easy to find later. Imported Markdown and text attachments are shown
in the item pane for the selected literature.

### Generate a Report

1. Select one or more regular literature items.
2. Click the Research Workbench icon in the item toolbar and choose
   `Generate AI Report`, or use the `Research Workbench` item pane and menu.
3. Choose a template.
4. Optionally enter an extra instruction, for example:

   ```text
   Focus on the control strategy, simulation settings, and unresolved limitations.
   ```

5. Click `Generate report`.

For a single item, the generated note is attached to that item. For multiple
items, the note is created as a standalone note, linked as a related item to
each source, and placed in the active collection when possible.

Reports are written in Markdown inside a Zotero note. The plugin converts
headings, lists, tables, quotations, links, and code blocks into HTML so the
note remains readable in the Zotero note editor.

### What Is Sent to Codex

The plugin assembles the selected material locally and passes it to the
signed-in Codex CLI. Depending on the settings, this can include:

- Title, authors, year, publication, DOI, URL, item type, and abstract.
- Zotero notes.
- PDF annotations and comments.
- Extracted PDF full text.
- Attachment names and content types.
- Imported README and documentation attachments.

The plugin itself does not call an AI API and does not contain an API key.
Codex handles the authenticated request. Review your own privacy requirements
before sending sensitive or unpublished material.

### Settings

The preference pane supports:

- `Codex executable`
- `Model override`
- `Extra CLI arguments`
- `Timeout in seconds`
- Default report template and report language
- Default extra instruction
- PDF text, annotations, notes, attachment list, and imported documentation
  toggles
- Maximum total context characters
- Maximum characters per imported document
- Whether to open the generated note
- Whether to add the `research-workbench:report` tag

Settings are saved when changed. `Restore Defaults` resets every Research
Workbench preference.

### Privacy

The plugin reads only the Zotero items you select. It assembles the source
material on your computer and starts the local Codex CLI. The CLI then uses
your existing Codex login to perform the request. The plugin does not create
any additional network connection, does not upload files to a separate
server, and does not store an API key.

### Troubleshooting

#### Codex is not found

Open the Research Workbench settings and enter the full path to the executable.
On Windows, a typical path looks like:

```text
C:\Users\<name>\AppData\Local\OpenAI\Codex\bin\<version>\codex.exe
```

Click `Detect Codex` after changing the path.

#### Codex is found but not logged in

Run this in a terminal:

```powershell
codex login status
```

If it is not logged in, run `codex login` and complete the browser flow. The
plugin uses the same Codex home directory and login state as that terminal.

#### The report times out

Increase `Timeout in seconds` in the settings, reduce the number of selected
items, or lower `Maximum total context characters`.

#### A GitHub URL returns HTML instead of Markdown

Use the repository URL, a `blob` URL, or a direct raw Markdown URL. The plugin
tries common README filenames and branches automatically.

#### A local path is not accepted

Use an absolute path. Paths containing spaces are supported. You can also use
the format:

```text
file:///C:/projects/demo/README.md
```

#### PDF full text is empty

Open the PDF in Zotero and make sure Zotero has indexed its text. Scanned PDFs
need OCR before Zotero can provide useful full text. The report can still use
metadata, notes, and annotations.

#### The plugin does not appear

Confirm that Zotero is version 7 or newer, restart Zotero, and check
`Help -> Debug Output for Troubleshooting`. Temporarily disabling and
re-enabling the plugin also refreshes its toolbar button, menu, item pane, and
preference registrations.

#### The toolbar icon is missing

Make sure the installed XPI is `1.0.1` or newer. Zotero 7 and 10 show the button
in the toolbar above the item list, near the attachment and note buttons.
Restart Zotero after installing or updating, and disable and re-enable the
plugin if the toolbar is still unchanged. The plugin also remains available
from `Tools` and the item pane while the button is hidden.

### Build the XPI

From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

The script validates the required files, reads the version from
`zotero-plugin/manifest.json`, and writes:

```text
release/zotero-research-workbench-1.0.1.xpi
```

The XPI root contains `manifest.json`, `bootstrap.js`, `prefs.js`, `content/`,
and `locale/`. It does not contain the legacy Python dashboard.

### Repository Layout

```text
zotero-plugin/                 Zotero XPI source
  bootstrap.js                 Add-on lifecycle entry point
  manifest.json                Add-on manifest and update URL
  prefs.js                     Default preferences
  content/                     Main logic, preferences UI, styles, icons
  locale/                      English and Simplified Chinese strings
scripts/build-xpi.ps1          XPI build script
release/                       Built XPI and update manifest
README.md                      Bilingual documentation
LICENSE                        MIT license
```

The repository contains only the Zotero plugin. There is no Python backend, no
local web server, and no other component to install.

### License

MIT. See `LICENSE`.

---

## 简体中文

### 功能概览

- 提供可直接安装的 Zotero `.xpi` 插件，不再依赖外部脚本或本地服务。
- 支持从以下来源导入 README：
  - `owner/repo`
  - GitHub 仓库链接
  - GitHub 文件链接
  - 直接的 Markdown 或文本链接
  - 本地文件路径
- 自动建立文献关联：
  - 只选中一条文献时，README 作为该文献的子附件。
  - 选中多条文献时，README 作为独立附件导入，并通过 Zotero
    `相关条目` 与这些文献关联。
- 报告可使用 Zotero 元数据、摘要、笔记、PDF 批注、PDF 全文、附件清单和
  已导入的 README。
- 内置四种报告方式：
  - 问题、方法与结论
  - 多篇对比综述
  - 快速摘要
  - 仅按自定义要求
- 默认研究报告模板包含八个部分：
  1. 要解决什么问题
  2. 提出的方法与技术路线
  3. 关键发现与证据
  4. 数据、实验或仿真设置
  5. 局限、假设与未解决问题
  6. 对我研究方向的意义
  7. 可复现要点
  8. 相关文献与材料关联
- 报告直接保存为 Zotero 笔记，不生成游离于文献库之外的文件。
- 在 Zotero 条目工具栏提供常驻的研究助手按钮，可直接导入 README、
  生成报告或打开设置。
- 提供原生 Zotero 设置页和一键 Codex 连接检测。
- 提供英语和简体中文本地化。

### 运行要求

- Zotero 桌面版 7 或更高版本，支持 Zotero 10。
- 同一台电脑已经安装 Codex CLI。
- Codex CLI 已经登录。ChatGPT 订阅登录即可，不需要提供 API Key。
- Codex 使用你的账号处理请求时需要联网。

建议先在终端确认：

```powershell
codex --version
codex login status
```

如果尚未登录：

```powershell
codex login
```

### 安装插件

1. 找到构建好的插件文件：

   ```text
   release/zotero-research-workbench-1.0.1.xpi
   ```

   可以直接从仓库的
   [release 目录](https://github.com/fangfren/Zotero-ai-organization/tree/main/release)
   下载，也可以按下方“构建 XPI”一节在本地自行构建。

2. 打开 Zotero。
3. 进入 `工具 -> 插件`。
4. 点击右上角齿轮，选择 `从文件安装插件...`。
5. 选择 `zotero-research-workbench-1.0.1.xpi`。
6. 确认安装。如果 Zotero 提示重启，请重启后再使用。

这个 XPI 只包含插件本体，不需要 Python、不需要本地服务器，也不需要其他运行时。
插件内置了 `update_url`，从本仓库安装后可以直接在 Zotero 插件管理器中检查更新。

### 第一次使用

1. 打开 `编辑 -> 设置 -> 研究助手`。
2. `Codex 可执行文件` 可以留空自动检测，也可以填写 `codex.exe`、
   `codex.cmd` 的完整路径，或 Codex 安装目录。
3. 点击 `检测 Codex`。
4. 检测成功后会显示实际路径和版本，并会真正调用一次本机 `codex exec`，
   用来确认订阅登录可用。

插件会自动搜索 `PATH` 和常见安装目录。在 Windows 上会检查：

```text
%LOCALAPPDATA%\OpenAI\Codex\bin
%APPDATA%\npm
%USERPROFILE%\.codex\bin
```

### 界面入口在哪里

插件启用后，Zotero 条目列表上方的工具栏中会出现研究助手图标，位置在
“添加附件”和“添加笔记”按钮附近。点击图标会展开：

- `为选中文献导入 README`
- `生成 AI 研究报告`
- `研究助手设置`

同样的功能也可以从 `工具` 菜单、文献右键菜单，以及条目信息栏右侧的
`研究助手` 面板进入。

如果看不到图标，请先重启一次 Zotero。如果仍然没有，进入 `工具 -> 插件`，
先禁用研究助手再重新启用，然后重启 Zotero。从旧版 XPI 更新后，必须让
Zotero 重新加载插件，新的工具栏按钮才会出现。

### 导入 README 并关联文献

1. 在 Zotero 中选中一篇或多篇普通文献。
2. 从以下任意入口执行导入：
   - 条目工具栏：点击研究助手图标，选择 `为选中文献导入 README`
   - 条目信息栏：`研究助手 -> 导入 README`
   - 文献右键菜单：`导入 README 并关联到这篇文献`
   - 主菜单：`工具 -> 为选中文献导入 README`
3. 输入以下任一格式：
   - `owner/repo`
   - `https://github.com/owner/repo`
   - `https://github.com/owner/repo/blob/main/README.md`
   - 可直接下载文本的 URL
   - `C:\projects\demo\README.md`
   - UNC 路径、`file://` URL，或 `~/...` 开头的路径

导入后的附件会自动带 `research-workbench:readme` 标签，便于后续检索。选中的
文献条目信息栏会显示已经关联的 README 和说明文档。

### 生成研究报告

1. 选中一篇或多篇普通文献。
2. 点击条目工具栏中的研究助手图标并选择 `生成 AI 研究报告`，也可以使用
   `研究助手` 条目信息栏或菜单。
3. 选择报告模板。
4. 根据需要填写补充要求，例如：

   ```text
   重点讲清控制策略、仿真参数设置，以及还没有解决的局限。
   ```

5. 点击 `生成报告`。

单篇文献的报告会自动挂到该文献下面。多篇文献的报告会作为独立笔记创建，尽量
放入当前分类，并通过 `相关条目` 与每篇来源文献关联。

报告以 Markdown 生成，再转换为 Zotero 笔记 HTML。标题、列表、表格、引用、
链接和代码块都会保留，便于直接在 Zotero 笔记编辑器中阅读和继续修改。

### 发送给 Codex 的内容

插件只在本机整理当前选中的材料，然后交给已登录的 Codex CLI。根据设置，材料
可能包括：

- 标题、作者、年份、出版物、DOI、URL、条目类型和摘要。
- Zotero 笔记。
- PDF 批注和批注评论。
- 从 PDF 提取的全文。
- 附件名称和内容类型。
- 已导入的 README 和说明文档。

插件本身不调用 AI API，不保存 API Key，也不额外连接其他模型服务。认证和请求
由 Codex CLI 使用你的现有登录完成。处理敏感或未公开材料前，请结合自己的隐私
要求判断是否适合发送。

### 设置说明

设置页支持：

- `Codex 可执行文件`
- `模型覆盖`
- `额外 CLI 参数`
- `超时时间`
- 默认报告模板和报告语言
- 默认补充要求
- PDF 全文、批注、笔记、附件清单、导入文档开关
- 总上下文字符上限
- 每份导入文档的字符上限
- 生成后是否自动打开笔记
- 是否添加 `research-workbench:report` 标签

修改设置后会自动保存。`恢复默认设置` 会重置研究助手的全部偏好。

### 隐私说明

插件只读取你主动选中的 Zotero 条目。它在你的电脑上组装材料，并启动本机
Codex CLI。Codex 随后使用你已有的登录状态处理请求。插件不会建立额外的上传
连接，不会把文件发送到独立服务器，也不会保存 API Key。

### 常见问题

#### 找不到 Codex

在设置页填写可执行文件的完整路径。Windows 上通常类似：

```text
C:\Users\<用户名>\AppData\Local\OpenAI\Codex\bin\<版本>\codex.exe
```

修改后点击 `检测 Codex`。

#### 能找到 Codex，但没有登录

在终端执行：

```powershell
codex login status
```

如果显示未登录，执行 `codex login` 并完成浏览器登录。插件使用的是同一个
Codex 用户目录和登录状态。

#### 生成报告超时

提高 `超时时间`，减少一次选中的文献数量，或降低 `总上下文字符上限`。

#### GitHub 链接下载到的是网页

请使用仓库地址、`blob` 地址或直接 raw Markdown 地址。插件会自动尝试常见的
README 文件名和分支名。

#### 本地路径无法识别

请使用绝对路径。路径中包含空格也可以。也可以使用：

```text
file:///C:/projects/demo/README.md
```

#### PDF 全文为空

请先用 Zotero 打开 PDF，确认 Zotero 已建立全文索引。扫描版 PDF 需要先做
OCR。即使全文不可用，报告仍然可以使用元数据、笔记和批注。

#### 插件没有出现在界面中

确认 Zotero 版本不低于 7，重启 Zotero，并查看
`帮助 -> 调试输出`。也可以在插件管理器中暂时禁用再重新启用，刷新菜单和
设置页注册；工具栏按钮、菜单、条目信息栏和设置页会一起重新加载。

#### 看不到工具栏图标

请确认安装的是 `1.0.1` 或更高版本的 XPI。Zotero 7 和 Zotero 10 会把按钮显示
在条目列表上方的工具栏中，位置靠近“添加附件”和“添加笔记”按钮。安装或更新
后需要重启 Zotero；如果工具栏仍然没有变化，请在插件管理器中禁用再重新启用
研究助手。即使按钮暂时隐藏，也仍然可以通过 `工具` 菜单和条目信息栏使用插件。

### 构建 XPI

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

脚本会检查必要文件、读取 `zotero-plugin/manifest.json` 中的版本号，并输出：

```text
release/zotero-research-workbench-1.0.1.xpi
```

XPI 根目录直接包含 `manifest.json`、`bootstrap.js`、`prefs.js`、`content/`
和 `locale/`，不会包含旧版 Python 网页工具。

### 仓库结构

```text
zotero-plugin/                 Zotero XPI 源码
  bootstrap.js                 插件生命周期入口
  manifest.json                插件清单与更新地址
  prefs.js                     默认偏好设置
  content/                     主逻辑、设置页、样式与图标
  locale/                      英语和简体中文字符串
scripts/build-xpi.ps1          XPI 构建脚本
release/                       构建后的 XPI 与更新清单
README.md                      双语说明文档
LICENSE                        MIT 许可证
```

仓库中只包含 Zotero 插件本体，没有 Python 后端、本地网页服务或其他需要安装
的组件。

### 许可证

MIT，详见 `LICENSE`。
