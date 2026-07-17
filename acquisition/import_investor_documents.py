import json
import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "smartcentres"
COLLECTION_NAME = "investor_documents"


def main() -> None:
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found. Did you create a .env file?")

    file_path = "data/processed/smartcentres/investor_documents.json"
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        documents = data if isinstance(data, list) else [data]

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        existing_count = collection.count_documents({})
        if existing_count > 0:
            print(f"Collection already has {existing_count} documents - clearing before re-import")
            collection.delete_many({})

        result = collection.insert_many(documents)
        print(
            f"Inserted {len(result.inserted_ids)} documents "
            f"into {DB_NAME}.{COLLECTION_NAME}"
        )

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