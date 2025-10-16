from pymongo import MongoClient
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os


load_dotenv()


MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST", 'localhost')
MONGO_PORT = os.getenv("MONGO_PORT", 27017)
DB_NAME = os.getenv("MONGO_DB")

time.sleep(5)

uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}?authSource=admin"

max_retries = 10
for attempt in range(max_retries):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info() 
        print("Connected to MongoDB")
        break
    except Exception:
        print(f"MongoDB not ready, retrying... ({attempt+1}/{max_retries})")
        time.sleep(5)
else:
    raise Exception("Could not connect to MongoDB after multiple attempts")


db = client[DB_NAME]


rooms_data = [
    {"number": 101, "hotel_id": "H001", "status": "available"},
    {"number": 102, "hotel_id": "H001", "status": "booked"},
    {"number": 201, "hotel_id": "H002", "status": "available"},
    {"number": 202, "hotel_id": "H002", "status": "booked"},
]

bookings_data = [
    {
        "user_id": "U001",
        "room_id": "R102",
        "hotel_id": "H001",
        "date_in": datetime(2025, 10, 18),
        "date_out": datetime(2025, 10, 20),
    },
    {
        "user_id": "U002",
        "room_id": "R202",
        "hotel_id": "H002",
        "date_in": datetime(2025, 10, 22),
        "date_out": datetime(2025, 10, 25),
    },
]

if db.rooms.count_documents({}) == 0:
    db.rooms.insert_many(rooms_data)
    print("Loaded sample rooms")

if db.bookings.count_documents({}) == 0:
    db.bookings.insert_many(bookings_data)
    print("Loaded sample bookings")