#!/usr/bin/env python3
# ABOUTME: Reads rich text (RTF or HTML) from the macOS clipboard, converts to Markdown via pandoc,
# ABOUTME: extracts embedded images, and rewrites image refs as Obsidian ![[wiki-links]].
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyobjc-framework-cocoa", "pypandoc", "pillow", "python-dotenv"]
# ///

import argparse
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from AppKit import NSPasteboard, NSPasteboardTypeHTML, NSPasteboardTypeRTF, NSPasteboardTypeString

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg"}


def detect_clipboard_format():
    """Detect the best rich text format available on the clipboard.

    Prefers RTF over HTML since it tends to produce cleaner Markdown.
    Returns ("rtf", bytes), ("html", bytes), or (None, None) if no rich text found.
    """
    pb = NSPasteboard.generalPasteboard()

    rtf_data = pb.dataForType_(NSPasteboardTypeRTF)
    if rtf_data is not None:
        return "rtf", bytes(rtf_data)

    html_data = pb.dataForType_(NSPasteboardTypeHTML)
    if html_data is not None:
        return "html", bytes(html_data)

    return None, None


def set_clipboard_text(text):
    """Write plain text to the macOS clipboard."""
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSPasteboardTypeString)


def convert_to_markdown(rich_bytes, source_format, media_dir):
    """Convert rich text bytes to Markdown via pandoc, extracting images to media_dir.

    source_format should be "rtf" or "html".
    media_dir is the directory where pandoc will extract embedded images.
    Returns the raw Markdown string from pandoc.
    """
    import pypandoc

    suffix = f".{source_format}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(rich_bytes)
        tmp_path = tmp.name

    try:
        # Use gfm (GitHub Flavored Markdown) — closest to what Obsidian supports.
        # Pandoc's default "markdown" emits fenced divs (::: {}), bracketed spans
        # ([text]{.class}), and header attributes that Obsidian can't render.
        markdown = pypandoc.convert_file(
            tmp_path,
            "gfm",
            format=source_format,
            extra_args=["--extract-media", str(media_dir), "--wrap=none"],
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return markdown


def resize_image(image_path, max_width):
    """Resize an image so its width does not exceed max_width, preserving aspect ratio.

    Modifies the file in place. Skips images already within the width limit.
    """
    from PIL import Image

    with Image.open(image_path) as img:
        if img.width <= max_width:
            return
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        resized = img.resize((max_width, new_height), Image.LANCZOS)
        resized.save(image_path)


def process_images(markdown, staging_dir, dest_dir, base_name, max_width=None):
    """Rename extracted images sequentially and move them to dest_dir.

    staging_dir is a temporary directory where pandoc extracted images.
    dest_dir is the final target directory for processed images.
    This function:
    - Finds all image files pandoc created under staging_dir
    - Renames each to {base_name}.image-001.png, etc.
    - Optionally resizes images to max_width (preserving aspect ratio)
    - Moves final files to dest_dir
    - Rewrites all references in the Markdown to Obsidian wiki-link format

    Returns (processed_markdown, image_count).
    """
    # Find all image files pandoc extracted (may be in staging_dir or a media/ subdir)
    extracted_images = sorted(
        p for p in staging_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not extracted_images:
        return markdown, 0

    image_count = 0
    for src_path in extracted_images:
        image_count += 1
        ext = src_path.suffix or ".png"
        new_name = f"{base_name}.image-{image_count:03d}{ext}"
        staged_path = staging_dir / new_name

        # Replace all references to this image in the markdown (absolute or relative paths)
        # Pandoc may emit ![alt](path) or <img src="path"> depending on format
        old_path_str = str(src_path)
        markdown = markdown.replace(old_path_str, new_name)
        # Also try the path relative to staging_dir
        try:
            rel_path_str = str(src_path.relative_to(staging_dir))
            markdown = markdown.replace(rel_path_str, new_name)
        except ValueError:
            pass

        # Rename within staging dir first, then resize in place
        if src_path != staged_path:
            shutil.move(str(src_path), str(staged_path))

        if max_width is not None:
            resize_image(staged_path, max_width)

        # Move the final processed image to the destination directory
        shutil.move(str(staged_path), str(dest_dir / new_name))

    # Rewrite remaining ![alt](filename) references to Obsidian ![[filename]] wiki-links
    markdown = re.sub(
        r"!\[[^\]]*\]\(([^)]+)\)",
        lambda m: f"![[{m.group(1)}]]",
        markdown,
    )

    # Rewrite <img src="filename" .../> HTML tags to Obsidian wiki-links
    markdown = re.sub(
        r'<img\s[^>]*src="([^"]+)"[^>]*/?>',
        lambda m: f"![[{m.group(1)}]]",
        markdown,
    )

    # Insert a space between consecutive image embeds that are concatenated
    markdown = re.sub(r"(\]\])(!?\[\[)", r"\1 \2", markdown)

    return markdown, image_count


def slugify(title):
    """Convert a title string to a filesystem-safe slug.

    "AI Meeting 2026-02-01" → "ai_meeting_2026-02-01"
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "_", slug)
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


def parse_args():
    """Parse command-line arguments with environment variable fallbacks.

    Priority: command-line args > environment variables > .env file > defaults
    """
    parser = argparse.ArgumentParser(
        description="Convert clipboard rich text (RTF/HTML) to Markdown with Obsidian image links.",
        epilog="All options can also be set via environment variables (see README) or a .env file.",
    )
    parser.add_argument(
        "--image-width",
        type=int,
        default=os.environ.get("PB2OBSIDIAN_IMAGE_WIDTH"),
        help="Maximum image width in pixels. Images wider than this are scaled down "
             "preserving aspect ratio. Env: PB2OBSIDIAN_IMAGE_WIDTH.",
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None,
        help="Title for the content. Used to name the subfolder, Markdown file, and images.",
    )
    parser.add_argument(
        "--md-dir",
        type=str,
        default=os.environ.get("PB2OBSIDIAN_MD_DIR"),
        help="Directory to store the Markdown file. Overrides the default subfolder location. "
             "Env: PB2OBSIDIAN_MD_DIR.",
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default=os.environ.get("PB2OBSIDIAN_IMAGE_DIR"),
        help="Directory to store extracted image files. Overrides the default subfolder location. "
             "Env: PB2OBSIDIAN_IMAGE_DIR.",
    )
    parser.add_argument(
        "--skip-note",
        action="store_true",
        help="Skip creating the Markdown file. Only extract images and place Markdown on clipboard.",
    )

    args = parser.parse_args()

    # Coerce image_width from env var string to int
    if isinstance(args.image_width, str):
        args.image_width = int(args.image_width)

    return args


def main():
    # Load .env from the script's directory, then from cwd (cwd takes priority)
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / ".env", override=False)
    load_dotenv(Path.cwd() / ".env", override=True)

    args = parse_args()

    # Parent output directory is always the current working directory
    parent_dir = Path.cwd()
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Check pandoc is available
    if not shutil.which("pandoc"):
        print("Error: pandoc is not installed.", file=sys.stderr)
        print("Install it with: brew install pandoc", file=sys.stderr)
        sys.exit(1)

    # Detect clipboard format (RTF preferred, HTML as fallback)
    source_format, rich_bytes = detect_clipboard_format()
    if source_format is None:
        print("Error: No rich text (RTF or HTML) found on clipboard.", file=sys.stderr)
        print("Copy some rich text first (e.g., from a webpage, email, Teams, or Word doc).", file=sys.stderr)
        sys.exit(1)

    print(f"Detected clipboard format: {source_format.upper()}")

    # Derive base name from title or fall back to timestamped default
    if args.title:
        base_name = slugify(args.title)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = f"clipboard-{timestamp}"

    # Determine where markdown and images go.
    # --md-dir and --image-dir override the default subfolder layout.
    default_dir = parent_dir / base_name
    md_dir = Path(args.md_dir).expanduser().resolve() if args.md_dir else default_dir
    image_dir = Path(args.image_dir).expanduser().resolve() if args.image_dir else default_dir
    md_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    md_path = md_dir / f"{base_name}.md"

    # Extract images to a temp directory so we never touch pre-existing files
    # in shared directories (e.g., Obsidian's _attachments/ folder).
    # Images are renamed and resized in the temp dir, then moved to image_dir.
    with tempfile.TemporaryDirectory() as staging_dir:
        staging_path = Path(staging_dir)
        markdown = convert_to_markdown(rich_bytes, source_format, staging_path)
        markdown, image_count = process_images(
            markdown, staging_path, image_dir, base_name,
            max_width=args.image_width,
        )

    # Write Markdown to file (unless --skip-note)
    if not args.skip_note:
        md_path.write_text(markdown, encoding="utf-8")

    # Put Markdown on clipboard
    set_clipboard_text(markdown)

    # Summary
    if not args.skip_note:
        print(f"Markdown written to: {md_path}")
    if image_count > 0:
        print(f"Extracted {image_count} image(s) to: {image_dir}")
        if args.image_width:
            print(f"Images scaled to max width: {args.image_width}px")
    print("Markdown placed on clipboard.")


if __name__ == "__main__":
    main()
