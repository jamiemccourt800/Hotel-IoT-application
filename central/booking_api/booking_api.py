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

uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}?authSource=admin"

client = MongoClient(uri)
db = client[DB_NAME]
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    load_sample_data()

@app.get("/health")
def health_check():
    return {"status": "ok", "connected to db": db.name, "uri": uri, "databases": db.list_collection_names()}


@app.post("/api/signin")
def sign_in(request: User):
        # Find user by username
    user = db.users.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")

    # Verify password
    if user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"user_id": str(user["user_id"]), "role": user["role"]}  

@app.get("/api/getroom/{userid}")
def get_user_room(userid):
    booking = db.bookings.find_one({"user_id": userid})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    room_info = db.rooms.find_one({"room_id": booking["room_id"]})
    if not room_info:
        raise HTTPException(status_code=404, detail="Room not found")

    return {
        "room_id": room_info["room_id"],
        "hotel_id": room_info["hotel_id"],
        "status": room_info["status"],
    }

@app.get("/api/get_hotels")
def get_hotels():
    hotels = db.hotels.find()
    hotel_list = []
    for hotel in hotels:
        hotel_list.append({
            "hotel_id": hotel["hotel_id"],
            "name": hotel["name"],
            "location": hotel["location"]
        })
    return {"hotels": hotel_list}

@app.get("/api/get_rooms/{hotel_id}")
def get_rooms(hotel_id: str):
    rooms = db.rooms.find({"hotel_id": hotel_id})
    room_list = []
    for room in rooms:
        room_list.append({
            "room_id": room["room_id"],
            "status": room["status"]
        })
    # room should show occupied if current date is between any booking date_in and date_out
    current_date = datetime.now()
    for room in room_list:
        booking = db.bookings.find_one({"room_id": room["room_id"]})
        if booking:
            if booking["date_in"] <= current_date <= booking["date_out"]:
                room["status"] = "occupied"
    return {"rooms": room_list}