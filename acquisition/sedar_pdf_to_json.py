"""
acquisition/sedar_pdf_to_json.py

Parses SEDAR+ MD&A filings into MongoDB-ready JSON documents.

Note: SEDAR+ has no public API, so the source PDFs in data/raw/sedar/
were downloaded manually from https://www.sedarplus.ca (SmartCentres REIT
profile), rather than pulled by a script. This is a known, expected
limitation of this source - documented in the group's data source plan.

Documents used (manually retrieved, July 2026):
- SmartCentres Annual MD&A, fiscal year 2024
- SmartCentres Annual MD&A, fiscal year 2025
- SmartCentres Q1 2026 Interim MD&A
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz  # PyMuPDF

INPUT_FOLDER = Path("data/raw/sedar")
OUTPUT_FILE = Path("data/processed/sedar/sedar_documents.json")


def clean_text(text: str) -> str:
    """Remove repeated whitespace from extracted PDF text."""
    return re.sub(r"\s+", " ", text).strip()


def extract_year(filename: str) -> int | None:
    """Extract a four-digit year from the filename."""
    match = re.search(r"\b(20\d{2})\b", filename)
    return int(match.group(1)) if match else None


def infer_document_type(filename: str) -> str:
    """Infer the SEDAR+ document type from its filename."""
    name = filename.lower()
    if "annual_mda" in name:
        return "annual_mda"
    if "interim_mda" in name:
        return "interim_mda"
    return "sedar_document"


def extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    """Extract text and page count from one PDF."""
    page_texts: list[str] = []
    with fitz.open(pdf_path) as document:
        for page in document:
            page_texts.append(page.get_text("text"))
        page_count = document.page_count
    return clean_text(" ".join(page_texts)), page_count


def build_documents() -> list[dict]:
    """Convert all local SEDAR+ PDFs into MongoDB-ready documents."""
    pdf_files = sorted(INPUT_FOLDER.glob("*.pdf"))
    if not pdf_files:
        print(f"WARNING: no PDF files found in {INPUT_FOLDER} - did you run the acquisition step first?")

    documents: list[dict] = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
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
            "company_name": "SmartCentres Real Estate Investment Trust",
            "source": "SEDAR+",
            "document_type": infer_document_type(pdf_path.name),
            "document_year": extract_year(pdf_path.name),
            "filename": pdf_path.name,
            "page_count": page_count,
            "text_length": len(text),
            "text": text,
        }
        documents.append(document)
    return documents


def main() -> None:
    documents = build_documents()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)
    print(f"\nCreated {len(documents)} documents")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()