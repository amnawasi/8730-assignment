"""
BSMM-8730 — Smart Centres REIT Analysis
Script: MongoDB Document Cleaning
Author: Muhammad Ahmad
Role: Member C — Data Cleaning (Usman and Eric's MongoDB data)
Date: July 2026

What this script does:
- Connects to MongoDB Atlas
- Reads raw documents from sedar_documents and investor_documents collections
- Cleans the data:
    - Extracts missing document_year from filename
    - Standardizes field names across both collections
    - Removes extra whitespace and line breaks from text
    - Removes repeated headers and footers
    - Handles missing values
    - Removes duplicate documents
- Saves cleaned documents into new cleaned collections
- Prints a full summary report

Collections read from:
- sedar_documents      (Usman and Eric's SEDAR+ data)
- investor_documents   (Usman and Eric's investor doc data)

Collections written to:
- sedar_documents_cleaned
- investor_documents_cleaned
"""

import re
import os
from pymongo import MongoClient
from datetime import datetime

# ============================================================
# SETTINGS
# ============================================================

MONGO_URI = "mongodb+srv://usman:MongoFix2026@cluster0.ectjwst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME = "smartcentres"

# Source collections (raw data — never modify these)
SEDAR_RAW     = "sedar_documents"
INVESTOR_RAW  = "investor_documents"

# Target collections (cleaned data)
SEDAR_CLEAN   = "sedar_documents_cleaned"
INVESTOR_CLEAN = "investor_documents_cleaned"


# ============================================================
# STEP 1 — Connect to MongoDB Atlas
# ============================================================

def connect_to_mongodb(uri):
    """
    Connects to MongoDB Atlas and returns the database object.
    Prints a confirmation message.
    """
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(uri)
    db = client[DB_NAME]
    print(f"Connected! Using database: {DB_NAME}")
    print()
    return db


# ============================================================
# STEP 2 — TOC Stripping Function
# ============================================================

def strip_table_of_contents(text):
    """
    Strips the jumbled table of contents block that appears at the
    start of SEDAR PDF documents.

    The TOC is a one-time block per document — not a repeated header —
    so it cannot be caught by the repeated pattern removal.

    It looks like a run of section headings and page numbers with no
    real sentence structure before the actual MD&A content begins.

    Strategy:
    - Search for known anchor phrases that mark the START of real content
    - Slice the text from that position onward
    - This works even when the text has no clear line breaks
    """
    if not text or not isinstance(text, str):
        return text

    # Known anchor phrases that mark the START of real content
    # in SEDAR MD&A documents — these are the first real sentences
    # after the jumbled TOC block
    content_anchors = [
        "This Management's Discussion and Analysis",
        "This MD&A should be read",
        "sets out SmartCentres",
        "MANAGEMENT'S DISCUSSION AND ANALYSIS FOR THE YEAR",
        "MANAGEMENT'S DISCUSSION AND ANALYSIS FOR THE THREE",
        "About this Management's Discussion",
    ]

    best_position = len(text)  # Start with end of text as default

    for anchor in content_anchors:
        pos = text.find(anchor)
        if pos != -1 and pos < best_position:
            best_position = pos

    # If we found an anchor before 20% into the text, strip before it
    threshold = len(text) * 0.20
    if best_position < threshold and best_position > 0:
        chars_removed = best_position
        print(f"    TOC stripped: removed {chars_removed} characters from the start")
        return text[best_position:]

    # If no anchor found near the start, return text unchanged
    print(f"    TOC strip: no TOC detected, text unchanged")
    return text


# ============================================================
# STEP 3 — Text Cleaning Function
# ============================================================

def clean_text(text, strip_toc=False):
    """
    Cleans raw PDF-extracted text by:
    - Optionally stripping the table of contents (for SEDAR docs)
    - Removing extra whitespace and blank lines
    - Removing repeated headers and footers (page numbers, report titles)
    - Stripping leading and trailing whitespace
    """
    if not text or not isinstance(text, str):
        return ""

    # Strip TOC block if requested (SEDAR documents only)
    if strip_toc:
        text = strip_table_of_contents(text)

    # Remove repeated headers and footers commonly found in SEDAR PDF extractions
    # These are phrases that appear on almost every page
    repeated_patterns = [
        r"MANAGEMENT'S DISCUSSION AND ANALYSIS\s*\n",
        r"SMARTCENTRES REAL ESTATE INVESTMENT TRUST\s*\|.*?REPORT\s*\d+",
        r"Page \d+ of \d+",
        r"^\s*\d+\s*$",   # Standalone page numbers
    ]
    for pattern in repeated_patterns:
        text = re.sub(pattern, " ", text, flags=re.MULTILINE | re.IGNORECASE)

    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Replace more than 2 consecutive newlines with 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading and trailing whitespace
    text = text.strip()

    return text


# ============================================================
# STEP 3 — Extract Year from Filename
# ============================================================

def extract_year_from_filename(filename):
    """
    Tries to extract a 4-digit year from the filename.
    Example: '2024_annual_mda_english.pdf' → 2024
    Returns None if no year found.
    """
    if not filename:
        return None

    match = re.search(r"(20\d{2})", filename)
    if match:
        return int(match.group(1))

    return None


# ============================================================
# STEP 4 — Check for Missing Values
# ============================================================

def check_missing(doc, required_fields):
    """
    Checks a document for missing or null required fields.
    Returns a list of field names that are missing.
    """
    missing = []
    for field in required_fields:
        if field not in doc or doc[field] is None or doc[field] == "":
            missing.append(field)
    return missing


# ============================================================
# STEP 5 — Clean SEDAR Documents
# ============================================================

def clean_sedar_documents(db):
    """
    Reads from sedar_documents (raw),
    cleans each document,
    and inserts into sedar_documents_cleaned.
    """
    print("=" * 60)
    print("CLEANING: sedar_documents")
    print("=" * 60)

    raw_collection   = db[SEDAR_RAW]
    clean_collection = db[SEDAR_CLEAN]

    # Drop the clean collection first for a fresh start
    clean_collection.drop()
    print(f"Dropped existing collection: {SEDAR_CLEAN}")

    raw_docs  = list(raw_collection.find())
    total     = len(raw_docs)
    print(f"Found {total} raw documents to clean.")
    print()

    cleaned_count  = 0
    skipped_count  = 0
    seen_filenames = set()   # For duplicate detection

    for i, doc in enumerate(raw_docs):
        print(f"  Processing document {i + 1}/{total}: {doc.get('filename', 'unknown')}")

        # --- Duplicate check ---
        filename = doc.get("filename", "")
        if filename in seen_filenames:
            print(f"    SKIPPED — duplicate filename: {filename}")
            skipped_count += 1
            continue
        seen_filenames.add(filename)

        # --- Fix document_year if null ---
        doc_year = doc.get("document_year")
        if doc_year is None:
            doc_year = extract_year_from_filename(filename)
            if doc_year:
                print(f"    Fixed document_year: extracted {doc_year} from filename")
            else:
                print(f"    WARNING: Could not extract year from filename: {filename}")

        # --- Clean the text ---
        # strip_toc=True removes the jumbled TOC block at the start of SEDAR docs
        raw_text    = doc.get("text", "")
        clean_text_ = clean_text(raw_text, strip_toc=True)

        # --- Check for missing required fields ---
        required = ["company_id", "source", "filename", "text"]
        missing  = check_missing(doc, required)
        if missing:
            print(f"    WARNING: Missing fields: {missing}")

        # --- Build the cleaned document ---
        # Standardize field names to match investor_documents structure
        cleaned_doc = {
            "company_id"    : doc.get("company_id"),
            "company_name"  : doc.get("company_name"),
            "source"        : doc.get("source"),
            "doc_type"      : doc.get("document_type"),   # Renamed to match investor_documents
            "document_year" : doc_year,
            "filename"      : filename,
            "page_count"    : doc.get("page_count"),
            "text_length"   : len(clean_text_),           # Updated after cleaning
            "text"          : clean_text_,
            "cleaned_at"    : datetime.utcnow().isoformat(),
            "cleaned_by"    : "Muhammad Ahmad"
        }

        # --- Insert into clean collection ---
        clean_collection.insert_one(cleaned_doc)
        cleaned_count += 1
        print(f"    Cleaned and saved. Text length: {len(raw_text)} → {len(clean_text_)} chars")

    print()
    print(f"SEDAR Documents Summary:")
    print(f"  Total raw     : {total}")
    print(f"  Cleaned       : {cleaned_count}")
    print(f"  Skipped (dups): {skipped_count}")
    print()


# ============================================================
# STEP 6 — Clean Investor Documents
# ============================================================

def clean_investor_documents(db):
    """
    Reads from investor_documents (raw),
    cleans each document,
    and inserts into investor_documents_cleaned.
    """
    print("=" * 60)
    print("CLEANING: investor_documents")
    print("=" * 60)

    raw_collection   = db[INVESTOR_RAW]
    clean_collection = db[INVESTOR_CLEAN]

    # Drop the clean collection first for a fresh start
    clean_collection.drop()
    print(f"Dropped existing collection: {INVESTOR_CLEAN}")

    raw_docs  = list(raw_collection.find())
    total     = len(raw_docs)
    print(f"Found {total} raw documents to clean.")
    print()

    cleaned_count  = 0
    skipped_count  = 0
    seen_filenames = set()

    for i, doc in enumerate(raw_docs):
        print(f"  Processing document {i + 1}/{total}: {doc.get('filename', 'unknown')}")

        # --- Duplicate check ---
        filename = doc.get("filename", "")
        if filename in seen_filenames:
            print(f"    SKIPPED — duplicate filename: {filename}")
            skipped_count += 1
            continue
        seen_filenames.add(filename)

        # --- Fix document_year if missing ---
        doc_year = doc.get("document_year")
        if doc_year is None:
            doc_year = extract_year_from_filename(filename)
            if doc_year:
                print(f"    Fixed document_year: extracted {doc_year} from filename")

        # --- Clean the text ---
        raw_text    = doc.get("text", "")
        clean_text_ = clean_text(raw_text)

        # --- Check for missing required fields ---
        required = ["company_id", "source", "filename", "text"]
        missing  = check_missing(doc, required)
        if missing:
            print(f"    WARNING: Missing fields: {missing}")

        # --- Build the cleaned document ---
        cleaned_doc = {
            "company_id"    : doc.get("company_id"),
            "source"        : doc.get("source"),
            "doc_type"      : doc.get("doc_type"),
            "title"         : doc.get("title"),
            "document_year" : doc_year,
            "filename"      : filename,
            "page_count"    : doc.get("page_count"),
            "text_length"   : len(clean_text_),
            "text"          : clean_text_,
            "cleaned_at"    : datetime.utcnow().isoformat(),
            "cleaned_by"    : "Muhammad Ahmad"
        }

        # --- Insert into clean collection ---
        clean_collection.insert_one(cleaned_doc)
        cleaned_count += 1
        print(f"    Cleaned and saved. Text length: {len(raw_text)} → {len(clean_text_)} chars")

    print()
    print(f"Investor Documents Summary:")
    print(f"  Total raw     : {total}")
    print(f"  Cleaned       : {cleaned_count}")
    print(f"  Skipped (dups): {skipped_count}")
    print()


# ============================================================
# STEP 7 — Final Verification
# ============================================================

def verify_cleaned_collections(db):
    """
    Prints a summary of what was saved in the cleaned collections.
    Confirms everything looks correct before finishing.
    """
    print("=" * 60)
    print("VERIFICATION: Cleaned Collections")
    print("=" * 60)

    for collection_name in [SEDAR_CLEAN, INVESTOR_CLEAN]:
        collection = db[collection_name]
        docs = list(collection.find())
        print(f"\nCollection: {collection_name}")
        print(f"  Total documents: {len(docs)}")

        for doc in docs:
            print(f"\n  Document: {doc.get('filename', 'unknown')}")
            print(f"    company_id    : {doc.get('company_id')}")
            print(f"    source        : {doc.get('source')}")
            print(f"    doc_type      : {doc.get('doc_type')}")
            print(f"    document_year : {doc.get('document_year')}")
            print(f"    page_count    : {doc.get('page_count')}")
            print(f"    text_length   : {doc.get('text_length')}")
            print(f"    cleaned_at    : {doc.get('cleaned_at')}")
            print(f"    cleaned_by    : {doc.get('cleaned_by')}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("BSMM-8730 — MongoDB Data Cleaning")
    print("Author : Muhammad Ahmad")
    print("Date   : July 2026")
    print("=" * 60)
    print()

    # Connect to MongoDB
    db = connect_to_mongodb(MONGO_URI)

    # Clean both collections
    clean_sedar_documents(db)
    clean_investor_documents(db)

    # Verify results
    verify_cleaned_collections(db)

    print()
    print("=" * 60)
    print("Done! MongoDB cleaning complete.")
    print("Cleaned collections:")
    print(f"  - {SEDAR_CLEAN}")
    print(f"  - {INVESTOR_CLEAN}")
    print("=" * 60)
