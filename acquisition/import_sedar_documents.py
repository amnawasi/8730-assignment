import os
import json
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "smartcentres"
COLLECTION_NAME = "sedar_documents"

def main():
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found. Did you create a .env file?")

    file_path = "data/processed/sedar/sedar_documents.json"
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = data if isinstance(data, list) else [data]

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Clear old data so re-running doesn't duplicate
        collection.delete_many({})

        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents into {DB_NAME}.{COLLECTION_NAME}")

        count = collection.count_documents({})
        print(f"Verification: collection now has {count} documents")
    except FileNotFoundError:
        print(f"Import failed: file not found at {file_path}")
    except json.JSONDecodeError as error:
        print(f"Import failed: invalid JSON file. {error}")
    except PyMongoError as error:
        print(f"MongoDB connection or import failed: {error}")
    finally:
        client.close()

if __name__ == "__main__":
    main()