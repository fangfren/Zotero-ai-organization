# Zotero Research Workbench / 研究助手

[English](#english) | [简体中文](#简体中文)

Research Workbench is a standalone Zotero plugin. It adds **one** entry to the
right item-pane sidenav, called `Research Workbench`. Clicking it opens an
embedded workbench page inside the right pane where you can switch between
four parts: annotations and notes, tag management, AI chat, and linked README
reading.

研究助手是一个独立的 Zotero 插件。它只在条目信息栏右侧导航栏增加**一个**入口，
名称为 `研究助手`。点击后在右侧栏内嵌打开工作台页面，可在四部分内容之间切换：
注释笔记、标签管理、AI 对话、关联 README 阅读。

The AI part talks to the Codex CLI that is already installed and signed in on
your computer. It does **not** require an API key, a Python installation, a
local web server, or an extra model service.

AI 部分调用电脑上已经安装并登录的 Codex CLI，**不需要 API Key、不需要安装
Python、不需要本地服务器，也不需要额外配置模型服务**。

Version 1.0.3 keeps the report generator removed, adds note and tag management,
adds a README reader inside the pane, and reduces the plugin to a single
right-side entry.

1.0.3 延续移除 AI 报告的改动，新增笔记管理与标签管理，新增面板内的 README
阅读器，并把插件收敛为右侧栏单一入口。

---

## English

### What You Get

- One entry in the right item-pane sidenav, `Research Workbench`, next to
  Zotero's own pane sections. There is no toolbar button and no settings entry
  in the item or PDF right-click menu.
- An embedded workbench page inside the right pane with four switchable parts:
  1. `Annotations & notes` - Zotero notes and PDF annotations of the item.
  2. `Tag manager` - add and remove tags, with library-wide suggestions.
  3. `AI chat` - multi-turn chat with the local Codex CLI.
  4. `README` - read linked README or documentation attachments inside the
     pane and import new ones.
- Per-item multi-turn chat. The first question carries the item context;
  later questions continue the same Codex session.
- Chat history and Codex session IDs persisted locally, so a conversation
  survives switching items and restarting Zotero.
- README import from `owner/repo`, a GitHub repository URL, a GitHub file URL,
  a direct Markdown or text URL, or a local file path.
- Automatic attachment linking:
  - One selected item: the README is added as a child attachment.
  - Multiple selected items: the README is added once as a standalone
    attachment and connected through Zotero related items.
- A native Zotero preferences pane with a built-in Codex connection test.
- English and Simplified Chinese localization.

Report generation, report templates, report notes, and report tags are gone.
The plugin does not write AI reports into your notes.

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
   release/zotero-research-workbench-1.0.3.xpi
   ```

   Download it from the repository
   [release folder](https://github.com/fangfren/Zotero-ai-organization/tree/main/release),
   or build it locally with the command in "Build the XPI" below.

2. Open Zotero.
3. Go to `Tools -> Add-ons`.
4. Click the gear button and choose `Install Add-on From File...`.
5. Select `zotero-research-workbench-1.0.3.xpi`.
6. Confirm the installation and restart Zotero if requested.

The XPI contains only the plugin. No Python installation, local server, or
extra runtime is required. The plugin is published with an `update_url`, so
future versions installed from this repository can be updated from Zotero's
add-on manager.

If you already have an older version installed, install 1.0.3 over it and
restart Zotero. The old toolbar button, the settings menu entries, and the
three-tab layout disappear, and the single right-pane entry appears.

### Where the Workbench Lives

After the plugin is enabled, select a regular literature item and look at the
right side of the Zotero window. In the vertical navigation strip at the right
edge of the item pane there is a `Research Workbench` icon. Click it to switch
the item pane to the workbench page.

The page has a row of four tabs at the top. The AI chat is selected first;
click any tab to switch parts. The page stays inside the item pane, so you can
keep using Zotero normally.

### Part 1: Annotations & Notes

The first tab has two blocks.

`Notes` lists the child notes of the selected item. You can:

- Create a note: type a title, then use the new-note button. The note is saved
  as a child note of the item and appears in Zotero's own notes list.
- Open a note: click a note title to open it in the Zotero note editor.
- Delete a note: use the delete button next to the note.

`PDF annotations` lists the annotations of the item's PDF attachments,
including the type (highlight, underline, note, and so on), the page number,
the color, and the annotation comment. Click an annotation to jump to it in
the Zotero PDF reader.

Both notes and annotations are also part of the material sent to Codex in the
AI chat.

### Part 2: Tag Manager

The second tab lists the tags of the selected item as chips. You can:

- Type a tag name and press `Enter` or the add button to add it. The input
  suggests tags that already exist in your library.
- Remove a tag with the `x` button on the chip. Changes are saved to Zotero
  immediately.

Adding a tag that already exists reports it instead of creating a duplicate.

### Part 3: AI Chat

1. Select a regular literature item.
2. Open the `AI chat` tab in the workbench.
3. Type a question and press `Enter`, or click `Send`.

For example:

```text
What problem does this paper solve, and what method does it propose?
Summarize the experiment setup and the main results.
What are the limitations the authors admit, and what is left open?
```

Useful behavior:

- Each literature item has its own conversation and its own Codex session.
- `New chat` clears the current conversation after a confirmation prompt and
  starts a fresh session on the next question.
- `Send` turns into `Stop` while a request is running, and stops the request.
  The question stays in the list so you can see what was asked.
- `Settings` opens the Research Workbench preference pane.
- Chat history and session IDs are stored as JSON files under your Zotero data
  directory:

  ```text
  <Zotero data directory>/research-workbench/chats/<libraryID>-<itemKey>.json
  ```

  The fallback locations are the Zotero profile directory and the system temp
  directory if the data directory is not writable.
- The plugin runs Codex in a read-only sandbox. It never lets Codex modify your
  Zotero files or your project files.

### Part 4: README

The fourth tab shows the README and documentation attachments already linked
to the item.

- Pick a document on the left; it is rendered on the right. Markdown headings,
  lists, code, links, and tables are shown in a readable form.
- `Import README` imports a new document and links it to the current item.
- `Refresh` re-reads the list of linked documents.
- Very long documents are truncated for display, and the page says so.

Supported import inputs:

- `owner/repo`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/blob/main/README.md`
- A direct `raw.githubusercontent.com` or other direct text URL
- A local path such as `C:\projects\demo\README.md`
- A UNC path, `file://` URL, or a path beginning with `~/`

The imported attachment receives the tag `research-workbench:readme`, which
makes it easy to find later.

### Import a README Outside the Pane

Two menus remain, and both only import README files:

- Main menu: `Tools -> Import README for Selected Items`
- Item right-click menu: `Import README and Link to This Item`

The toolbar button and the `Research Workbench Settings` menu entries were
removed in 1.0.3. Settings are still available from `Edit -> Settings ->
Research Workbench` and from the `Settings` button in the chat tab.

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
tab. The preference pane supports:

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

The Codex settings page also offers `Detect Codex`, which reports the detected
path, the version, and performs a real `codex exec` call using your current
login.

The plugin searches `PATH` and common Codex install locations. On Windows this
includes the versioned folders under:

```text
%LOCALAPPDATA%\OpenAI\Codex\bin
%APPDATA%\npm
%USERPROFILE%\.codex\bin
```

### Privacy

The plugin reads only the Zotero items you select. It assembles the source
material on your computer and starts the local Codex CLI. The CLI then uses
your existing Codex login to perform the request. The plugin does not create
any additional network connection, does not upload files to a separate
server, and does not store an API key. Chat history is stored locally in your
Zotero data directory and is never uploaded by the plugin itself.

### Troubleshooting

#### The Research Workbench entry is missing from the right pane

Make sure the installed XPI is 1.0.3. Then disable and re-enable Research
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

#### The README tab says no document is linked

Use `Import README` in the README tab, `Tools -> Import README for Selected
Items`, or the item right-click menu. The tab only lists attachments tagged
`research-workbench:readme` or text documents attached to the item.

#### I want to clear everything for one item

Open that item's `AI chat` tab and click `New chat`. The stored JSON file for
that item is cleared. To remove imported documents, delete the
`research-workbench:readme` attachment in Zotero as usual.

### Build the XPI

From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

The script validates the required files, reads the version from
`zotero-plugin/manifest.json`, and writes:

```text
release/zotero-research-workbench-1.0.3.xpi
```

The XPI root contains `manifest.json`, `bootstrap.js`, `prefs.js`, `content/`,
and `locale/`.

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

- 只在条目信息栏右侧导航栏增加**一个**入口 `研究助手`，和其他 Zotero 面板
  入口放在一起。不再有工具栏按钮，条目和 PDF 右键菜单里也没有设置入口。
- 点击后在右侧栏内嵌打开工作台页面，页面顶部有四个可切换的部分：
  1. `注释笔记` —— 这篇文献的 Zotero 笔记和 PDF 注释。
  2. `标签管理` —— 增删标签，并给出全库标签联想。
  3. `AI 对话` —— 与本地 Codex CLI 多轮对话。
  4. `关联 README` —— 在面板内阅读已关联的 README 或说明文档，并导入新的
     文档。
- 每篇文献独立的多轮对话：第一条问题携带文献上下文，后续问题继续同一个
  Codex 会话。
- 对话记录和 Codex 会话 ID 保存在本机，切换文献或重启 Zotero 后仍可继续。
- 支持从以下来源导入 README：`owner/repo`、GitHub 仓库链接、GitHub 文件
  链接、直接的 Markdown 或文本链接、本地文件路径。
- 自动建立文献关联：
  - 只选中一条文献时，README 作为该文献的子附件。
  - 选中多条文献时，README 作为独立附件导入，并通过 Zotero
    `相关条目` 与这些文献关联。
- 提供原生 Zotero 设置页和一键 Codex 连接检测。
- 提供英语和简体中文本地化。

报告生成、报告模板、报告笔记和报告标签已经移除，插件不会把 AI 报告写进
你的笔记。

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
   release/zotero-research-workbench-1.0.3.xpi
   ```

   可以直接从仓库的
   [release 目录](https://github.com/fangfren/Zotero-ai-organization/tree/main/release)
   下载，也可以按下方“构建 XPI”一节在本地自行构建。

2. 打开 Zotero。
3. 进入 `工具 -> 插件`。
4. 点击右上角齿轮，选择 `从文件安装插件...`。
5. 选择 `zotero-research-workbench-1.0.3.xpi`。
6. 确认安装。如果 Zotero 提示重启，请重启后再使用。

这个 XPI 只包含插件本体，不需要 Python、不需要本地服务器，也不需要其他运行时。
插件内置了 `update_url`，从本仓库安装后可以直接在 Zotero 插件管理器中检查更新。

如果之前装过旧版本，直接用 1.0.3 覆盖安装并重启 Zotero。旧的工具栏按钮、
设置菜单和旧的三标签布局会消失，新的右侧单一入口会出现。

### 工作台入口在哪里

插件启用后，选中一篇普通文献，然后看 Zotero 窗口右侧。在条目信息栏最右侧
的竖排导航栏中会出现 `研究助手` 图标，点击后条目信息栏会切换到工作台页面。

页面顶部是一排四个标签，默认停在 `AI 对话`。点击任意标签即可切换部分，
整个页面都嵌在右侧栏内，不影响你继续使用 Zotero。

### 第一部分：注释笔记

这个部分包含两块内容。

`笔记` 列出这篇文献的子笔记，可以：

- 新建笔记：输入标题后点击新建按钮。笔记会作为该文献的子笔记保存，并出现在
  Zotero 自己的笔记列表中。
- 打开笔记：点击笔记标题，会在 Zotero 笔记编辑器中打开。
- 删除笔记：点击笔记右侧的删除按钮。

`PDF 注释` 列出这篇文献 PDF 附件中的注释，包含类型（高亮、下划线、注释等）、
页码、颜色和注释评论。点击某条注释会跳转到 Zotero PDF 阅读器中的对应位置。

笔记和注释同样会作为材料的一部分发送给 Codex。

### 第二部分：标签管理

这个部分以标签块的形式列出当前文献的标签，可以：

- 输入标签名后按 `Enter` 或点击添加按钮，输入框会联想库中已有的标签。
- 点击标签块上的 `x` 按钮删除标签。修改会立即保存到 Zotero。

如果添加的标签已经存在，会给出提示，不会产生重复标签。

### 第三部分：AI 对话

1. 选中一篇普通文献。
2. 在工作台打开 `AI 对话`。
3. 输入问题并按 `Enter`，或点击 `发送`。

例如：

```text
这篇文献要解决什么问题，提出了什么方法？
总结实验设置和主要结果。
作者承认的局限有哪些，还有哪些问题没有解决？
```

使用要点：

- 每篇文献各自拥有独立的对话和 Codex 会话。
- `新建对话` 会先确认，再清空当前对话，下一条提问开启新的会话。
- 请求执行期间 `发送` 会变成 `停止`，点击可以取消请求。提问仍保留在列表中，
  方便查看问过什么。
- `设置` 会打开研究助手的设置页。
- 对话记录和会话 ID 以 JSON 文件保存在 Zotero 数据目录下：

  ```text
  <Zotero 数据目录>/research-workbench/chats/<libraryID>-<条目 Key>.json
  ```

  如果数据目录不可写，会退回到 Zotero 配置目录或系统临时目录。
- 插件以只读沙箱运行 Codex，不会让 Codex 修改你的 Zotero 文件或项目文件。

### 第四部分：关联 README

这个部分显示已经关联到当前文献的 README 和说明文档。

- 在左侧选择一份文档，右侧会渲染它的内容，支持 Markdown 标题、列表、代码、
  链接和表格。
- `导入 README` 可以为当前文献导入新文档并建立关联。
- `刷新` 会重新读取已关联的文档列表。
- 文档过长时会截断显示，并在页面上给出提示。

支持的导入格式：

- `owner/repo`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/blob/main/README.md`
- 可直接下载文本的 URL
- `C:\projects\demo\README.md`
- UNC 路径、`file://` URL，或 `~/...` 开头的路径

导入后的附件会自动带 `research-workbench:readme` 标签，便于后续检索。

### 面板之外的 README 入口

插件只保留两个菜单入口，且都只用于导入 README：

- 主菜单：`工具 -> 为选中文献导入 README`
- 文献右键菜单：`导入 README 并关联到这篇文献`

1.0.3 已移除工具栏按钮和 `研究助手设置` 菜单入口。设置仍然可以从
`编辑 -> 设置 -> 研究助手`，或对话页面的 `设置` 按钮进入。

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

打开 `编辑 -> 设置 -> 研究助手`，或点击对话部分的 `设置`。设置页支持：

- `Codex 可执行文件`
- `模型覆盖`
- `额外 CLI 参数`
- `超时时间（秒）`（60 到 3600，默认 600）
- PDF 全文、批注、笔记、附件清单、导入文档开关
- 总上下文字符上限
- 每份导入文档的字符上限

修改设置后会自动保存。`恢复默认设置` 会重置研究助手的全部偏好。

设置页还提供 `检测 Codex`：会显示检测到的路径和版本，并真正调用一次
`codex exec`，用来确认订阅登录可用。

插件会自动搜索 `PATH` 和常见安装目录。在 Windows 上会检查：

```text
%LOCALAPPDATA%\OpenAI\Codex\bin
%APPDATA%\npm
%USERPROFILE%\.codex\bin
```

### 隐私说明

插件只读取你主动选中的 Zotero 条目。它在你的电脑上组装材料，并启动本机
Codex CLI。Codex 随后使用你已有的登录状态处理请求。插件不会建立额外的上传
连接，不会把文件发送到独立服务器，也不会保存 API Key。对话记录只保存在本机
Zotero 数据目录中，插件本身不会上传。

### 常见问题

#### 右侧栏没有研究助手入口

请确认安装的是 1.0.3。然后进入 `工具 -> 插件`，先禁用研究助手再重新启用，
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

#### README 部分提示没有关联文档

可以使用 README 部分的 `导入 README`、`工具 -> 为选中文献导入 README`，
或文献右键菜单导入。这个部分只列出带 `research-workbench:readme` 标签的
附件，以及挂在条目下的文本文档。

#### 想清空某篇文献的全部对话

打开该文献的 `AI 对话` 部分，点击 `新建对话`。该条目对应的 JSON 文件会被
清空。想删除已导入的文档，按 Zotero 的常规方式删除带
`research-workbench:readme` 标签的附件即可。

### 构建 XPI

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

脚本会检查必要文件、读取 `zotero-plugin/manifest.json` 中的版本号，并输出：

```text
release/zotero-research-workbench-1.0.3.xpi
```

XPI 根目录直接包含 `manifest.json`、`bootstrap.js`、`prefs.js`、`content/`
和 `locale/`。

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
