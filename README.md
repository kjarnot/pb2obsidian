# pb2obsidian

A macOS command-line tool that converts rich text from the clipboard into Obsidian-compatible Markdown. It reads RTF or HTML from the pasteboard, runs it through pandoc, extracts embedded images to disk, renames them sequentially, and rewrites image references as Obsidian `![[wiki-links]]`. The resulting Markdown is written to a file and placed back on the clipboard.

## Prerequisites

- macOS (uses the native NSPasteboard API)
- [pandoc](https://pandoc.org/) for RTF/HTML to Markdown conversion
- [uv](https://docs.astral.sh/uv/) for dependency management

```bash
brew install pandoc
```

## Setup

```bash
git clone <repo-url> && cd rtf2md
uv sync
```

## Usage

Copy some rich text to the clipboard (from a webpage, email, MS Teams, Word, etc.), then run from your desired output directory:

```bash
uv run python pb2obsidian.py
```

Output is always relative to the current working directory.

### Command-Line Options

| Flag | Description |
|------|-------------|
| `-t, --title TITLE` | Title for the content. Slugified and used to name the subfolder, Markdown file, and images. |
| `--image-width PX` | Maximum image width in pixels. Wider images are scaled down preserving aspect ratio. |
| `--md-dir DIR` | Directory to store the Markdown file. Overrides the default subfolder. |
| `--image-dir DIR` | Directory to store extracted images. Overrides the default subfolder. |

### Examples

```bash
# Basic: output goes to ./clipboard-20260223-153651/
uv run python pb2obsidian.py

# Named output with title
uv run python pb2obsidian.py -t "AI Meeting 2026-02-01"
# → ./ai_meeting_2026-02-01/ai_meeting_2026-02-01.md
# → ./ai_meeting_2026-02-01/ai_meeting_2026-02-01.image-001.png

# Scale images down to 800px wide
uv run python pb2obsidian.py -t "Design Review" --image-width 800

# Separate Markdown and image directories
uv run python pb2obsidian.py -t "Meeting Notes" --md-dir ~/vault/notes --image-dir ~/vault/attachments

# Combine options
uv run python pb2obsidian.py -t "Q1 Planning" --image-width 1024 --image-dir ~/notes/images
```

## Configuration

All options (except `--title`) can be set via environment variables or a `.env` file so you don't have to type them every time.

### Environment Variables

| Variable | Corresponds to |
|----------|---------------|
| `PB2OBSIDIAN_IMAGE_WIDTH` | `--image-width` |
| `PB2OBSIDIAN_MD_DIR` | `--md-dir` |
| `PB2OBSIDIAN_IMAGE_DIR` | `--image-dir` |

### `.env` File

Create a `.env` file in the project directory (next to `pb2obsidian.py`) or in your current working directory:

```bash
# .env
PB2OBSIDIAN_IMAGE_WIDTH=1024
PB2OBSIDIAN_MD_DIR=~/Documents/obsidian-vault/notes
PB2OBSIDIAN_IMAGE_DIR=~/Documents/obsidian-vault/attachments
```

### Priority Order

Command-line args override environment variables, which override `.env` values:

```
CLI flags  >  environment variables  >  .env file  >  defaults
```

If a `.env` file exists in both the script directory and the current working directory, the cwd version takes priority.

## Output Structure

### Default (no title)

```
./clipboard-20260223-153651/
├── clipboard-20260223-153651.md
├── clipboard-20260223-153651.image-001.png
└── clipboard-20260223-153651.image-002.jpg
```

### With `--title "AI Meeting 2026-02-01"`

```
./ai_meeting_2026-02-01/
├── ai_meeting_2026-02-01.md
├── ai_meeting_2026-02-01.image-001.png
└── ai_meeting_2026-02-01.image-002.jpg
```

### With `--md-dir` and `--image-dir`

```
~/vault/notes/
└── ai_meeting_2026-02-01.md

~/vault/attachments/
├── ai_meeting_2026-02-01.image-001.png
└── ai_meeting_2026-02-01.image-002.jpg
```

## Clipboard Format Detection

The tool automatically detects whether the clipboard contains RTF or HTML data. RTF is preferred when both are present since it tends to produce cleaner Markdown. Applications like MS Teams typically provide HTML, while Word and macOS TextEdit provide RTF.

If the tool reports no rich text on the clipboard, you can use the diagnostic script to see what data types are available:

```bash
uv run python probe_clipboard.py
```

This lists every pasteboard type and its data size, which is useful for debugging clipboard issues with specific applications.

## How It Works

1. Reads RTF or HTML data from the macOS clipboard via `NSPasteboard`
2. Writes it to a temp file and converts to GFM (GitHub Flavored Markdown) via pandoc
3. pandoc's `--extract-media` flag pulls embedded images out to disk
4. Images are renamed sequentially (`{title}.image-001.png`, etc.) and optionally resized
5. Image references in the Markdown are rewritten to Obsidian embed syntax: `![[filename.png]]`
6. The final Markdown is written to disk and placed on the clipboard

### Why GFM?

Pandoc's default `markdown` output format includes extensions like fenced divs (`::: {}`), bracketed spans (`[text]{.class}`), and header attributes that Obsidian cannot render. GFM is the closest standard format to what Obsidian supports.

## Dependencies

Managed by uv via `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `pyobjc-framework-cocoa` | macOS clipboard access via NSPasteboard |
| `pypandoc` | Python wrapper for pandoc |
| `pillow` | Image resizing |
| `python-dotenv` | `.env` file loading |

External:

| Tool | Purpose |
|------|---------|
| `pandoc` | RTF/HTML to Markdown conversion and image extraction |
