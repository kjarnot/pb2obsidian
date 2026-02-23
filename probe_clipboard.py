#!/usr/bin/env python3
# ABOUTME: Diagnostic tool to inspect all data types available on the macOS clipboard.
# ABOUTME: Helps determine what format applications put on the clipboard.

from AppKit import NSPasteboard


def probe_clipboard():
    """List all pasteboard types currently on the clipboard."""
    pb = NSPasteboard.generalPasteboard()
    types = pb.types()

    print(f"Found {len(types)} pasteboard type(s) on clipboard:\n")

    for i, ptype in enumerate(types, 1):
        print(f"{i}. {ptype}")

        # Try to get data for this type
        data = pb.dataForType_(ptype)
        if data:
            data_len = len(data)
            print(f"   → Data length: {data_len} bytes")

            # For text types, show a preview
            if any(text_type in str(ptype).lower() for text_type in ['string', 'text', 'utf8']):
                try:
                    text = pb.stringForType_(ptype)
                    if text:
                        preview = text[:100].replace('\n', '\\n')
                        if len(text) > 100:
                            preview += "..."
                        print(f"   → Preview: {preview}")
                except:
                    pass
        else:
            print(f"   → No data available")

        print()


if __name__ == "__main__":
    probe_clipboard()
