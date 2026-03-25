#!/usr/bin/env python3
# Script to extract embedded manuals from src/tarpitd.py
# and write them to markdown files under docs/manual/
# This is the reverse operation of insert_doc.py

import re
from pathlib import Path
from typing import Optional

# Configuration constants
DOC_WRAP = "# ============================================================================="
DOC_START = "# -----------------------------------------------------------------------------"
SRC_FILE = Path("./src/tarpitd.py")
DOCS_FOLDER = Path("./docs/manual")
MANPAGES = ["tarpitd.py.1", "tarpitd.conf.5"]


def extract_manual(content: str, manual_name: str) -> Optional[str]:
    """
    Extract the manual content from the Python source file.

    Finds the manual section and returns the content between the triple quotes.
    """
    # Convert manual name to variable name
    # e.g., "tarpitd.py.1" -> "_MANUAL_TARPITD_PY_1"
    var_name = f"_MANUAL_{manual_name.upper().replace('.', '_')}"

    # Find the manual section header
    try:
        wrap_index = content.index(DOC_WRAP)
        manual_index = content.index(f"# Manual: {manual_name}", wrap_index)
        start_marker = content.index(DOC_START, manual_index)

        # Find the variable assignment
        var_pattern = f'{var_name} = r"""'
        var_index = content.index(var_pattern, start_marker)
        content_start = var_index + len(var_pattern)

        # Find the closing triple quotes
        # Use a regex to find the next """ after the content start
        closing_pattern = re.compile(r'"""\s*(?=\n# ====|\n\n|$)', re.MULTILINE)
        match = closing_pattern.search(content, content_start)

        if not match:
            raise ValueError(
                f"Could not find closing triple quotes for '{manual_name}'"
            )

        content_end = match.start()

        # Extract and return the content
        manual_content = content[content_start:content_end]
        return manual_content.strip()

    except ValueError as e:
        raise ValueError(f"Could not find manual '{manual_name}': {e}")


def main():
    # Read the source file content
    try:
        content = SRC_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {SRC_FILE}: {e}")
        return

    for manual_name in MANPAGES:
        md_file = DOCS_FOLDER / f"{manual_name}.md"

        try:
            manual_content = extract_manual(content, manual_name)
        except ValueError as e:
            print(f"Error extracting manual '{manual_name}': {e}")
            continue

        # Write the extracted content to the markdown file
        try:
            md_file.write_text(manual_content, encoding="utf-8")
            print(f"Extracted manual '{manual_name}' to {md_file}.")
        except Exception as e:
            print(f"Error writing to {md_file}: {e}")
            continue

    print("Manual extraction completed successfully")


if __name__ == "__main__":
    main()
