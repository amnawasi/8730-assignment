import os
import pymysql
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ---------- MySQL (structured data) ----------
print("=== MySQL ===")
try:
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    print("Tables in MySQL:")
    for t in tables:
        print("  -", t[0])
    conn.close()
except Exception as e:
    print("MySQL error:", e)

# ---------- MongoDB (unstructured data) ----------
print("\n=== MongoDB ===")
try:
    client = MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
    db = client["smartcentres"]
    print("Collections in MongoDB:")
    for name in db.list_collection_names():
        count = db[name].count_documents({})
        print(f"  - {name} ({count} docs)")
    client.close()
except Exception as e:
    print("MongoDB error:", e)