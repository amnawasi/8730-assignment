"""
BSMM-8730 — Smart Centres REIT Analysis
Script: MongoDB Document Validation
Author: Muhammad Ahmad
Role: Member C — Data Validation
Date: July 2026

What this script does:
- Connects to the existing MongoDB collections (no new collections created)
- Validates sedar_documents and investor_documents in place
- Checks for:
    1. Duplicate filenames
    2. document_year outside the 2020-2026 range
    3. Suspiciously short text_length (sign of failed extraction)
    4. company_id consistently "smartcentres"
- Fixes any problems found directly in the existing collections
- Prints a full validation report
"""

import re
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ============================================================
# SETTINGS
# ============================================================

MONGO_URI = "mongodb+srv://usman:MongoFix2026@cluster0.ectjwst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME             = "smartcentres"
COLLECTIONS         = ["sedar_documents", "investor_documents"]
MIN_YEAR            = 2020
MAX_YEAR            = 2026
MIN_TEXT_LENGTH     = 500
EXPECTED_COMPANY_ID = "smartcentres"


# ============================================================
# STEP 1 — Connect to MongoDB
# ============================================================

def connect_to_mongodb(uri):
    """
    Connects to MongoDB Atlas using certifi for TLS.
    certifi fix prevents NetworkTimeout errors on some machines.
    """
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    print(f"Connected! Using database: {DB_NAME}")
    print()
    return client, db


# ============================================================
# STEP 2 — Extract Year from Filename
# ============================================================

def extract_year_from_filename(filename):
    if not filename:
        return None
    match = re.search(r"(20\d{2})", str(filename))
    if match:
        return int(match.group(1))
    return None


# ============================================================
# STEP 3 — Validate a Single Collection
# ============================================================

def validate_collection(db, collection_name):
    print("=" * 60)
    print(f"VALIDATING: {collection_name}")
    print("=" * 60)

    collection = db[collection_name]
    docs       = list(collection.find())
    total      = len(docs)

    print(f"Total documents: {total}")
    print()

    # Each check uses its OWN counter
    # so PASS always prints correctly regardless of other checks

    # --------------------------------------------------------
    # CHECK 1 — Duplicate filenames
    # --------------------------------------------------------
    print("CHECK 1: Duplicate filenames")
    seen_filenames = {}
    check1_found   = 0
    check1_fixed   = 0

    for doc in docs:
        filename = doc.get("filename", "")
        doc_id   = doc["_id"]
        if filename in seen_filenames:
            print(f"  FOUND — Duplicate: {filename} — removing")
            collection.delete_one({"_id": doc_id})
            check1_found += 1
            check1_fixed += 1
        else:
            seen_filenames[filename] = doc_id

    if check1_found == 0:
        print("  PASS — No duplicate filenames found.")
    else:
        print(f"  FIXED {check1_fixed}/{check1_found} duplicates.")
    print()

    # Reload after removing duplicates
    docs = list(collection.find())

    # --------------------------------------------------------
    # CHECK 2 — document_year outside 2020-2026 range
    # --------------------------------------------------------
    print(f"CHECK 2: document_year outside {MIN_YEAR}-{MAX_YEAR} range")
    check2_found = 0
    check2_fixed = 0

    for doc in docs:
        doc_year = doc.get("document_year")
        filename = doc.get("filename", "")
        doc_id   = doc["_id"]

        if doc_year is None:
            extracted = extract_year_from_filename(filename)
            if extracted:
                collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"document_year": extracted}}
                )
                print(f"  FIXED — {filename}: set document_year to {extracted}")
                check2_found += 1
                check2_fixed += 1
            else:
                print(f"  WARNING — {filename}: document_year is null, could not extract")
                check2_found += 1

        elif not (MIN_YEAR <= int(doc_year) <= MAX_YEAR):
            print(f"  WARNING — {filename}: document_year {doc_year} out of range")
            check2_found += 1

    if check2_found == 0:
        print(f"  PASS — All document_year values are within {MIN_YEAR}-{MAX_YEAR}.")
    else:
        print(f"  Fixed {check2_fixed}/{check2_found} year issues.")
    print()

    # --------------------------------------------------------
    # CHECK 3 — Suspiciously short text_length
    # --------------------------------------------------------
    print(f"CHECK 3: text_length below {MIN_TEXT_LENGTH} characters")
    check3_found = 0

    for doc in docs:
        text_length   = doc.get("text_length", 0)
        actual_length = len(doc.get("text", "") or "")
        filename      = doc.get("filename", "")

        if text_length < MIN_TEXT_LENGTH or actual_length < MIN_TEXT_LENGTH:
            print(f"  WARNING — {filename}: stored={text_length}, actual={actual_length}")
            print(f"    This may indicate a failed PDF extraction.")
            check3_found += 1

    if check3_found == 0:
        print(f"  PASS — All documents have sufficient text (>{MIN_TEXT_LENGTH} chars).")
    print()

    # --------------------------------------------------------
    # CHECK 4 — company_id consistently "smartcentres"
    # --------------------------------------------------------
    print(f'CHECK 4: company_id consistently "{EXPECTED_COMPANY_ID}"')
    check4_found = 0
    check4_fixed = 0

    for doc in docs:
        company_id = doc.get("company_id", "")
        filename   = doc.get("filename", "")
        doc_id     = doc["_id"]

        if company_id != EXPECTED_COMPANY_ID:
            collection.update_one(
                {"_id": doc_id},
                {"$set": {"company_id": EXPECTED_COMPANY_ID}}
            )
            print(f"  FIXED — {filename}: '{company_id}' to '{EXPECTED_COMPANY_ID}'")
            check4_found += 1
            check4_fixed += 1

    if check4_found == 0:
        print(f'  PASS — All documents have company_id = "{EXPECTED_COMPANY_ID}".')
    print()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------
    total_found = check1_found + check2_found + check3_found + check4_found
    total_fixed = check1_fixed + check2_fixed + check4_fixed

    print(f"Summary for {collection_name}:")
    print(f"  Total documents  : {total}")
    print(f"  Issues found     : {total_found}")
    print(f"  Issues fixed     : {total_fixed}")
    print(f"  Issues remaining : {total_found - total_fixed}")
    print()

    return {
        "collection"  : collection_name,
        "total"       : total,
        "issues_found": total_found,
        "issues_fixed": total_fixed
    }


# ============================================================
# STEP 4 — Final Report
# ============================================================

def print_final_report(results):
    print("=" * 60)
    print("FINAL VALIDATION REPORT")
    print("=" * 60)
    print()

    total_found = 0
    total_fixed = 0

    for r in results:
        print(f"Collection      : {r['collection']}")
        print(f"  Documents     : {r['total']}")
        print(f"  Issues found  : {r['issues_found']}")
        print(f"  Issues fixed  : {r['issues_fixed']}")
        print()
        total_found += r["issues_found"]
        total_fixed += r["issues_fixed"]

    remaining = total_found - total_fixed
    print(f"TOTAL ISSUES FOUND : {total_found}")
    print(f"TOTAL ISSUES FIXED : {total_fixed}")
    print(f"REMAINING ISSUES   : {remaining}")
    print()

    if total_found == 0:
        print("No issues found. Existing cleaning was already sufficient.")
    elif remaining == 0:
        print("All issues found were fixed successfully.")
    else:
        print(f"WARNING: {remaining} issue(s) could not be fixed automatically.")
        print("Manual review recommended.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("BSMM-8730 — MongoDB Validation Script")
    print("Author : Muhammad Ahmad")
    print("Date   : July 2026")
    print("=" * 60)
    print()

    client = None
    try:
        client, db = connect_to_mongodb(MONGO_URI)

        results = []
        for collection_name in COLLECTIONS:
            result = validate_collection(db, collection_name)
            results.append(result)

        print_final_report(results)

    except PyMongoError as e:
        print(f"MongoDB connection error: {e}")
        print("Check your internet connection and try again.")

    finally:
        if client:
            client.close()
            print()
            print("MongoDB connection closed.")
