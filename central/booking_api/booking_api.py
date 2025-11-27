from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pymongo import MongoClient
import os, hashlib

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
DB_NAME = os.getenv("MONGO_DB", "hotel_db")

uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{DB_NAME}?authSource=admin"
client = MongoClient(uri)
db = client[DB_NAME]

app = FastAPI()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class User(BaseModel):
    username: str
    password: str
    role: str
@app.get("/api/signin")
def sign_in(request: User):
        # Find user by username
    user = db.users.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Verify password
    if user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"user_id": str(user["_id"]), "role": user["role"]}  
@app.get("/api/getroom/{userid}")
def get_user_room(userid):
    # get the room id from the booking db based on the user id
    room_id = db.bookings.find_one({"user_id": userid})["room_id"]
    if not room_id:
        raise HTTPException(status_code=401, detail="User doesn't exist") 
    room_info = db.rooms.find_one({"room_id" : room_id})
    if not room_info:
        raise HTTPException(status_code=401, detail="User doesn't exist") 
    return {
        "number": room_info["number"],
        "hotel_id": room_info["hotel_id"],
        "status": room_info["status"]
    }
    