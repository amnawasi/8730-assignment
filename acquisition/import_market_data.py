"""
acquisition/import_market_data.py

Imports processed fundamentals and news data into MongoDB Atlas.
Same pattern as import_investor_documents.py and import_sedar_documents.py.
"""

import os
import json
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "smartcentres"


def import_collection(client, db_name, collection_name, file_path, is_list):
    db = client[db_name]
    collection = db[collection_name]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = data if is_list else [data]

    collection.delete_many({})
    result = collection.insert_many(documents)
    print(f"Inserted {len(result.inserted_ids)} document(s) into {db_name}.{collection_name}")

    count = collection.count_documents({})
    print(f"Verification: {collection_name} now has {count} document(s)")


def main():
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found. Did you create a .env file?")

    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    try:
        import_collection(
            client, DB_NAME, "fundamentals",
            "data/processed/smartcentres/fundamentals_clean.json", is_list=False
        )
        import_collection(
            client, DB_NAME, "news_headlines",
            "data/processed/smartcentres/news_clean.json", is_list=True
        )
    except FileNotFoundError as error:
        print(f"Import failed: file not found. {error}")
    except json.JSONDecodeError as error:
        print(f"Import failed: invalid JSON file. {error}")
    except PyMongoError as error:
        print(f"MongoDB connection or import failed: {error}")
    finally:
        client.close()


if __name__ == "__main__":
    main()