import fitz

from app.chunking import chunk_text


def extract_pages(pdf_path: str):
    """
    Extract text from a PDF page by page.
    """

    document = fitz.open(pdf_path)

    pages = []

    try:
        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text")

            if text.strip():
                pages.append({
                    "page_number": page_number,
                    "text": text
                })

    finally:
        document.close()

    return pages


def create_chunks_from_pdf(pdf_path: str):
    """
    Extract PDF text and split every page into chunks.
    """

    pages = extract_pages(pdf_path)

    chunks = []

    for page in pages:

        page_chunks = chunk_text(
            page["text"],
            chunk_size=1000,
            overlap=200
        )

        for chunk in page_chunks:

            chunks.append({
                "page_number": page["page_number"],
                "content": chunk
            })

    return chunks