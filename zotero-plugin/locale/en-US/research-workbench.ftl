research-workbench-section-header = Research Workbench
research-workbench-section-sidenav =
    .tooltiptext = Research Workbench

research-workbench-menu-tools-import = Import README for Selected Items
research-workbench-menu-item-import = Import README and Link to This Item

research-workbench-prefs-intro = AI chat uses the Codex CLI already installed and signed in on this computer. The plugin does not require an API key and does not send a separate request to a model provider.
research-workbench-prefs-codex-heading = Codex connection
research-workbench-prefs-codex-help = Install Codex CLI, run "codex login" once, then use Detect Codex below.
research-workbench-prefs-codex-path = Codex executable
research-workbench-prefs-codex-path-placeholder =
    .placeholder = Auto-detect
research-workbench-prefs-codex-path-help = Leave blank to search PATH and common install folders automatically. A full path or install directory is also accepted.
research-workbench-prefs-model = Model override
research-workbench-prefs-model-placeholder =
    .placeholder = Use the model configured by Codex
research-workbench-prefs-model-help = Optional. Leave blank to use the default model from your Codex configuration.
research-workbench-prefs-extra-args = Extra CLI arguments
research-workbench-prefs-extra-args-placeholder =
    .placeholder = Example: -c model_reasoning_effort="high"
research-workbench-prefs-extra-args-help = Advanced option. Arguments are inserted into each Codex chat request.
research-workbench-prefs-timeout = Timeout in seconds
research-workbench-prefs-timeout-help = Applies to one chat reply or connection test. Values are limited to 60-3600 seconds.
research-workbench-prefs-test-button = Detect Codex
research-workbench-prefs-reset-button = Restore Defaults

research-workbench-prefs-chat-heading = AI chat
research-workbench-prefs-chat-help = Each literature item keeps its own multi-turn Codex conversation. The first question includes the selected context material; later questions continue the same session.

research-workbench-prefs-context-heading = Material sent to Codex
research-workbench-prefs-include-pdf = PDF full text
research-workbench-prefs-include-annotations = PDF annotations
research-workbench-prefs-include-notes = Zotero notes
research-workbench-prefs-include-attachments = Attachment list
research-workbench-prefs-include-imported = Imported README and documentation
research-workbench-prefs-max-context = Maximum total context characters
research-workbench-prefs-max-context-help = Larger values provide more source text but consume more subscription quota and take longer.
research-workbench-prefs-per-doc = Maximum characters per imported document
research-workbench-prefs-per-doc-help = Limits how much of each README or text attachment is included in the AI context. The attachment itself is stored in full.

research-workbench-prefs-privacy = The selected Zotero metadata and documents are assembled locally and passed to the signed-in Codex CLI. Chat history is stored locally in your Zotero data directory.
