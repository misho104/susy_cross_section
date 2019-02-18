#!env python3

import pathlib
import re
import sys

re_doubled_cite = re.compile(r'\\cite\{(.*?)\}\\cite\{(.*?)\}')


def finalize(text):
    doubled_cite_match = re_doubled_cite.search(text)
    if doubled_cite_match:
        text = re_doubled_cite.sub(r'\\cite{\1,\2}', text)
        text = finalize(text)
    return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [TEX_FILE]", file=sys.stderr)
        exit(1)

    target = pathlib.Path(sys.argv[1])
    text = target.read_text()
    target.write_text(finalize(text))
    exit(0)
