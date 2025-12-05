from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pymongo import MongoClient
import os, hashlib
from sample_data import load_sample_data


MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASS = os.getenv("MONGO_PASS", "1Password")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
DB_NAME = os.getenv("MONGO_DB", "hotel_db")

uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class User(BaseModel):
    username: str
    password: str

@app.on_event("startup")
def startup_event():
    try:
        client.admin.command("ping")
        print("Mongo connected")
    except Exception as e:
        print("Mongo connection failed:", e)

    load_sample_data()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": db.name,
        "collections": db.list_collection_names(),
    }

@app.post("/api/signin")
def sign_in(request: User):
    user = db.users.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")

    if user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"user_id": user["user_id"], "role": user["role"]}

@app.get("/api/getroom/{userid}")
def get_user_room(userid):
    booking = db.bookings.find_one({"user_id": userid})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    room = db.rooms.find_one({"room_id": booking["room_id"]})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return {
        "room_id": room["room_id"],
        "room_type": room["room_type"],
        "hotel_id": room["hotel_id"],
        "status": room["status"],
    }


@app.get("/api/get_hotels")
def get_hotels():
    hotels = db.hotels.find()
    return {"hotels": [
        {"hotel_id": h["hotel_id"], "name": h["name"], "location": h["location"]}
        for h in hotels
    ]}


@app.get("/api/get_rooms/{hotel_id}")
def get_rooms(hotel_id: str):
    current_date = datetime.now()

    rooms_cursor = db.rooms.find({"hotel_id": hotel_id})
    rooms = []
    print(rooms_cursor)
    for room in rooms_cursor:
        room_status = room["status"]

        active_booking = db.bookings.find_one({
            "room_id": room["room_id"],
            "date_in": {"$lte": current_date},
            "date_out": {"$gte": current_date}
        })

        if active_booking:
            room_status = "occupied"

        rooms.append({
            "room_id": room["room_id"],
            "status": room_status
        })

    return {"rooms": rooms}
