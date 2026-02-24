# Developer Guide - pb2obsidian

**Version:** 0.1.0
**Last Updated:** 2026-02-24

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Contributing](#contributing)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

**Required:**
- macOS (uses NSPasteboard API)
- Python >=3.12
- [uv](https://docs.astral.sh/uv/) (dependency manager)
- [pandoc](https://pandoc.org/) (RTF/HTML converter)

**Installation:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pandoc
brew install pandoc
```

---

## Development Setup

### 1. Clone Repository

```bash
git clone git@github.com:kjarnot/pb2obsidian.git
cd pb2obsidian
```

### 2. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 3. Verify Installation

```bash
# Test main tool
uv run python pb2obsidian.py --help

# Test diagnostic utility
uv run python probe_clipboard.py
```

### 4. Configure Editor

**VS Code (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.rulers": [88],
    "editor.tabSize": 4
  }
}
```

**PyCharm:**
- File → Settings → Project → Python Interpreter
- Select `.venv/bin/python`
- Enable "Format on Save" (black)

---

## Project Structure

```
pb2obsidian/
├── pb2obsidian.py          # Main tool (304 lines)
├── probe_clipboard.py      # Diagnostic utility (43 lines)
├── pyproject.toml          # Project config + dependencies
├── uv.lock                 # Dependency lock file
├── README.md               # User documentation
├── PROJECT_INDEX.md        # Project overview
├── API_REFERENCE.md        # Function API docs
├── ARCHITECTURE.md         # Design decisions
├── DEVELOPER_GUIDE.md      # This file
├── .venv/                  # Virtual environment (git-ignored)
├── .env                    # User config (git-ignored)
└── notes/                  # Example outputs (git-tracked)
    └── mo-20260211/
        ├── mo-20260211.md
        └── mo-20260211.image-*.jpg
```

### Git Ignore

**.gitignore:**
```
.venv/
__pycache__/
*.pyc
*.pyo
.env
.DS_Store
```

**What to Track:**
- ✅ `pb2obsidian.py`, `probe_clipboard.py`
- ✅ `pyproject.toml`, `uv.lock`
- ✅ Documentation (*.md)
- ✅ Example outputs (`notes/`)
- ❌ `.venv/` (recreated via `uv sync`)
- ❌ `.env` (user-specific config)

---

## Development Workflow

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Edit `pb2obsidian.py` or `probe_clipboard.py`
   - Follow existing code style (see [Code Style](#code-style))

3. **Test Changes**
   ```bash
   # Manual test
   uv run python pb2obsidian.py -t "Test Note"

   # Verify output
   ls -la ./test_note/
   cat ./test_note/test_note.md
   ```

4. **Update Documentation**
   - If API changes: Update `API_REFERENCE.md`
   - If design changes: Update `ARCHITECTURE.md`
   - Always update: `README.md` (if user-facing)

5. **Commit Changes**
   ```bash
   git add pb2obsidian.py API_REFERENCE.md
   git commit -m "Add support for custom image formats"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

---

## Code Style

### General Principles

- **PEP 8 compliant** (via black formatter)
- **Type hints** for function signatures (Python 3.12+)
- **Docstrings** for all public functions (Google style)
- **Comments** for complex logic only (code should be self-documenting)

### Example Function

```python
def process_images(
    markdown: str,
    staging_dir: Path,
    dest_dir: Path,
    base_name: str,
    max_width: int | None = None
) -> tuple[str, int]:
    """Rename extracted images sequentially and move them to dest_dir.

    staging_dir is a temporary directory where pandoc extracted images.
    dest_dir is the final target directory for processed images.
    This function:
    - Finds all image files pandoc created under staging_dir
    - Renames each to {base_name}.image-001.png, etc.
    - Optionally resizes images to max_width (preserving aspect ratio)
    - Moves final files to dest_dir
    - Rewrites all references in the Markdown to Obsidian wiki-link format

    Args:
        markdown: Raw Markdown string from pandoc
        staging_dir: Temporary directory where pandoc extracted images
        dest_dir: Final target directory for processed images
        base_name: Base name for sequential image renaming
        max_width: Optional maximum image width in pixels

    Returns:
        tuple[str, int]: (processed_markdown, image_count)

    Example:
        >>> md, count = process_images(markdown, Path("/tmp/staging"), Path("./note"), "meeting", 1024)
        >>> print(f"Processed {count} images")
        Processed 3 images
    """
    # Implementation...
```

### ABOUTME Comments

**All files must start with ABOUTME comments:**
```python
#!/usr/bin/env python3
# ABOUTME: Reads rich text (RTF or HTML) from the macOS clipboard, converts to Markdown via pandoc,
# ABOUTME: extracts embedded images, and rewrites image refs as Obsidian ![[wiki-links]].
```

**Purpose:** Quickly grep for file purposes across projects.

```bash
grep -r "^# ABOUTME:" .
```

---

## Testing

### Current State

**No automated tests currently.** Testing is manual via example conversions.

**Why?**
- Small, single-purpose tool (304 lines)
- Heavy reliance on external tools (pandoc, NSPasteboard)
- Clipboard testing difficult to automate

---

### Manual Testing Checklist

Before each release, test these scenarios:

#### 1. **Basic Conversion**
```bash
# Copy rich text from browser (e.g., Wikipedia article with images)
uv run python pb2obsidian.py -t "test-basic"

# Verify:
✓ Markdown file created
✓ Images extracted and renamed
✓ References are ![[image-001.png]] format
✓ Markdown on clipboard
```

#### 2. **Image Resizing**
```bash
# Copy content with large images (>2000px wide)
uv run python pb2obsidian.py -t "test-resize" --image-width 1024

# Verify:
✓ Images scaled to 1024px wide
✓ Aspect ratio preserved
✓ File sizes reduced
```

#### 3. **Custom Directories**
```bash
uv run python pb2obsidian.py -t "test-dirs" \
  --md-dir ~/tmp/notes \
  --image-dir ~/tmp/images

# Verify:
✓ Markdown in ~/tmp/notes/
✓ Images in ~/tmp/images/
✓ References work despite separate dirs
```

#### 3b. **Shared Image Directory (Pre-Existing Files)**
```bash
# Create a test directory with pre-existing images
mkdir -p ~/tmp/shared-images
cp some-existing-image.png ~/tmp/shared-images/

# Copy rich text with images to clipboard, then:
uv run python pb2obsidian.py -t "test-shared" \
  --image-dir ~/tmp/shared-images

# Verify:
✓ Pre-existing images in ~/tmp/shared-images/ are UNTOUCHED
✓ Only new images appear with test_shared.image-NNN.ext naming
✓ Pre-existing image filenames are unchanged (not renamed or resized)
```

#### 4. **Skip Note Flag**
```bash
uv run python pb2obsidian.py -t "test-skip" --skip-note

# Verify:
✓ No Markdown file created
✓ Images still extracted
✓ Markdown on clipboard
```

#### 5. **Environment Variables**
```bash
echo "PB2OBSIDIAN_IMAGE_WIDTH=800" > .env
uv run python pb2obsidian.py -t "test-env"

# Verify:
✓ Images resized to 800px (from .env)
✓ Can override with CLI: --image-width 1200
```

#### 6. **Edge Cases**
```bash
# Test with no images
# Copy plain text → should work, no image processing

# Test with no rich text
# Copy plain text only → should error gracefully

# Test with special characters in title
uv run python pb2obsidian.py -t "Test: Special!@# Characters"
# Verify: slugified correctly → test_special_characters
```

---

### Adding Automated Tests (Future)

**Recommended Approach:**

1. **Mock NSPasteboard**
   ```python
   from unittest.mock import MagicMock, patch

   @patch('AppKit.NSPasteboard')
   def test_detect_clipboard_format(mock_pasteboard):
       # Mock RTF data
       mock_pb = MagicMock()
       mock_pb.dataForType_.return_value = b'rtf data'
       mock_pasteboard.generalPasteboard.return_value = mock_pb

       format_type, data = detect_clipboard_format()
       assert format_type == "rtf"
       assert data == b'rtf data'
   ```

2. **Fixture-Based Testing**
   ```python
   # tests/fixtures/sample.rtf
   # tests/fixtures/sample.html

   def test_convert_to_markdown():
       with open("tests/fixtures/sample.rtf", "rb") as f:
           rtf_bytes = f.read()

       output_dir = Path("tests/output")
       markdown = convert_to_markdown(rtf_bytes, "rtf", output_dir)

       assert "# Sample" in markdown
       assert len(list(output_dir.glob("*.png"))) > 0
   ```

3. **Integration Tests**
   ```python
   def test_full_workflow():
       # Given: RTF file with embedded images
       # When: Run full conversion
       # Then: Verify output structure and content
   ```

**Test Framework:** pytest + pytest-mock

**Coverage Goal:** >80% (excluding CLI arg parsing)

---

## Contributing

### Contribution Guidelines

1. **Check Existing Issues**
   - Search GitHub issues before creating new ones
   - Comment on existing issues if you plan to work on them

2. **Discuss Major Changes**
   - Open an issue first for architectural changes
   - Get feedback before investing time

3. **Follow Code Style**
   - Use black formatter (enforced)
   - Type hints required for new functions
   - Docstrings required for public API

4. **Update Documentation**
   - API changes → Update `API_REFERENCE.md`
   - Design changes → Update `ARCHITECTURE.md`
   - User-facing → Update `README.md`

5. **Test Thoroughly**
   - Run manual test checklist (see [Testing](#testing))
   - Add fixtures for new features

6. **Write Clear Commit Messages**
   ```
   Add support for custom image formats

   - Add WEBP, AVIF to IMAGE_EXTENSIONS
   - Update documentation with new formats
   - Test with sample images
   ```

---

### Areas for Contribution

**Good First Issues:**
- 🟢 Add support for new image formats
- 🟢 Improve error messages
- 🟢 Add CLI flag for preserving original image names
- 🟢 Documentation improvements

**Medium Difficulty:**
- 🟡 Add automated tests (pytest setup)
- 🟡 Cross-platform clipboard support (Linux/Windows)
- 🟡 Image compression option (optimize file sizes)

**Advanced:**
- 🔴 Watch mode (monitor clipboard continuously)
- 🔴 Obsidian plugin (direct vault integration)
- 🔴 OCR for image text extraction

---

## Release Process

### Version Numbering

**Semantic Versioning (semver):**
- **MAJOR:** Breaking changes (e.g., CLI interface change)
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes, documentation updates

**Example:**
- `0.1.0` → Initial release
- `0.2.0` → Add `--skip-note` flag
- `0.2.1` → Fix image resize bug

---

### Release Checklist

1. **Update Version**
   ```toml
   # pyproject.toml
   [project]
   version = "0.2.0"
   ```

2. **Update Changelog**
   ```markdown
   # CHANGELOG.md

   ## [0.2.0] - 2026-02-24

   ### Added
   - `--skip-note` flag to skip Markdown file creation
   - Environment variable support for all options

   ### Fixed
   - Image resize aspect ratio calculation
   ```

3. **Run Full Test Suite**
   - Manual test checklist (see [Testing](#testing))
   - Verify all examples in README work

4. **Update Documentation**
   - `README.md` → Usage examples
   - `API_REFERENCE.md` → New functions/parameters
   - `ARCHITECTURE.md` → Design changes

5. **Commit Release**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release v0.2.0"
   git tag v0.2.0
   git push origin master --tags
   ```

6. **GitHub Release**
   - Create release on GitHub
   - Copy CHANGELOG entry to release notes
   - Attach zip of source code

---

## Troubleshooting

### Common Issues

#### 1. **"pandoc is not installed"**

**Symptom:**
```
Error: pandoc is not installed.
Install it with: brew install pandoc
```

**Solution:**
```bash
brew install pandoc
# Verify: which pandoc
```

---

#### 2. **"No rich text found on clipboard"**

**Symptom:**
```
Error: No rich text (RTF or HTML) found on clipboard.
```

**Diagnosis:**
```bash
uv run python probe_clipboard.py
# Check output for public.rtf or public.html
```

**Solution:**
- Copy rich text from app that provides RTF/HTML (browser, Word, etc.)
- Some apps (e.g., terminal) only provide plain text

---

#### 3. **Images Not Extracted**

**Symptom:** Markdown created but no images in output directory.

**Diagnosis:**
- Check if source content actually has embedded images
- Verify pandoc version: `pandoc --version` (needs `--extract-media` support)

**Solution:**
```bash
# Test pandoc directly
echo '<img src="data:image/png;base64,..."/>' | \
  pandoc -f html -t gfm --extract-media=./test
# Should create ./test/media/image1.png
```

---

#### 4. **Permission Denied on Image Resize**

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'note.image-001.png'
```

**Solution:**
- Check file permissions: `ls -la`
- Ensure output directory is writable
- Try running with `sudo` (not recommended for normal use)

---

#### 5. **Module Import Errors**

**Symptom:**
```
ModuleNotFoundError: No module named 'AppKit'
```

**Solution:**
```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Reinstall dependencies
uv sync

# Verify installation
python -c "from AppKit import NSPasteboard"
```

---

### Debug Mode

**Enable verbose output:**
```python
# Add to main() for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Useful Debug Commands:**
```bash
# Check clipboard types
uv run python probe_clipboard.py

# Verify pandoc
which pandoc
pandoc --version

# Check Python environment
python --version
python -m site

# List installed packages
uv pip list
```

---

## Development Tools

### Recommended Tools

1. **black** (formatter)
   ```bash
   uv pip install black
   black pb2obsidian.py
   ```

2. **pylint** (linter)
   ```bash
   uv pip install pylint
   pylint pb2obsidian.py
   ```

3. **mypy** (type checker)
   ```bash
   uv pip install mypy
   mypy pb2obsidian.py
   ```

4. **ipython** (REPL)
   ```bash
   uv pip install ipython
   ipython
   ```

---

## Resources

### Documentation
- [Pandoc Manual](https://pandoc.org/MANUAL.html)
- [PyObjC Documentation](https://pyobjc.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)

### Related Projects
- [obsidian-clipper](https://github.com/obsidianmd/obsidian-clipper) - Official Obsidian web clipper
- [obsidian-importer](https://github.com/obsidianmd/obsidian-importer) - Import tool for various formats
- [markdownify](https://github.com/matthewwithanm/python-markdownify) - HTML to Markdown (Python)

---

## See Also

- [API_REFERENCE.md](./API_REFERENCE.md) - Function signatures and usage
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Design decisions and workflow
- [PROJECT_INDEX.md](./PROJECT_INDEX.md) - Project overview
- [README.md](./README.md) - User guide
