# Zotero Research Workbench

Local-first dashboard for reading, categorizing, annotating, and reporting on a
Zotero library. It reads the local Zotero SQLite database, exports structured
notes and metadata, and serves a dependency-free web dashboard.

## Features

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

## Requirements

- Python 3.10 or newer
- Zotero desktop with a local data directory
- Optional: Codex CLI for local Codex report generation
- Optional: an OpenAI-compatible API endpoint and key for API report generation

No third-party Python packages are required. The application uses the Python
standard library.

## Installation

```bash
git clone https://github.com/<your-account>/zotero-research-workbench.git
cd zotero-research-workbench
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

## Quick Start

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

Windows users can double-click `open-desktop.cmd` when a compatible bundled
Python runtime is present. On other systems, use the two Python commands above.

## Zotero Data Directory

The default Zotero path is:

```text
%USERPROFILE%\Zotero
```

The application reads these files:

```text
zotero.sqlite
zotero.sqlite-wal
zotero.sqlite-shm
```

It copies them into `.cache/` and queries the snapshot. Zotero can remain open
while the application runs.

Override the data directory:

```bash
python sync_zotero.py --zotero-dir "D:\path\to\Zotero"
python app_server.py
```

## Synchronization

Run `sync_zotero.py` after changing Zotero data:

```bash
python sync_zotero.py
```

The dashboard reads the generated `output/data/library.json`. The resync process
does not modify Zotero.

## Configuration

Copy example configuration files to local files:

```bash
cp config/categories.example.json config/categories.json
cp config/ai.example.json config/ai.json
```

### Categories

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

### AI Reports

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

## Command Line Options

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

## REST API

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

## Output Layout

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

## Privacy

- Zotero data is read from a local snapshot.
- Generated notes, annotations, and reports stay in the local output directory.
- API or Codex report generation sends only the material referenced by the
  selected report scope and the instruction supplied in the request.
- The application does not upload Zotero data.

## Limitations

- Classification follows Zotero collections but does not write back to Zotero.
- Moving an item between categories requires changing its Zotero collection and
  resyncing.
- The application is not a replacement for Zotero's own note editing or backup
  tools.
- Codex CLI requires access to the user's Codex configuration directory. When
  that access is unavailable, API mode can be used instead.

## License

Released under the [MIT License](LICENSE).
