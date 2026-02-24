# API Reference - pb2obsidian

**Version:** 0.1.0
**Module:** pb2obsidian.py
**Last Updated:** 2026-02-24

---

## Table of Contents

- [Clipboard Functions](#clipboard-functions)
- [Conversion Functions](#conversion-functions)
- [Image Processing](#image-processing)
- [Utility Functions](#utility-functions)
- [CLI Interface](#cli-interface)

---

## Clipboard Functions

### `detect_clipboard_format()`

Detect the best rich text format available on the clipboard.

**Signature:**
```python
def detect_clipboard_format() -> tuple[str | None, bytes | None]
```

**Parameters:**
- None

**Returns:**
- `tuple[str | None, bytes | None]`:
  - `("rtf", bytes)` if RTF data found (preferred)
  - `("html", bytes)` if HTML data found (fallback)
  - `(None, None)` if no rich text found

**Behavior:**
- Prefers RTF over HTML (cleaner Markdown output)
- Uses macOS `NSPasteboard.generalPasteboard()`
- Checks `NSPasteboardTypeRTF` first, then `NSPasteboardTypeHTML`

**Example:**
```python
format_type, data = detect_clipboard_format()
if format_type is None:
    print("No rich text on clipboard")
else:
    print(f"Found {format_type.upper()}: {len(data)} bytes")
```

**Platform:** macOS only (NSPasteboard API)

---

### `set_clipboard_text(text)`

Write plain text to the macOS clipboard.

**Signature:**
```python
def set_clipboard_text(text: str) -> None
```

**Parameters:**
- `text` (str): Plain text string to place on clipboard

**Returns:**
- None

**Behavior:**
- Clears existing clipboard contents
- Sets plain text (`NSPasteboardTypeString`)
- Replaces all previous clipboard data

**Example:**
```python
markdown = "# Hello World\n\nThis is markdown."
set_clipboard_text(markdown)
# Clipboard now contains the markdown text
```

**Platform:** macOS only (NSPasteboard API)

---

## Conversion Functions

### `convert_to_markdown(rich_bytes, source_format, media_dir)`

Convert rich text bytes to Markdown via pandoc, extracting images to media_dir.

**Signature:**
```python
def convert_to_markdown(
    rich_bytes: bytes,
    source_format: str,
    media_dir: Path
) -> str
```

**Parameters:**
- `rich_bytes` (bytes): Raw RTF or HTML data
- `source_format` (str): Either `"rtf"` or `"html"`
- `media_dir` (Path): Directory where pandoc will extract embedded images (typically a temporary staging directory)

**Returns:**
- `str`: Raw Markdown string from pandoc (GFM format)

**Behavior:**
1. Creates temp file with appropriate suffix (`.rtf` or `.html`)
2. Writes `rich_bytes` to temp file
3. Invokes pandoc with:
   - Target format: `gfm` (GitHub Flavored Markdown)
   - `--extract-media {media_dir}` for embedded images
   - `--wrap=none` to preserve line structure
4. Cleans up temp file
5. Returns raw Markdown string

**Why GFM?**
Pandoc's default `markdown` format includes extensions Obsidian cannot render:
- Fenced divs (`::: {}`)
- Bracketed spans (`[text]{.class}`)
- Header attributes

GFM is closest to Obsidian's Markdown flavor.

**Example:**
```python
format_type, rich_bytes = detect_clipboard_format()
if format_type:
    with tempfile.TemporaryDirectory() as staging_dir:
        staging_path = Path(staging_dir)
        markdown = convert_to_markdown(rich_bytes, format_type, staging_path)
        # markdown contains GFM, images in staging_path/media/
```

**Requirements:**
- `pandoc` must be installed and in PATH
- `pypandoc` Python package

**Raises:**
- `RuntimeError`: If pandoc not found or conversion fails

---

## Image Processing

### `resize_image(image_path, max_width)`

Resize an image so its width does not exceed max_width, preserving aspect ratio.

**Signature:**
```python
def resize_image(image_path: Path, max_width: int) -> None
```

**Parameters:**
- `image_path` (Path): Path to image file
- `max_width` (int): Maximum width in pixels

**Returns:**
- None (modifies file in place)

**Behavior:**
- Opens image with Pillow
- Skips if `image.width <= max_width`
- Calculates aspect ratio: `ratio = max_width / image.width`
- Resizes: `new_height = int(image.height * ratio)`
- Uses `Image.LANCZOS` resampling (high quality)
- Saves over original file

**Example:**
```python
image_path = Path("my-note/screenshot.png")
resize_image(image_path, max_width=1024)
# Image now max 1024px wide, aspect ratio preserved
```

**Supported Formats:**
Any format Pillow supports (PNG, JPG, GIF, BMP, TIFF, WEBP, SVG)

**Note:** Modifies file in place - no backup created

---

### `process_images(markdown, staging_dir, dest_dir, base_name, max_width=None)`

Rename extracted images sequentially, move them to dest_dir, and rewrite Markdown references.

**Signature:**
```python
def process_images(
    markdown: str,
    staging_dir: Path,
    dest_dir: Path,
    base_name: str,
    max_width: int | None = None
) -> tuple[str, int]
```

**Parameters:**
- `markdown` (str): Raw Markdown from pandoc
- `staging_dir` (Path): Temporary directory where pandoc extracted images
- `dest_dir` (Path): Final target directory for processed images
- `base_name` (str): Base name for sequential renaming
- `max_width` (int | None): Optional max width for resizing

**Returns:**
- `tuple[str, int]`:
  - Processed Markdown with rewritten references
  - Count of images processed

**Behavior:**

1. **Find Images**: Recursively searches `staging_dir` for files with extensions:
   - `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`, `.svg`

2. **Rename Sequentially** (within staging dir):
   - `{base_name}.image-001.png`
   - `{base_name}.image-002.jpg`
   - etc.

3. **Rewrite References**:
   - Replaces absolute paths: `/tmp/staging/media/image1.png` → `base_name.image-001.png`
   - Replaces relative paths: `media/image1.png` → `base_name.image-001.png`

4. **Resize** (if `max_width` provided):
   - Calls `resize_image()` on each image in the staging directory

5. **Move to Destination**:
   - Moves each processed image from `staging_dir` to `dest_dir`
   - Pre-existing files in `dest_dir` are never scanned or modified

6. **Convert to Obsidian Format**:
   - `![alt](filename.png)` → `![[filename.png]]`
   - `<img src="filename.png" />` → `![[filename.png]]`

7. **Insert Spacing**:
   - Adds space between consecutive embeds: `]]![[` → `]] ![[`

**Example:**
```python
with tempfile.TemporaryDirectory() as staging_dir:
    staging_path = Path(staging_dir)
    markdown = convert_to_markdown(rich_bytes, "rtf", staging_path)
    processed_md, img_count = process_images(
        markdown,
        staging_path,
        dest_dir=Path("~/vault/attachments"),
        base_name="meeting-notes",
        max_width=1024,
    )
print(f"Processed {img_count} images")
# Images now in dest_dir: meeting-notes.image-001.png, etc.
# References: ![[meeting-notes.image-001.png]]
```

**Image Extensions Recognized:**
```python
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".tiff", ".tif", ".webp", ".svg"
}
```

---

## Utility Functions

### `slugify(title)`

Convert a title string to a filesystem-safe slug.

**Signature:**
```python
def slugify(title: str) -> str
```

**Parameters:**
- `title` (str): Human-readable title string

**Returns:**
- `str`: Filesystem-safe slug (lowercase, underscores for spaces)

**Behavior:**
1. Convert to lowercase
2. Strip leading/trailing whitespace
3. Remove non-alphanumeric characters (except spaces, hyphens, underscores)
4. Replace whitespace runs with single underscore
5. Collapse multiple underscores to single underscore
6. Strip leading/trailing underscores

**Examples:**
```python
slugify("AI Meeting 2026-02-01")
# → "ai_meeting_2026-02-01"

slugify("Design Review: Q1 Planning")
# → "design_review_q1_planning"

slugify("  Multi   Space   Title  ")
# → "multi_space_title"

slugify("Special!@#$%Characters")
# → "specialcharacters"
```

**Use Cases:**
- Creating directory names from titles
- Generating Markdown filenames
- Creating image base names

---

## CLI Interface

### `parse_args()`

Parse command-line arguments with environment variable fallbacks.

**Signature:**
```python
def parse_args() -> argparse.Namespace
```

**Parameters:**
- None (reads from `sys.argv` and environment)

**Returns:**
- `argparse.Namespace` with attributes:
  - `title` (str | None): User-provided title
  - `image_width` (int | None): Max image width in pixels
  - `md_dir` (str | None): Markdown output directory
  - `image_dir` (str | None): Image output directory
  - `skip_note` (bool): Whether to skip file creation (CLI only, no env var)

**Priority Order:**
```
CLI arguments > Environment variables > .env file > defaults
```

**Environment Variables:**
- `PB2OBSIDIAN_IMAGE_WIDTH` → `--image-width`
- `PB2OBSIDIAN_MD_DIR` → `--md-dir`
- `PB2OBSIDIAN_IMAGE_DIR` → `--image-dir`

**Example:**
```python
args = parse_args()
print(f"Title: {args.title}")
print(f"Max width: {args.image_width}")
print(f"MD dir: {args.md_dir}")
print(f"Image dir: {args.image_dir}")
print(f"Skip note: {args.skip_note}")
```

**CLI Usage:**
```bash
# Title with custom directories
pb2obsidian -t "Meeting Notes" --md-dir ~/vault/notes --image-dir ~/vault/attachments

# Image resizing
pb2obsidian --image-width 1024

# Skip file creation (clipboard only)
pb2obsidian --skip-note
```

---

### `main()`

Entry point orchestrating the full conversion workflow.

**Signature:**
```python
def main() -> None
```

**Parameters:**
- None

**Returns:**
- None

**Exit Codes:**
- `0`: Success
- `1`: Error (pandoc missing, no rich text on clipboard)

**Workflow:**

1. **Load Configuration**
   - Load `.env` from script directory (if exists)
   - Load `.env` from current directory (if exists, overrides)
   - Parse command-line arguments

2. **Validate Environment**
   - Check pandoc is installed (`shutil.which("pandoc")`)
   - Exit with error message if missing

3. **Detect Clipboard Format**
   - Call `detect_clipboard_format()`
   - Exit if no rich text found

4. **Determine Output Structure**
   - If `--title` provided: `base_name = slugify(title)`
   - Else: `base_name = f"clipboard-{timestamp}"`
   - Default directories: `{cwd}/{base_name}/`
   - Override with `--md-dir` and/or `--image-dir`

5. **Convert and Process** (inside a temporary staging directory)
   - `convert_to_markdown()` → raw Markdown + images extracted to staging dir
   - `process_images()` → rename and resize in staging dir, move to dest, rewrite references

6. **Write Output**
   - Write Markdown file (unless `--skip-note`)
   - Place Markdown on clipboard

7. **Display Summary**
   - Print Markdown path
   - Print image count and location
   - Print image width if resized
   - Confirm clipboard placement

**Example Execution:**
```python
if __name__ == "__main__":
    main()
```

**Sample Output:**
```
Detected clipboard format: RTF
Markdown written to: ./meeting_notes_2026-02-24/meeting_notes_2026-02-24.md
Extracted 3 image(s) to: ./meeting_notes_2026-02-24
Images scaled to max width: 1024px
Markdown placed on clipboard.
```

---

## Probe Clipboard Utility

### `probe_clipboard()` (probe_clipboard.py)

Diagnostic tool to inspect all data types available on the macOS clipboard.

**Signature:**
```python
def probe_clipboard() -> None
```

**Parameters:**
- None

**Returns:**
- None (prints to stdout)

**Behavior:**
1. Gets all pasteboard types from `NSPasteboard.generalPasteboard()`
2. For each type:
   - Prints type name
   - Gets data length (bytes)
   - For text types: shows 100-char preview

**Example Output:**
```
Found 5 pasteboard type(s) on clipboard:

1. public.rtf
   → Data length: 14832 bytes

2. public.html
   → Data length: 8421 bytes

3. public.utf8-plain-text
   → Data length: 523 bytes
   → Preview: # Meeting Notes\n\nDiscussed the Q1 roadmap...

4. public.png
   → Data length: 156234 bytes

5. com.apple.webarchive
   → Data length: 42817 bytes
```

**Use Cases:**
- Debugging why pb2obsidian can't find rich text
- Understanding what data an application provides
- Testing clipboard integration with different apps

**Usage:**
```bash
uv run python probe_clipboard.py
```

---

## Error Handling

### Common Errors

**No pandoc installed:**
```
Error: pandoc is not installed.
Install it with: brew install pandoc
```

**No rich text on clipboard:**
```
Error: No rich text (RTF or HTML) found on clipboard.
Copy some rich text first (e.g., from a webpage, email, Teams, or Word doc).
```

**Pandoc conversion failure:**
```
RuntimeError: Pandoc conversion failed: [pandoc error message]
```

---

## Dependencies

### Required Python Packages
- `pyobjc-framework-cocoa` → NSPasteboard API
- `pypandoc` → Pandoc wrapper
- `pillow` → Image processing
- `python-dotenv` → .env loading

### Required External Tools
- `pandoc` → RTF/HTML conversion

---

## Platform Requirements

**macOS only:** Uses Apple's `NSPasteboard` API for clipboard access.

**Python:** >=3.12 required

---

## See Also

- [PROJECT_INDEX.md](./PROJECT_INDEX.md) - Project overview and quick reference
- [README.md](./README.md) - User guide and usage examples
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Design decisions and workflow
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Contributing and development
