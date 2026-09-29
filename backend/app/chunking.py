import re


def _split_long_text(
    text: str,
    chunk_size: int,
    overlap: int
) -> list[str]:
    chunks = []

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text)
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(
            r"\n\s*\n",
            text
        )
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = re.sub(
            r"[ \t]+",
            " ",
            paragraph
        )

        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(
                _split_long_text(
                    paragraph,
                    chunk_size,
                    overlap
                )
            )

            continue

        candidate = (
            f"{current_chunk}\n\n{paragraph}"
            if current_chunk
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        chunks.append(current_chunk)

        overlap_text = (
            current_chunk[-overlap:].strip()
            if overlap
            else ""
        )

        candidate = (
            f"{overlap_text}\n\n{paragraph}"
            if overlap_text
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks