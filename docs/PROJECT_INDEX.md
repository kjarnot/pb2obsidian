# Project Index: pb2obsidian

**Generated:** 2026-02-24
**Purpose:** macOS clipboard RTF/HTML to Markdown converter with Obsidian image links

---

## 📁 Project Structure

```
pb2obsidian/
├── pb2obsidian.py          # Main CLI tool (11KB)
├── probe_clipboard.py      # Clipboard diagnostic utility (1.3KB)
├── pyproject.toml          # Project config and dependencies
├── README.md               # Documentation
├── uv.lock                 # Dependency lock file
└── notes/                  # Example output directory
    └── mo-20260211/        # Sample converted note with images
```

---

## 🚀 Entry Points

### Primary Tool
- **CLI**: `pb2obsidian.py` → Main conversion tool
  - Script name: `pb2obsidian` (via pyproject.toml)
  - Usage: `uv run python pb2obsidian.py [options]`
  - Purpose: Convert rich clipboard content to Obsidian-compatible Markdown

### Diagnostic Tool
- **Utility**: `probe_clipboard.py` → Clipboard format inspector
  - Usage: `uv run python probe_clipboard.py`
  - Purpose: Debug clipboard data types and formats

---

## 📦 Core Modules

### pb2obsidian.py (Main Module)
**Functions:**
- `detect_clipboard_format()` → Returns ("rtf"|"html", bytes) or (None, None)
- `set_clipboard_text(text)` → Write to macOS clipboard
- `convert_to_markdown(bytes, format, media_dir)` → Pandoc RTF/HTML → Markdown conversion
- `process_images(md, staging_dir, dest_dir, base, width)` → Rename, resize, move images; rewrite refs
- `resize_image(path, max_width)` → Scale image preserving aspect ratio
- `slugify(title)` → Title → filesystem-safe slug (e.g., "AI Meeting" → "ai_meeting")
- `parse_args()` → CLI arg parsing with env var fallbacks
- `main()` → Entry point orchestrating full conversion workflow

**Key Constants:**
- `IMAGE_EXTENSIONS` → {.png, .jpg, .jpeg, .gif, .bmp, .tiff, .tif, .webp, .svg}

**Dependencies Used:**
- `AppKit.NSPasteboard` → macOS clipboard access
- `pypandoc` → Pandoc wrapper for format conversion
- `PIL.Image` → Image resizing via Pillow
- `dotenv.load_dotenv` → Environment config loading

### probe_clipboard.py (Diagnostic)
**Functions:**
- `probe_clipboard()` → List all pasteboard types with size/preview

---

## 🔧 Configuration

### pyproject.toml
- **Project metadata**: Name, version, description
- **Python requirement**: >=3.12
- **Dependencies**: pyobjc-framework-cocoa, pypandoc, pillow, python-dotenv
- **CLI script**: `pb2obsidian` entry point

### Environment Variables (optional .env)
- `PB2OBSIDIAN_IMAGE_WIDTH` → Max image width in pixels
- `PB2OBSIDIAN_MD_DIR` → Override Markdown output directory
- `PB2OBSIDIAN_IMAGE_DIR` → Override image output directory

**Priority:** CLI args > env vars > .env > defaults

---

## 📚 Documentation

- **README.md**: Complete usage guide
  - Prerequisites (macOS, pandoc, uv)
  - Setup instructions
  - Command-line options reference
  - Configuration via .env
  - Output structure examples
  - Clipboard format detection
  - How it works (workflow explanation)
  - Dependencies reference

---

## 🧪 Test Coverage

**Status:** No automated tests currently
- Manual testing via example outputs in `notes/mo-20260211/`
- Contains 8 extracted images + converted Markdown

---

## 🔗 Key Dependencies

### Python Packages (via pyproject.toml)
| Package | Version | Purpose |
|---------|---------|---------|
| pyobjc-framework-cocoa | latest | macOS NSPasteboard API access |
| pypandoc | latest | Python wrapper for pandoc |
| pillow | latest | Image processing and resizing |
| python-dotenv | latest | .env file loading |

### External Tools (required)
| Tool | Purpose |
|------|---------|
| pandoc | RTF/HTML → Markdown conversion + image extraction |
| uv | Python dependency management |

---

## 📝 Quick Start

### Installation
```bash
git clone git@github.com:kjarnot/pb2obsidian.git && cd pb2obsidian
uv sync
brew install pandoc  # if not installed
```

### Basic Usage
```bash
# Copy rich text to clipboard, then:
uv run python pb2obsidian.py

# With title
uv run python pb2obsidian.py -t "Meeting Notes 2026-02-24"

# Custom directories + image scaling
uv run python pb2obsidian.py -t "Q1 Planning" \
  --md-dir ~/vault/notes \
  --image-dir ~/vault/attachments \
  --image-width 1024

# Skip file creation (clipboard only)
uv run python pb2obsidian.py -t "Screenshots" --skip-note
```

### Diagnostic
```bash
# Inspect clipboard formats
uv run python probe_clipboard.py
```

---

## 🎯 Workflow Overview

1. **Clipboard Detection** → Reads RTF (preferred) or HTML from NSPasteboard
2. **Pandoc Conversion** → Converts to GFM (GitHub Flavored Markdown)
3. **Image Extraction** → Pandoc `--extract-media` pulls embedded images to a temporary staging directory
4. **Image Processing** → Sequential rename (`base.image-001.png`) + optional resize in staging dir
5. **Image Delivery** → Move processed images from staging dir to final destination
6. **Reference Rewrite** → Convert `![alt](path)` → `![[filename.png]]` (Obsidian format)
7. **Output** → Write Markdown file + place on clipboard

---

## 🏷️ Tags

`#clipboard` `#markdown` `#obsidian` `#pandoc` `#macos` `#rtf` `#html` `#image-extraction` `#python3.12` `#uv`

---

**Index Size:** ~4KB
**Total Project LOC:** ~350 lines (excluding dependencies)
**Complexity:** Low (single-purpose utility with clear workflow)
