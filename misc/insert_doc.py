import re
import textwrap
from pathlib import Path
from typing import List

# Configuration constants
DOC_WRAP = "# ============================================================================="
DOC_START = "# -----------------------------------------------------------------------------"
SRC_FILE = Path("./src/tarpitd.py")
DOCS_FOLDER = Path("./docs")
MANPAGES = ["tarpitd.py.1", "tarpitd.py.7"]
WRAP_WIDTH = 70

def reformat_markdown(text: str) -> str:
    """
    Reformat markdown text by merging paragraphs and wrapping text,
    while keeping code blocks (lines starting with two or more spaces) intact.
    """
    lines = text.splitlines()
    buffer: List[str] = []
    result: List[str] = []
    
    for line in lines:
        # Check for code block (line that starts with two spaces)
        if re.match(r'^ {2}', line):
            if buffer:
                result.append(_process_paragraph(buffer))
                buffer = []
            result.append(line.rstrip())
        elif not line.strip():
            # Empty line: flush buffered paragraph
            if buffer:
                result.append(_process_paragraph(buffer))
                buffer = []
            result.append('')
        else:
            # Regular text: strip and buffer
            buffer.append(line.strip())
    
    # Process any remaining buffered text
    if buffer:
        result.append(_process_paragraph(buffer))
    
    return _clean_extra_newlines(result)

def _process_paragraph(lines: List[str]) -> str:
    """Merge the buffered lines and wrap the text to a fixed width."""
    merged = re.sub(r'\s+', ' ', ' '.join(lines).strip())
    return "\n".join(textwrap.wrap(merged,
                                   width=WRAP_WIDTH,
                                   break_long_words=False,
                                   replace_whitespace=False))

def _clean_extra_newlines(segments: List[str]) -> str:
    """Remove multiple consecutive empty lines."""
    cleaned = []
    prev_empty = False
    for segment in segments:
        if segment == '':
            # Append an empty line only if the previous segment wasn't empty
            if not prev_empty:
                cleaned.append(segment)
                prev_empty = True
        else:
            cleaned.append(segment)
            prev_empty = False
    return "\n".join(cleaned).strip()

def update_manual_section(content: str, manual_name: str, new_md: str) -> str:
    """
    Finds the section for the manual in the content and replaces the content between the markers.
    """
    try:
        # Locate the first DOC_WRAP and then manual name and DOC_START and get the start index
        wrap_index = content.index(DOC_WRAP)
        manual_index = content.index(manual_name, wrap_index)
        start = content.index(DOC_START, manual_index) + len(DOC_START)
        end = content.index(DOC_WRAP, start)
    except ValueError as e:
        raise ValueError(f"Could not find the appropriate tags for manual '{manual_name}': {e}")

    # Format the new manual definition, preserving the surrounding markers
    manual_var = f"_MANUAL_{manual_name.upper().replace('.', '_')}"
    new_section = f'\n{manual_var} = r""" \n{new_md}\n"""\n'
    return content[:start] + new_section + content[end:]

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
            md_raw = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            continue

        new_md = reformat_markdown(md_raw)

        try:
            content = update_manual_section(content, manual_name, new_md)
        except ValueError as e:
            print(e)
            continue

        print(f"Updated section for manual '{manual_name}'.")

    # Write updated content back to the file
    try:
        SRC_FILE.write_text(content, encoding="utf-8")
        print("File updated successfully")
    except Exception as e:
        print(f"Error writing to {SRC_FILE}: {e}")

if __name__ == "__main__":
    main()