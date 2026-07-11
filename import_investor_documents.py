import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "smartcentres"
COLLECTION_NAME = "investor_documents"

def main():
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found. Did you create a .env file?")

    file_path = "data/processed/smartcentres/investor_documents.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = data if isinstance(data, list) else [data]

    client = MongoClient(MONGO_URI)
    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Clear old data so re-running doesn't duplicate
        collection.delete_many({})

        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents into {DB_NAME}.{COLLECTION_NAME}")

        count = collection.count_documents({})
        print(f"Verification: collection now has {count} documents")
    finally:
        client.close()

if __name__ == "__main__":
    main()