from __future__ import annotations

import json
import re
from pathlib import Path

import fitz  # PyMuPDF


INPUT_FOLDER = Path("data/raw/smartcentres")
OUTPUT_FILE = Path(
    "data/processed/smartcentres/investor_documents.json"
)

START_YEAR = 2020
END_YEAR = 2026

# Only prioritize documents directly related to investment analysis.
IMPORTANT_KEYWORDS = (
    "annual-report",
    "quarter",
    "q1",
    "q2",
    "q3",
    "q4",
    "aif",
    "esg-report",
    "press-release",
)


def clean_text(text: str) -> str:
    """Clean repeated whitespace from extracted PDF text."""
    return re.sub(r"\s+", " ", text).strip()


def extract_year(filename: str) -> int | None:
    """Extract a year between 2020 and 2026 from the filename."""
    matches = re.findall(r"\b(202[0-6])\b", filename)

    if not matches:
        return None

    return int(matches[0])


def infer_doc_type(filename: str) -> str:
    """Infer a basic document type from the filename."""
    name = filename.lower()

    if "annual-report" in name:
        return "annual_report"
    if "aif" in name:
        return "annual_information_form"
    if "esg" in name:
        return "esg_report"
    if "quarter" in name or re.search(r"\bq[1-4]\b", name):
        return "quarterly_report"
    if "press-release" in name or "release" in name:
        return "press_release"

    return "investor_document"


def is_relevant_pdf(pdf_path: Path) -> bool:
    """Keep only important English investment documents."""
    name = pdf_path.name.lower()

    if "french" in name or "-fr-" in name or name.endswith("-fr.pdf"):
        return False

    return any(keyword in name for keyword in IMPORTANT_KEYWORDS)


def extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    """Extract text from every page of one PDF."""
    page_texts: list[str] = []

    with fitz.open(pdf_path) as document:
        for page in document:
            page_texts.append(page.get_text("text"))

        page_count = document.page_count

    return clean_text(" ".join(page_texts)), page_count


def build_documents() -> list[dict]:
    """Convert selected PDFs into MongoDB-ready JSON documents."""
    documents: list[dict] = []

    for pdf_path in sorted(INPUT_FOLDER.glob("*.pdf")):
        if not is_relevant_pdf(pdf_path):
            continue

        year = extract_year(pdf_path.name)

        if year is not None and not START_YEAR <= year <= END_YEAR:
            continue

        try:
            text, page_count = extract_pdf_text(pdf_path)
        except Exception as error:
            print(f"Skipped {pdf_path.name}: {error}")
            continue

        if not text:
            print(f"Skipped empty-text PDF: {pdf_path.name}")
            continue

        document = {
            "company_id": "smartcentres",
            "source": "smartcentres.com",
            "doc_type": infer_doc_type(pdf_path.name),
            "title": pdf_path.stem.replace("-", " "),
            "document_year": year,
            "filename": pdf_path.name,
            "page_count": page_count,
            "text_length": len(text),
            "text": text,
        }

        documents.append(document)
        print(
            f"Processed: {pdf_path.name} "
            f"({page_count} pages, {len(text)} characters)"
        )

    return documents


def save_json(documents: list[dict]) -> None:
    """Save all documents into one JSON file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    documents = build_documents()
    save_json(documents)

    print(f"\nCreated {len(documents)} JSON documents.")
    print(f"Saved to: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()