from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import os
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_sample_data():
    today = datetime.now()

    MONGO_USER = os.getenv("MONGO_USER", "admin")
    MONGO_PASS = os.getenv("MONGO_PASS", "1Password")
    MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
    DB_NAME = os.getenv("MONGO_DB", "hotel_db")

    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}?authSource=admin"
    # change to a while loop with a break   
    while True:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            print("Connected to MongoDB")
            break
        except Exception:
            print(f"MongoDB not ready, retrying...")
            time.sleep(5)

    db = client[DB_NAME]

    # Sample data
    rooms_data = [
    {"room_id": "101", "hotel_id": "hotel_01", "status": "booked", "room_type": "normal"},
    {"room_id": "102", "hotel_id": "hotel_01", "status": "booked", "room_type": "premium"},
    {"room_id": "201", "hotel_id": "hotel_02", "status": "available", "room_type": "vip"},
    {"room_id": "202", "hotel_id": "hotel_02", "status": "booked", "room_type": "normal"},
]


    bookings_data = [
    {
        "user_id": "U001",
        "room_id": "101",
        "hotel_id": "hotel_01",
        "date_in": today - timedelta(days=1),
        "date_out": today + timedelta(days=2),
    },
    {
        "user_id": "U002",
        "room_id": "102",
        "hotel_id": "hotel_01",
        "date_in": today + timedelta(days=2),
        "date_out": today + timedelta(days=5),
    },
    {
        "user_id": "U003",
        "room_id": "201",
        "hotel_id": "hotel_02",
        "date_in": today - timedelta(days=5),
        "date_out": today - timedelta(days=2),
    },
    {
        "user_id": "U004",
        "room_id": "202",
        "hotel_id": "hotel_02",
        "date_in": today - timedelta(days=1),
        "date_out": today + timedelta(days=1),
    },
]

    hotel_data = [
        {"hotel_id": "hotel_01", "name": "Grand Plaza", "location": "Dublin"},
        {"hotel_id": "hotel_02", "name": "Sea View Resort", "location": "Cork"},      
    ]

    users_data = [
        {"user_id": "U001", "username": "john_doe", "password_hash": hash_password("1Password"), "role": "customer"},
        {"user_id": "U002", "username": "jane_smith", "password_hash": hash_password("1Password"), "role": "customer"},
        {"user_id": "A001", "username": "admin", "password_hash": hash_password("1Password"), "role": "admin"},
        {"user_id": "A002", "username": "manager1", "password_hash": hash_password("1Password"), "role": "hotel_manager"},
    ]

    # Insert sample data if collections are empty
    if db.rooms.count_documents({}) == 0:
        db.rooms.insert_many(rooms_data)
        print("Loaded sample rooms")

    if db.bookings.count_documents({}) == 0:
        db.bookings.insert_many(bookings_data)
        print("Loaded sample bookings")

    if db.users.count_documents({}) == 0:
        db.users.insert_many(users_data)
        print("Loaded sample users")

    if db.hotels.count_documents({}) == 0:
        db.hotels.insert_many(hotel_data)
        print("Loaded sample hotels")
