research-workbench-section-header = 研究助手
research-workbench-section-sidenav =
    .tooltiptext = 研究助手

research-workbench-menu-tools-import = 为选中文献导入 README
research-workbench-menu-item-import = 导入 README 并关联到这篇文献

research-workbench-prefs-intro = AI 对话通过本机已安装并已登录的 Codex CLI 完成，不需要 API Key，也不会由插件另行请求模型服务。
research-workbench-prefs-codex-heading = Codex 连接
research-workbench-prefs-codex-help = 先安装 Codex CLI，在终端执行一次 codex login，然后点击下方“检测 Codex”。
research-workbench-prefs-codex-path = Codex 可执行文件
research-workbench-prefs-codex-path-placeholder =
    .placeholder = 自动检测
research-workbench-prefs-codex-path-help = 留空时会自动搜索 PATH 和常见安装目录，也可以填写完整路径或安装目录。
research-workbench-prefs-model = 模型覆盖
research-workbench-prefs-model-placeholder =
    .placeholder = 使用 Codex 当前配置的模型
research-workbench-prefs-model-help = 可选。留空时使用 Codex 配置文件中的默认模型。
research-workbench-prefs-extra-args = 额外 CLI 参数
research-workbench-prefs-extra-args-placeholder =
    .placeholder = 例如：-c model_reasoning_effort="high"
research-workbench-prefs-extra-args-help = 高级选项，参数会插入到每次 Codex 对话请求中。
research-workbench-prefs-timeout = 超时时间（秒）
research-workbench-prefs-timeout-help = 适用于一次对话回复或连接检测，范围限制为 60 到 3600 秒。
research-workbench-prefs-test-button = 检测 Codex
research-workbench-prefs-reset-button = 恢复默认设置

research-workbench-prefs-chat-heading = AI 对话
research-workbench-prefs-chat-help = 每篇文献保留自己的多轮 Codex 会话。第一条问题会附带上下文材料，后续问题继续同一个会话。

research-workbench-prefs-context-heading = 发送给 Codex 的材料
research-workbench-prefs-include-pdf = PDF 全文
research-workbench-prefs-include-annotations = PDF 批注
research-workbench-prefs-include-notes = Zotero 笔记
research-workbench-prefs-include-attachments = 附件清单
research-workbench-prefs-include-imported = 已导入的 README 和说明文档
research-workbench-prefs-max-context = 总上下文字符上限
research-workbench-prefs-max-context-help = 数值越大，可用原文越多，但会消耗更多订阅额度并增加等待时间。
research-workbench-prefs-per-doc = 每份导入文档的字符上限
research-workbench-prefs-per-doc-help = 限制每份 README 或文本附件进入 AI 上下文的内容量，附件本身仍会完整保存在 Zotero 中。

research-workbench-prefs-privacy = 所选 Zotero 元数据和文档只在本机整理，并交给已登录的 Codex CLI；对话记录保存在本机 Zotero 数据目录中。
