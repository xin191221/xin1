import re
import io

import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from all pages of a PDF file."""
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def clean_resume_text(raw_text: str) -> str:
    """Clean and structure extracted resume text."""
    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^[^\w一-鿿]+$", "", text, flags=re.MULTILINE)
    text = text.strip()
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text


def parse_resume(file_bytes: bytes) -> tuple[str, str]:
    """Parse PDF and return (raw_text, cleaned_text)."""
    raw = extract_text_from_pdf(file_bytes)
    cleaned = clean_resume_text(raw)
    return raw, cleaned
