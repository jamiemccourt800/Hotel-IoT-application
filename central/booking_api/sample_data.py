from pymongo import MongoClient
from datetime import datetime
import time
import os
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_sample_data():
    MONGO_USER = os.getenv("MONGO_USER", "admin")
    MONGO_PASS = os.getenv("MONGO_PASS", "1Password")
    MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
    DB_NAME = os.getenv("MONGO_DB", "hotel_db")

    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}?authSource=admin"

    # Wait for Mongo to be ready
    max_retries = 10
    for attempt in range(max_retries):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            print("Connected to MongoDB")
            break
        except Exception:
            print(f"MongoDB not ready, retrying ({attempt+1}/{max_retries})...")
            time.sleep(5)
    else:
        raise Exception("Could not connect to MongoDB after multiple attempts")

    db = client[DB_NAME]

    # Sample data
    rooms_data = [
        {"number": "101", "hotel_id": "hotel_01", "status": "available"},
        {"number": "102", "hotel_id": "hotel_01", "status": "booked"},
        {"number": "201", "hotel_id": "hotel_02", "status": "available"},
        {"number": "202", "hotel_id": "hotel_02", "status": "booked"},
    ]

    bookings_data = [
        {"user_id": "U001", "room_id": "101", "hotel_id": "hotel_01", "date_in": datetime(2025,10,18), "date_out": datetime(2025,10,20)},
        {"user_id": "U002", "room_id": "101", "hotel_id": "hotel_01", "date_in": datetime(2025,10,22), "date_out": datetime(2025,10,25)},
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
