# Zotero Research Workbench / 研究助手

[English](#english) | [简体中文](#简体中文)

**Version 1.0.0 - first public release.**

Research Workbench is a standalone Zotero plugin. It adds **one** entry to the
right item-pane sidenav, called `Research Workbench`. Clicking it opens an
embedded workbench page inside the right pane where you can switch between
four parts: annotations and notes, tag management, AI chat, and linked README
reading.

`1.0.0` 是研究助手的第一个公开版本。它是一个独立的 Zotero 插件，只在条目信息栏
右侧导航栏增加**一个**入口，名称为 `研究助手`。点击后在右侧栏内嵌打开工作台
页面，可在四部分内容之间切换：注释笔记、标签管理、AI 对话、关联 README 阅读。

The AI part talks to the Codex CLI that is already installed and signed in on
your computer. It does **not** require an API key, a Python installation, a
local web server, or an extra model service.

AI 部分调用电脑上已经安装并登录的 Codex CLI，**不需要 API Key、不需要安装
Python、不需要本地服务器，也不需要额外配置模型服务**。

---

## English

### What You Get

- One entry in the right item-pane sidenav, `Research Workbench`, next to
  Zotero's own pane sections. There is no toolbar button and no settings entry
  in the item or PDF right-click menu.
- The entry is enabled for regular literature items, for PDF attachments under
  a literature item, and for standalone PDFs that were imported on their own.
- An embedded workbench page inside the right pane with four switchable parts:
  1. `Annotations & notes` - Zotero notes and PDF annotations of the item,
     listed as attachment-style rows.
  2. `Tag manager` - add and remove tags, with library-wide suggestions.
  3. `AI chat` - multi-turn chat with the local Codex CLI.
  4. `README` - read linked README or documentation attachments inside the
     pane, open or remove them, and import new ones. Each document is shown as
     an attachment-style row.
- Per-item multi-turn chat. The first question carries the item context; later
  questions continue the same Codex session.
- Chat history and Codex session IDs stored locally, so a conversation
  survives switching items and restarting Zotero.
- README import from `owner/repo`, a GitHub repository URL, a GitHub file URL,
  a direct Markdown or text URL, or a local file path.
- Automatic attachment linking:
  - One selected literature item: the README is added as a child attachment.
  - A standalone PDF, or multiple selected items: the README is added once as
    a standalone attachment and connected through Zotero related items.
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

### Install

1. Download the release file:

   ```text
   release/zotero-research-workbench-1.0.0.xpi
   ```

   Download it from the repository
   [release folder](https://github.com/fangfren/Zotero-ai-organization/tree/main/release),
   from the GitHub Releases page, or build it locally with the command in
   "Build the XPI" below.

2. Open Zotero.
3. Go to `Tools -> Add-ons`.
4. Click the gear button and choose `Install Add-on From File...`.
5. Select `zotero-research-workbench-1.0.0.xpi`.
6. Confirm the installation and restart Zotero if requested.

The XPI contains only the plugin. No Python installation, local server, or
extra runtime is required. The plugin is published with an `update_url`, so
future versions installed from this repository can be updated from Zotero's
add-on manager.

### Where the Workbench Lives

After the plugin is enabled, select a literature item, a PDF attachment under a
literature item, or a standalone PDF, and look at the right side of the Zotero
window. In the vertical navigation strip at the right edge of the item pane
there is a `Research Workbench` icon. Click it to switch the item pane to the
workbench page.

Selecting a child or standalone PDF resolves the workbench to that PDF: its
annotations and full text are used directly, and a child PDF also shows the
notes, tags, and metadata of its parent literature item.

The page has a row of four tabs at the top. The AI chat is selected first;
click any tab to switch parts. The page stays inside the item pane, so you can
keep using Zotero normally.

### Part 1: Annotations & Notes

The first tab has two blocks. Both render as attachment-style rows with a type
badge, title, metadata line, a short preview, and action buttons.

`Notes` lists the notes of the selected item. You can:

- Create a note: type a title, then use the new-note button. The note is saved
  as a child note of the item and appears in Zotero's own notes list.
- Open a note: click a note title to open it in the Zotero note editor.
- Delete a note: use the delete button next to the note.
- `Refresh` re-reads the note and annotation lists.

When the workbench was opened from a standalone PDF, new notes are saved as
standalone Zotero notes and related to that PDF, because Zotero only allows
notes to be children of literature items.

`PDF annotations` lists the annotations of the item's PDF attachments,
including the type (highlight, underline, note, and so on), the page number,
the color, and the annotation comment. Each annotation is an attachment-style
row; use `Open in PDF` to jump to it in the Zotero PDF reader.

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

1. Select a literature item, a PDF attachment under a literature item, or a
   standalone PDF.
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
- Child and standalone PDFs reuse the conversation of the item they resolve
  to, so switching between a literature item and its PDF keeps one thread.
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
to the item as attachment-style rows.

- Click a row, or use `Read`, to render that document on the right. Markdown
  headings, lists, code, links, and tables are shown in a readable form.
- `Open` selects the attachment in Zotero so you can open it with your system
  application.
- `Remove` moves the attachment to the Zotero trash after a confirmation.
- `Import README` imports a new document and links it to the current item.
- `Refresh` re-reads the list of linked documents.
- Very long documents are truncated for display, and the page says so.

Rows show a type badge (`PDF`, `MD`, `TXT`, ...) and the date the attachment
was added, so imported README files are easy to tell apart from the PDFs of a
literature item.

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

Two menus also import README files, and both only import README files:

- Main menu: `Tools -> Import README for Selected Items`
- Item right-click menu: `Import README and Link to This Item`

The plugin settings stay in `Edit -> Settings -> Research Workbench`, and in
the `Settings` button of the chat tab.

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

Make sure the installed XPI is 1.0.0. Then disable and re-enable Research
Workbench in `Tools -> Add-ons`, and restart Zotero. Zotero registers item-pane
sections only while the plugin is loading, so an update needs a reload.

Also check that you have selected a literature item or a PDF attachment. The
section is enabled for regular items and file attachments, and disabled for
notes and other item types.

#### I installed an older development build before

Development builds 1.0.1 to 1.0.4 were never released here. If you installed
one of them from an earlier commit, remove it in `Tools -> Add-ons` first, then
install 1.0.0 and restart Zotero.

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
release/zotero-research-workbench-1.0.0.xpi
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

### Release Notes

`1.0.0` - the first public release.

- One right-pane entry that opens an embedded four-part workbench.
- Notes, PDF annotations, and linked README files are listed as
  attachment-style rows with a badge, metadata, preview, and row actions.
- Tag management, multi-turn Codex chat, README import, and README reading all
  live in the same pane.
- No toolbar button, no right-click settings entry, and no API key.

### License

MIT. See `LICENSE`.

---

## 简体中文

### 功能概览

- 只在条目信息栏右侧导航栏增加**一个**入口 `研究助手`，和其他 Zotero 面板
  入口放在一起。没有工具栏按钮，条目和 PDF 右键菜单里也没有设置入口。
- 普通文献条目、文献下的 PDF 附件、以及单独导入的 PDF 都能看到这个入口。
- 点击后在右侧栏内嵌打开工作台页面，页面顶部有四个可切换的部分：
  1. `注释笔记` —— 这篇文献的 Zotero 笔记和 PDF 注释，以附件列表形式展示。
  2. `标签管理` —— 增删标签，并给出全库标签联想。
  3. `AI 对话` —— 与本地 Codex CLI 多轮对话。
  4. `关联 README` —— 在面板内阅读已关联的 README 或说明文档，并导入新的
     文档；每份文档以附件列表形式展示。
- 每篇文献独立的多轮对话：第一条问题携带文献上下文，后续问题继续同一个
  Codex 会话。
- 对话记录和 Codex 会话 ID 保存在本机，切换文献或重启 Zotero 后仍可继续。
- 支持从以下来源导入 README：`owner/repo`、GitHub 仓库链接、GitHub 文件
  链接、直接的 Markdown 或文本链接、本地文件路径。
- 自动建立文献关联：
  - 只选中一条文献时，README 作为该文献的子附件。
  - 选中单独 PDF 或多条文献时，README 作为独立附件导入，并通过 Zotero
    `相关条目` 与这些条目关联。
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

### 安装

1. 下载发布文件：

   ```text
   release/zotero-research-workbench-1.0.0.xpi
   ```

   可以从仓库的 [release 目录](https://github.com/fangfren/Zotero-ai-organization/tree/main/release)、
   GitHub Releases 页面下载，也可以按下面「构建 XPI」一节自行构建。

2. 打开 Zotero。
3. 进入 `工具 -> 插件`。
4. 点击齿轮按钮，选择 `从文件安装插件…`。
5. 选择 `zotero-research-workbench-1.0.0.xpi`。
6. 确认安装，如有提示则重启 Zotero。

这个 XPI 只包含插件本体，不需要 Python、不需要本地服务器，也不需要其他运行
组件。插件清单里写有 `update_url`，以后从本仓库安装的版本可以直接在 Zotero
的插件管理器中更新。

### 工作台在这里

插件启用后，选中一条文献、文献下的 PDF 附件、或者单独导入的 PDF，看向
Zotero 窗口右侧：在条目面板最右边的竖排导航条里会出现 `研究助手` 图标。
点击它，条目面板就会切换到工作台页面。

选中文献下的 PDF 或单独的 PDF 时，工作台会解析到这篇 PDF：直接使用它的注释
和全文；如果是文献下的 PDF，还会同时显示父级文献的笔记、标签和元数据。

页面顶部是一排四个标签页，默认先打开 `AI 对话`，点击任意标签即可切换。整个
页面都嵌在条目面板里，不影响 Zotero 的其他操作。

### 第 1 部分：注释笔记

第一个标签页包含两块内容，都以附件列表形式展示，每一行有类型徽标、标题、
元信息、简短预览和操作按钮。

`笔记` 列出当前条目的笔记，可以：

- 新建笔记：输入标题后点击新建按钮。笔记会保存为该条目的子笔记，并出现在
  Zotero 自己的笔记列表里。
- 打开笔记：点击笔记标题，在 Zotero 笔记编辑器中打开。
- 删除笔记：点击该行右侧的删除按钮。
- `刷新` 重新读取笔记和注释列表。

如果工作台是从单独 PDF 打开的，新建的笔记会保存为独立的 Zotero 笔记并与
该 PDF 建立关联，因为 Zotero 只允许文献条目拥有子笔记。

`PDF 注释` 列出该条目 PDF 附件中的注释，包括类型（高亮、下划线、便签等）、
页码、颜色和注释内容。每条注释都是一行附件式条目，点击 `在 PDF 中打开`
可以跳转到 Zotero PDF 阅读器中的对应位置。

笔记和注释同样会作为 AI 对话的上下文发送给 Codex。

### 第 2 部分：标签管理

第二个标签页以标签块的形式列出当前条目的标签，可以：

- 输入标签名后按 `回车` 或点击添加按钮，输入框会联想本库已有的标签。
- 点击标签块上的 `x` 删除标签。修改会立即保存到 Zotero。

添加已存在的标签时会给出提示，不会重复添加。

### 第 3 部分：AI 对话

1. 选中一条文献、文献下的 PDF 附件、或单独导入的 PDF。
2. 在工作台里打开 `AI 对话` 标签页。
3. 输入问题后按 `回车`，或点击 `发送`。

例如：

```text
这篇论文要解决什么问题，提出了什么方法？
总结实验设置和主要结果。
作者承认了哪些局限，还有哪些问题没有解决？
```

具体行为：

- 每篇文献有独立的对话和独立的 Codex 会话。
- 文献下的 PDF 和单独 PDF 会复用它们解析到的条目的对话，所以文献与其 PDF
  之间切换时仍然是同一段对话。
- `新建对话` 会在确认后清空当前对话，下一次提问时开启新的会话。
- 请求进行中 `发送` 会变成 `停止`，可以中断本次请求；已经提出的问题仍保留
  在列表里。
- `设置` 打开研究助手的设置页。
- 对话记录与会话 ID 以 JSON 文件保存在 Zotero 数据目录下：

  ```text
  <Zotero 数据目录>/research-workbench/chats/<libraryID>-<itemKey>.json
  ```

  如果数据目录不可写，会依次回退到 Zotero 配置目录和系统临时目录。
- 插件以只读沙箱运行 Codex，不会让 Codex 修改你的 Zotero 数据或项目文件。

### 第 4 部分：关联 README

第四个标签页以附件列表形式展示已经关联到该条目的 README 和说明文档。

- 点击某一行或 `阅读`，在右侧渲染该文档：Markdown 标题、列表、代码、链接、
  表格都会以可读形式呈现。
- `打开` 在 Zotero 中选中该附件，便于用系统程序打开。
- `删除` 在确认后把附件移入 Zotero 回收站。
- `导入 README` 导入新文档并关联到当前条目。
- `刷新` 重新读取已关联文档列表。
- 过长的文档会截断显示，并在页面上注明。

每行都会显示类型徽标（`PDF`、`MD`、`TXT` 等）和附件加入日期，方便区分导入
的 README 与文献自带的 PDF。

支持的导入来源：

- `owner/repo`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/blob/main/README.md`
- 直接的 `raw.githubusercontent.com` 或其他文本链接
- 本地路径，例如 `C:\projects\demo\README.md`
- UNC 路径、`file://` 链接，或以 `~/` 开头的路径

导入的附件会带上标签 `research-workbench:readme`，便于以后检索。

### 在面板外导入 README

另外还有两个菜单入口，它们同样只做导入 README 这一件事：

- 主菜单：`工具 -> 为选中条目导入 README`
- 条目右键菜单：`导入 README 并关联到这篇文献`

插件设置仍然可以从 `编辑 -> 设置 -> 研究助手` 打开，也可以点击对话标签页里的
`设置` 按钮。

### 发送给 Codex 的内容

插件在本机组装选中条目的材料，然后交给已登录的 Codex CLI。根据设置，内容
可能包括：

- 标题、作者、年份、出版物、DOI、URL、条目类型和摘要。
- Zotero 笔记。
- PDF 注释和批注内容。
- 提取出的 PDF 全文。
- 附件名称与内容类型。
- 导入的 README 与说明文档。

一段对话只有第一条消息包含这些材料；后续消息只发送你的新问题，因为 Codex
会话已经保存了之前的上下文。

插件本身不调用任何 AI API，也不保存 API Key，认证与请求都由 Codex 完成。
发送敏感或未公开材料前，请结合自己的隐私要求判断。

### 设置

从 `编辑 -> 设置 -> 研究助手` 打开，或点击对话标签页里的 `设置` 按钮。设置页
支持：

- `Codex 可执行文件`
- `模型覆盖`
- `额外命令行参数`
- `超时时间（秒）`（60-3600，默认 600）
- PDF 全文、注释、笔记、附件列表、导入文档等上下文开关
- 上下文总字符上限
- 单个导入文档的字符上限

设置修改后立即保存。`恢复默认值` 会重置研究助手的全部偏好设置。

设置页还提供 `检测 Codex`，会显示检测到的路径、版本，并用当前登录实际执行
一次 `codex exec`。

插件会搜索 `PATH` 和常见的 Codex 安装位置。在 Windows 上包括这些目录下的
版本化文件夹：

```text
%LOCALAPPDATA%\OpenAI\Codex\bin
%APPDATA%\npm
%USERPROFILE%\.codex\bin
```

### 隐私

插件只读取你选中的 Zotero 条目，材料都在本机组装，然后启动本地 Codex CLI；
后续请求由 CLI 使用你已有的 Codex 登录完成。插件不会额外建立网络连接，不会
把文件上传到独立服务器，也不会保存 API Key。对话记录只保存在本机 Zotero
数据目录中，插件本身不会上传。

### 常见问题

#### 右侧栏里找不到研究助手入口

请确认安装的是 1.0.0。然后进入 `工具 -> 插件`，先禁用研究助手再重新启用，
并重启 Zotero —— Zotero 只在插件加载时注册条目面板分区，更新后需要重新加载。

同时确认当前选中的是文献条目或 PDF 附件：该分区对普通条目和文件附件启用，
对笔记等其他条目类型不启用。

#### 之前装过旧的开发版本

1.0.1 到 1.0.4 都只是仓库里的开发提交，从未发布。如果你从早前的提交安装过
其中之一，请先在 `工具 -> 插件` 里移除，再安装 1.0.0 并重启 Zotero。

#### 找不到 Codex

打开研究助手设置，填写可执行文件的完整路径。Windows 上常见路径形如：

```text
C:\Users\<用户名>\AppData\Local\OpenAI\Codex\bin\<版本>\codex.exe
```

修改路径后点击 `检测 Codex`。

#### 找到 Codex 但没有登录

在终端执行：

```powershell
codex login status
```

如果显示未登录，执行 `codex login` 并完成浏览器流程。插件与终端使用同一个
Codex 配置目录和登录状态。

#### 回复超时

在设置里调大 `超时时间`，减少选中条目数量，或调低 `上下文总字符上限`。超时
只作用于单次回复，不影响整段对话。

#### GitHub 链接返回的是 HTML 而不是 Markdown

改用仓库链接、`blob` 链接，或直接的 raw Markdown 链接。插件会自动尝试常见的
README 文件名和分支名。

#### 本地路径无法识别

请使用绝对路径，支持包含空格的路径。也可以使用这种格式：

```text
file:///C:/projects/demo/README.md
```

#### PDF 全文是空的

请在 Zotero 中打开该 PDF，确认 Zotero 已经为其建立全文索引。扫描版 PDF 需要
先做 OCR。此时对话仍然可以使用元数据、笔记和注释。

#### README 标签页提示没有关联文档

请使用 README 标签页里的 `导入 README`、`工具 -> 为选中条目导入 README`，或
条目右键菜单导入。该标签页只列出带有 `research-workbench:readme` 标签的附件
以及条目下的文本文档。

#### 想清空某条条目的全部内容

打开该条目的 `AI 对话` 标签页，点击 `新建对话` 即可清空对应的 JSON 文件。
要移除导入的文档，像平常一样在 Zotero 中删除带
`research-workbench:readme` 标签的附件。

### 构建 XPI

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-xpi.ps1
```

脚本会检查必要文件、读取 `zotero-plugin/manifest.json` 中的版本号，并输出：

```text
release/zotero-research-workbench-1.0.0.xpi
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

### 版本说明

`1.0.0` —— 第一个公开版本。

- 一个右侧栏入口，点开即是内嵌的四部分工作台。
- 笔记、PDF 注释和关联 README 都以附件列表形式展示，带类型徽标、元信息、
  预览和行内操作。
- 标签管理、多轮 Codex 对话、README 导入与阅读都在同一个面板里完成。
- 没有工具栏按钮，没有右键设置入口，也不需要 API Key。

### 许可证

MIT，详见 `LICENSE`。
