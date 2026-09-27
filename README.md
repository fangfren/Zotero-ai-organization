# Zotero Research Workbench

[English](#english) | [简体中文](#简体中文)

Research Workbench is a standalone Zotero plugin. It adds an **AI Chat** entry
to the right item-pane sidenav, opens an embedded chat page there, and talks to
the Codex CLI that is already installed and signed in on your computer. It also
imports README or documentation files and links them to Zotero literature
items.

研究助手是一个独立的 Zotero 插件。它在条目信息栏右侧的导航栏中增加 **AI 对话**
入口，点击后会在右侧栏内嵌打开聊天页面，并调用电脑上已经安装且已登录的 Codex
CLI。插件同时支持导入 README 或说明文档，并与 Zotero 文献条目建立关联。

The plugin does **not** require an API key, a Python installation, a local web
server, or an extra model service. The only AI runtime it calls is `codex`.

插件**不需要 API Key、不需要安装 Python、不需要本地服务器，也不需要额外配置模型
服务**。它唯一调用的 AI 运行时是 `codex`。

Version 1.0.2 removes the old report-generation feature. Chat is now the only
AI feature, and every literature item keeps its own multi-turn conversation.

1.0.2 已移除旧的 AI 报告生成功能。现在 AI 部分只保留对话，每篇文献各自维护
自己的多轮会话。

---

## English

### What You Get

- A real Zotero `.xpi` plugin that installs from a single file.
- An **AI Chat** button in the right item-pane sidenav, next to the other
  Zotero pane sections.
- An embedded chat page inside the right pane. No separate window, no browser
  tab, no external web app.
- Per-item multi-turn chat with the local Codex CLI. The first question sends
  the item context; later questions continue the same Codex session.
- Chat history and Codex session IDs persisted locally, so a conversation
  survives switching items and restarting Zotero.
- README import from `owner/repo`, a GitHub repository URL, a GitHub file URL,
  a direct Markdown or text URL, or a local file path.
- Automatic attachment linking:
  - One selected item: the README is added as a child attachment.
  - Multiple selected items: the README is added once as a standalone
    attachment and connected through Zotero related items.
- A list of linked README and documentation attachments under the chat box.
- A native Zotero preferences pane with a built-in Codex connection test.
- English and Simplified Chinese localization.

Report generation, report templates, report notes, and report tags have been
removed in 1.0.2. The plugin no longer writes anything into your notes.

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
   release/zotero-research-workbench-1.0.2.xpi
   ```

   Download it from the repository
   [release folder](https://github.com/fangfren/Zotero-ai-organization/tree/main/release),
   or build it locally with the command in "Build the XPI" below.

2. Open Zotero.
3. Go to `Tools -> Add-ons`.
4. Click the gear button and choose `Install Add-on From File...`.
5. Select `zotero-research-workbench-1.0.2.xpi`.
6. Confirm the installation and restart Zotero if requested.

The XPI contains only the plugin. No Python installation, local server, or
extra runtime is required. The plugin is published with an `update_url`, so
future versions installed from this repository can be updated from Zotero's
add-on manager.

If you already have an older version installed, install 1.0.2 over it and
restart Zotero. The old toolbar button and the report menu entries disappear,
and the new right-pane entry appears.

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

### Where the Chat Lives

After the plugin is enabled, select a regular literature item and look at the
right side of the Zotero window. In the vertical navigation strip at the right
edge of the item pane there is an **AI Chat** icon. Click it to switch the item
pane to the Research Workbench chat page.

The embedded page contains, from top to bottom:

- `New chat` and `Settings` buttons.
- The message list, with your questions and Codex replies.
- A question box. Press `Enter` to send, or `Shift+Enter` for a new line.
- `Send` while idle, which turns into `Stop` while a request is running.
- `Import README` for the current item.
- `Linked README / documents`, listing everything already linked to the item.

The same actions are also available outside the pane:

- `Tools -> Import README for Selected Items`
- `Tools -> Research Workbench Settings`
- Item right-click menu: `Import README and Link to This Item`

There is no toolbar button any more. Version 1.0.2 intentionally puts the entry
point in the right sidenav so it behaves like other Zotero pane plugins.

### Chat with Codex

1. Select a regular literature item.
2. Open the `AI Chat` section in the right item pane.
3. Type a question and press `Enter`.

For example:

```text
What problem does this paper solve, and what method does it propose?
Summarize the experiment setup and the main results.
What are the limitations the authors admit, and what is left open?
```

The first question in a conversation also carries the item context. Later
questions are sent to the same Codex session through `codex exec resume`, so
Codex remembers what you already discussed about that item.

Useful behavior:

- Each literature item has its own conversation and its own Codex session.
- `New chat` clears the current conversation after a confirmation prompt and
  starts a fresh session on the next question.
- `Stop` cancels the running request. The question stays in the list so you can
  see what was asked.
- Chat history and session IDs are stored as JSON files under your Zotero data
  directory:

  ```text
  <Zotero data directory>/research-workbench/chats/<libraryID>-<itemKey>.json
  ```

  The fallback locations are the Zotero profile directory and the system temp
  directory if the data directory is not writable.
- The plugin runs Codex in a read-only sandbox. It never lets Codex modify your
  Zotero files or your project files.

### Import a README and Link It to Literature

1. Select one or more regular literature items in Zotero.
2. Use one of these entry points:
   - Item pane: `AI Chat -> Import README`
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
makes it easy to find later. Imported Markdown and text attachments are listed
in the chat page for every literature item they are linked to.

### What Is Sent to Codex

The plugin assembles the selected material locally and passes it to the
signed-in Codex CLI. Depending on the settings, this can include:

- Title, authors, year, publication, DOI, URL, item type, and abstract.
- Zotero notes.
- PDF annotations and comments.
- Extracted PDF full text.
- Attachment names and content types.
- Imported README and documentation attachments.

The first message of a conversation contains this material. Follow-up messages
contain only your new question, because the Codex session already holds the
earlier context.

The plugin itself does not call an AI API and does not contain an API key.
Codex handles the authenticated request. Review your own privacy requirements
before sending sensitive or unpublished material.

### Settings

Open `Edit -> Settings -> Research Workbench`, or click `Settings` in the chat
page. The preference pane supports:

- `Codex executable`
- `Model override`
- `Extra CLI arguments`
- `Timeout in seconds` (60-3600, default 600)
- PDF full text, annotations, notes, attachment list, and imported
  documentation toggles
- Maximum total context characters
- Maximum characters per imported document

Settings are saved when changed. `Restore Defaults` resets every Research
Workbench preference.

### Privacy

The plugin reads only the Zotero items you select. It assembles the source
material on your computer and starts the local Codex CLI. The CLI then uses
your existing Codex login to perform the request. The plugin does not create
any additional network connection, does not upload files to a separate
server, and does not store an API key. Chat history is stored locally in your
Zotero data directory and is never uploaded by the plugin itself.

### Troubleshooting

#### The AI Chat entry is missing from the right pane

Make sure the installed XPI is 1.0.2. Then disable and re-enable Research
Workbench in `Tools -> Add-ons`, and restart Zotero. Zotero registers item-pane
sections only while the plugin is loading, so an update needs a reload.

Also check that you have selected a regular literature item. The section is
disabled for attachments, notes, and other non-regular items.

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

#### The reply times out

Increase `Timeout in seconds` in the settings, reduce the number of selected
items, or lower `Maximum total context characters`. The timeout applies to one
reply, not to the whole conversation.

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
need OCR before Zotero can provide useful full text. Chat can still use
metadata, notes, and annotations.

#### I want to clear everything for one item

Open that item's `AI Chat` section and click `New chat`. The stored JSON file
for that item is cleared. To remove imported documents, delete the
`research-workbench:readme` attachment in Zotero as usual.

### Build the XPI

From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

The script validates the required files, reads the version from
`zotero-plugin/manifest.json`, and writes:

```text
release/zotero-research-workbench-1.0.2.xpi
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

- 提供可直接安装的 Zotero `.xpi` 插件，一个文件即可完成安装。
- 在条目信息栏右侧导航栏中增加 **AI 对话** 按钮，和其他 Zotero 面板入口
  放在一起。
- 点击后在右侧栏内嵌打开聊天页面，不弹独立窗口，不打开浏览器，也不需要
  外部网页应用。
- 与本地 Codex CLI 进行多轮对话：第一条问题携带文献上下文，后续问题继续
  同一个 Codex 会话。
- 对话记录和 Codex 会话 ID 保存在本机，切换文献或重启 Zotero 后仍可继续。
- 支持从以下来源导入 README：`owner/repo`、GitHub 仓库链接、GitHub 文件
  链接、直接的 Markdown 或文本链接、本地文件路径。
- 自动建立文献关联：
  - 只选中一条文献时，README 作为该文献的子附件。
  - 选中多条文献时，README 作为独立附件导入，并通过 Zotero
    `相关条目` 与这些文献关联。
- 在聊天框下方列出已经关联的 README 和说明文档。
- 提供原生 Zotero 设置页和一键 Codex 连接检测。
- 提供英语和简体中文本地化。

1.0.2 已移除报告生成、报告模板、报告笔记和报告标签。插件不会再往你的笔记
里写入任何内容。

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
   release/zotero-research-workbench-1.0.2.xpi
   ```

   可以直接从仓库的
   [release 目录](https://github.com/fangfren/Zotero-ai-organization/tree/main/release)
   下载，也可以按下方“构建 XPI”一节在本地自行构建。

2. 打开 Zotero。
3. 进入 `工具 -> 插件`。
4. 点击右上角齿轮，选择 `从文件安装插件...`。
5. 选择 `zotero-research-workbench-1.0.2.xpi`。
6. 确认安装。如果 Zotero 提示重启，请重启后再使用。

这个 XPI 只包含插件本体，不需要 Python、不需要本地服务器，也不需要其他运行时。
插件内置了 `update_url`，从本仓库安装后可以直接在 Zotero 插件管理器中检查更新。

如果之前装过旧版本，直接用 1.0.2 覆盖安装并重启 Zotero。旧的工具栏按钮和
报告菜单会消失，新的右侧面板入口会出现。

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

### 对话入口在哪里

插件启用后，选中一篇普通文献，然后看 Zotero 窗口右侧。在条目信息栏最右侧
的竖排导航栏中会出现一个 **AI 对话** 图标，点击后条目信息栏会切换到研究
助手的聊天页面。

内嵌页面从上到下包括：

- `新建对话` 和 `设置` 按钮。
- 消息列表，显示你的提问和 Codex 的回复。
- 问题输入框。按 `Enter` 发送，按 `Shift+Enter` 换行。
- `发送` 按钮；请求执行期间会变成 `停止`。
- `导入 README`，为当前文献导入文档。
- `已关联的 README / 文档`，列出已经关联到这篇文献的文档。

面板之外也有同样的入口：

- `工具 -> 为选中文献导入 README`
- `工具 -> 研究助手设置`
- 文献右键菜单：`导入 README 并关联到这篇文献`

1.0.2 不再提供条目工具栏按钮，入口统一放在右侧导航栏，行为与其他 Zotero
面板插件一致。

### 与 Codex 对话

1. 选中一篇普通文献。
2. 在右侧条目信息栏打开 `AI 对话`。
3. 输入问题并按 `Enter`。

例如：

```text
这篇文献要解决什么问题，提出了什么方法？
总结实验设置和主要结果。
作者承认的局限有哪些，还有哪些问题没有解决？
```

一段对话中的第一条问题会附带文献上下文。后续问题通过
`codex exec resume` 发送到同一个 Codex 会话，因此 Codex 会记住你们之前
关于这篇文献讨论过的内容。

使用要点：

- 每篇文献各自拥有独立的对话和 Codex 会话。
- `新建对话` 会先确认，再清空当前对话，下一条提问开启新的会话。
- `停止` 会取消正在执行的请求。提问仍保留在列表中，方便查看问过什么。
- 对话记录和会话 ID 以 JSON 文件保存在 Zotero 数据目录下：

  ```text
  <Zotero 数据目录>/research-workbench/chats/<libraryID>-<条目 Key>.json
  ```

  如果数据目录不可写，会退回到 Zotero 配置目录或系统临时目录。
- 插件以只读沙箱运行 Codex，不会让 Codex 修改你的 Zotero 文件或项目文件。

### 导入 README 并关联文献

1. 在 Zotero 中选中一篇或多篇普通文献。
2. 从以下任意入口执行导入：
   - 条目信息栏：`AI 对话 -> 导入 README`
   - 文献右键菜单：`导入 README 并关联到这篇文献`
   - 主菜单：`工具 -> 为选中文献导入 README`
3. 输入以下任一格式：
   - `owner/repo`
   - `https://github.com/owner/repo`
   - `https://github.com/owner/repo/blob/main/README.md`
   - 可直接下载文本的 URL
   - `C:\projects\demo\README.md`
   - UNC 路径、`file://` URL，或 `~/...` 开头的路径

导入后的附件会自动带 `research-workbench:readme` 标签，便于后续检索。已关联
的 README 和说明文档会显示在聊天页面下方的文档列表中。

### 发送给 Codex 的内容

插件只在本机整理当前选中的材料，然后交给已登录的 Codex CLI。根据设置，材料
可能包括：

- 标题、作者、年份、出版物、DOI、URL、条目类型和摘要。
- Zotero 笔记。
- PDF 批注和批注评论。
- 从 PDF 提取的全文。
- 附件名称和内容类型。
- 已导入的 README 和说明文档。

一段对话的第一条消息会带上这些材料；后续消息只发送你的新问题，因为 Codex
会话已经保留了之前的上下文。

插件本身不调用 AI API，不保存 API Key，也不额外连接其他模型服务。认证和请求
由 Codex CLI 使用你的现有登录完成。处理敏感或未公开材料前，请结合自己的隐私
要求判断是否适合发送。

### 设置说明

打开 `编辑 -> 设置 -> 研究助手`，或点击聊天页面中的 `设置`。设置页支持：

- `Codex 可执行文件`
- `模型覆盖`
- `额外 CLI 参数`
- `超时时间（秒）`（60 到 3600，默认 600）
- PDF 全文、批注、笔记、附件清单、导入文档开关
- 总上下文字符上限
- 每份导入文档的字符上限

修改设置后会自动保存。`恢复默认设置` 会重置研究助手的全部偏好。

### 隐私说明

插件只读取你主动选中的 Zotero 条目。它在你的电脑上组装材料，并启动本机
Codex CLI。Codex 随后使用你已有的登录状态处理请求。插件不会建立额外的上传
连接，不会把文件发送到独立服务器，也不会保存 API Key。对话记录只保存在本机
Zotero 数据目录中，插件本身不会上传。

### 常见问题

#### 右侧栏没有 AI 对话入口

请确认安装的是 1.0.2。然后进入 `工具 -> 插件`，先禁用研究助手再重新启用，
并重启 Zotero。Zotero 只在插件加载时注册条目信息栏分区，更新后需要重新加载。

另外请确认当前选中的是普通文献条目。附件、笔记等非普通条目会禁用该分区。

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

#### 回复超时

提高 `超时时间`，减少一次选中的文献数量，或降低 `总上下文字符上限`。超时
限制针对单次回复，不是整段对话。

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
OCR。即使全文不可用，对话仍然可以使用元数据、笔记和批注。

#### 想清空某篇文献的全部对话

打开该文献的 `AI 对话` 面板，点击 `新建对话`。该条目对应的 JSON 文件会被
清空。想删除已导入的文档，按 Zotero 的常规方式删除带
`research-workbench:readme` 标签的附件即可。

### 构建 XPI

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

脚本会检查必要文件、读取 `zotero-plugin/manifest.json` 中的版本号，并输出：

```text
release/zotero-research-workbench-1.0.2.xpi
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
