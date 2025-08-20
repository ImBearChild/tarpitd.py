#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# type: ignore

"""
Usage examples:
1) Read from a file and print the snippet:
   python split_string_for_source.py --input-file long.txt --width 80

2) Read from clipboard (requires pyperclip):
   python split_string_for_source.py --clipboard --width 80

3) Specify variable name and output file:
   python split_string_for_source.py -i long.txt -n long_text -o snippet.py

The script produces code like:
long_text = (
    "segment one"
    "segment two"
    ...
)
"""

import argparse
import sys

try:
    import pyperclip 
except Exception:
    pyperclip = None

def escape_segment(s, quote_char='"'):
    # Escape backslashes and the chosen quote character,
    # and replace real newlines with \n so the generated
    # adjacent literals do not create actual line breaks.
    s = s.replace('\\', '\\\\')
    if quote_char == '"':
        s = s.replace('"', '\\"')
    else:
        s = s.replace("'", "\\'")
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    return s

def split_to_segments(text, width):
    # Simple fixed-width split by characters.
    # If you prefer splitting on word boundaries, replace this logic.
    segments = []
    i = 0
    n = len(text)
    while i < n:
        seg = text[i:i+width]
        segments.append(seg)
        i += width
    return segments

def build_snippet(var_name, segments, quote_char='"', indent='    '):
    # Build the Python snippet with adjacent string literals inside parentheses.
    lines = []
    header = f"{var_name} = ("
    lines.append(header)
    for seg in segments:
        esc = escape_segment(seg, quote_char=quote_char)
        lines.append(f"{indent}{quote_char}{esc}{quote_char}")
    lines.append(")")
    return "\n".join(lines)

def read_input_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    p = argparse.ArgumentParser(description="Split a long string into adjacent Python string literals")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-file", "-i", help="input text file containing the long string")
    group.add_argument("--clipboard", "-c", action="store_true", help="read input from clipboard (requires pyperclip)")
    group.add_argument("--stdin", action="store_true", help="read input from standard input")
    p.add_argument("--width", "-w", type=int, default=80, help="maximum characters per segment (default 80)")
    p.add_argument("--var-name", "-n", default="long_text", help="variable name for the generated snippet (default: long_text)")
    p.add_argument("--quote", choices=['"', "'"], default='"', help='quote character to use (default: ")')
    p.add_argument("--indent", default="    ", help="indentation for each segment line (default 4 spaces)")
    p.add_argument("--output-file", "-o", help="write the generated code to a file (otherwise stdout)")

    args = p.parse_args()

    if args.clipboard:
        if pyperclip is None:
            print("Error: pyperclip is not installed. Install it or use --input-file.", file=sys.stderr)
            sys.exit(2)
        text = pyperclip.paste()
    elif args.stdin:
        text = sys.stdin.read()
    else:
        text = read_input_from_file(args.input_file)

    if text is None:
        text = ""

    segments = split_to_segments(text, args.width)
    snippet = build_snippet(args.var_name, segments, quote_char=args.quote, indent=args.indent)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(snippet)
        print(f"Wrote snippet to {args.output_file}")
    else:
        # Print to stdout. If in a terminal, just print.
        print(snippet)

if __name__ == "__main__":
    main()
