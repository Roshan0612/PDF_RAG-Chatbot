import re

from app.tokenization import (
    count_tokens,
    decode_tokens,
    encode_tokens
)


def _split_long_text(
    text: str,
    chunk_size: int,
    overlap: int
) -> list[str]:
    tokens = encode_tokens(text)

    chunks = []

    start = 0

    while start < len(tokens):
        end = min(
            start + chunk_size,
            len(tokens)
        )

        chunk_tokens = tokens[start:end]

        chunk = decode_tokens(
            chunk_tokens
        ).strip()

        if chunk:
            chunks.append(chunk)

        if end == len(tokens):
            break

        start = end - overlap

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80
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

        paragraph_tokens = count_tokens(
            paragraph
        )

        if paragraph_tokens > chunk_size:
            if current_chunk:
                chunks.append(
                    current_chunk
                )

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

        if count_tokens(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        chunks.append(
            current_chunk
        )

        if overlap:
            current_tokens = encode_tokens(
                current_chunk
            )

            overlap_text = decode_tokens(
                current_tokens[-overlap:]
            ).strip()
        else:
            overlap_text = ""

        candidate = (
            f"{overlap_text}\n\n{paragraph}"
            if overlap_text
            else paragraph
        )

        if count_tokens(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            current_chunk = paragraph

    if current_chunk:
        chunks.append(
            current_chunk
        )

    return chunks