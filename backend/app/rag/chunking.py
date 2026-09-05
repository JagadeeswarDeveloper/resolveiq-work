"""Policy-aware text chunking."""

import re


def chunk_document(text: str, max_chars: int = 700) -> list[dict]:
    """Split on sections first, then bounded paragraphs without losing headings."""
    sections = re.split(r"\n\s*\n", text.strip())
    chunks = []
    for index, section in enumerate(sections):
        cleaned = " ".join(section.split())
        if not cleaned:
            continue
        heading_match = re.match(r"^([^:]{2,80}):\s*(.*)$", cleaned)
        heading = heading_match.group(1) if heading_match else f"Section {index + 1}"
        body = heading_match.group(2) if heading_match else cleaned
        for offset in range(0, len(body), max_chars):
            content = body[offset:offset + max_chars].strip()
            if content:
                chunks.append({"content": content, "section": heading})
    return chunks
