# libs/cast/query/src/casting/cast/query/rag/chunking.py
from __future__ import annotations
import re
from typing import List


_HEADING_RE = re.compile(r"(?m)^(?P<h>#{1,6})\s+(?P<text>.+?)\s*$")


def split_by_headings(md_body: str, max_chars: int) -> List[str]:
    """
    Split Markdown by headings (# .. ######) into chunks <= max_chars.
    If a chunk still exceeds max_chars, we fall back to paragraph splitting.
    """
    text = md_body or ""
    # Identify headings and their spans
    positions = [(m.start(), m.group(0)) for m in _HEADING_RE.finditer(text)]
    sections: List[str] = []

    if not positions:
        # No headings — paragraph fallback
        return split_by_paragraphs(text, max_chars)

    # Build coarse sections per heading
    starts = [pos for pos, _ in positions] + [len(text)]
    for i in range(len(starts) - 1):
        chunk = text[starts[i]: starts[i + 1]].strip()
        if chunk:
            sections.append(chunk)

    # Merge small ones + split large ones
    out: List[str] = []
    buf = ""
    for section in sections:
        if len(section) > max_chars:
            # Flush buffer
            if buf:
                out.append(buf)
                buf = ""
            # Split this large section further
            out.extend(split_by_paragraphs(section, max_chars))
            continue
        # Try to accumulate
        if len(buf) + len(section) + 2 <= max_chars:
            buf = f"{buf}\n\n{section}" if buf else section
        else:
            if buf:
                out.append(buf)
            buf = section
    if buf:
        out.append(buf)
    return out


def split_by_paragraphs(text: str, max_chars: int) -> List[str]:
    """Greedy paragraph splitter to respect max_chars."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    if not paras:
        return [text[:max_chars]] if text else []

    out: List[str] = []
    buf = ""
    for p in paras:
        if len(p) > max_chars:
            # Hard cut long paragraph
            while p:
                out.append(p[:max_chars])
                p = p[max_chars:]
            continue
        if len(buf) + len(p) + 2 <= max_chars:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                out.append(buf)
            buf = p
    if buf:
        out.append(buf)
    return out