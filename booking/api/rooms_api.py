import uuid
import os
from fastapi import FastAPI, Query, Header, HTTPException, Body
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

# ------------------------------
# Pydantic Models
# ------------------------------
class UnitName(BaseModel):
    unit_name_id: int
    unit_name: str

class BedType(BaseModel):
    bed_type_id: int
    bed_type_name: str
    bed_type_description1: str
    bed_type_description_imperial1: str
    is_active: bool

class PropertyCategory(BaseModel):
    code: int
    name: str
    code_ota: int
    code_booking_extended: int

class UnitType(BaseModel):
    unit_type_id: int
    unit_type_name: str
    is_multi_room: bool
    is_active: bool
    valid_property_categories: List[int]
    suggested_unit_names: List[UnitName]

class Bed(BaseModel):
    bed_type_id: int
    count: int = 1

class Room(BaseModel):
    room_name: str
    beds: List[Bed] = []

class UnitBase(BaseModel):
    unit_type_id: int
    unit_name: str
    rooms: List[Room]
    max_occupancy: int
    max_adults: int
    max_children: int
    
class UnitCreate(UnitBase):
    pass

class Unit(UnitBase):
    unit_id: str
    property_id: str

    class Config:
        schema_extra = {
            "example": {
                "unit_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "property_id": "123456",
                "unit_type_id": 1,
                "unit_name": "Apartment",
                "rooms": [
                    {
                        "room_name": "Bedroom",
                        "beds": [
                            {"bed_type_id": 1, "count": 2}
                        ]
                    }
                ],
                "max_occupancy": 2,
                "max_adults": 2,
                "max_children": 0
            }
        }

# ------------------------------
# Mongo Configuration
# ------------------------------
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb") or "mongodb"
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "bookings")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

if MONGO_USER:
    mongo_url = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
else:
    mongo_url = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"

client = AsyncIOMotorClient(mongo_url)
db = client[MONGO_DB]

app = FastAPI(title="Booking.com Mock Rooms API with MongoDB")

# ------------------------------
# Seed data (only once)
# ------------------------------
SEED_UNIT_TYPES = [
    {
        "unit_type_id": 1,
        "unit_type_name": "Apartment",
        "is_multi_room": True,
        "is_active": True,
        "valid_property_categories": [201, 202, 204, 205],
        "suggested_unit_names": [
            {"unit_name_id": 9, "unit_name": "Apartment"},
            {"unit_name_id": 41, "unit_name": "Apartment with Balcony"},
        ]
    },
    {
        "unit_type_id": 2,
        "unit_type_name": "Studio",
        "is_multi_room": False,
        "is_active": True,
        "valid_property_categories": [201, 202],
        "suggested_unit_names": [
            {"unit_name_id": 44, "unit_name": "Studio Apartment"},
            {"unit_name_id": 45, "unit_name": "Studio with Sea View"},
        ]
    },
]

SEED_UNIT_NAMES = [
    {"unit_name_id": 9, "unit_name": "Apartment"},
    {"unit_name_id": 41, "unit_name": "Apartment with Balcony"},
    {"unit_name_id": 44, "unit_name": "Studio Apartment"},
    {"unit_name_id": 45, "unit_name": "Studio with Sea View"},
]

SEED_BED_TYPES = [
    {
        "bed_type_id": 1,
        "bed_type_name": "Single bed",
        "bed_type_description1": "90–130 cm wide",
        "bed_type_description_imperial1": "35–51 inches wide",
        "is_active": True
    },
    {
        "bed_type_id": 2,
        "bed_type_name": "Double bed",
        "bed_type_description1": "131–150 cm wide",
        "bed_type_description_imperial1": "52–59 inches wide",
        "is_active": True
    },
]

SEED_PROPERTY_CATEGORIES = [
    {"code": 201, "name": "Apartment", "code_ota": 1001, "code_booking_extended": 2001},
    {"code": 202, "name": "Studio", "code_ota": 1002, "code_booking_extended": 2002},
    {"code": 204, "name": "Villa", "code_ota": 1003, "code_booking_extended": 2003},
]

@app.on_event("startup")
async def seed_meta_data():
    if await db.unit_types.count_documents({}) == 0:
        await db.unit_types.insert_many(SEED_UNIT_TYPES)
    if await db.unit_names.count_documents({}) == 0:
        await db.unit_names.insert_many(SEED_UNIT_NAMES)
    if await db.bed_types.count_documents({}) == 0:
        await db.bed_types.insert_many(SEED_BED_TYPES)
    if await db.property_categories.count_documents({}) == 0:
        await db.property_categories.insert_many(SEED_PROPERTY_CATEGORIES)

# ------------------------------
# Endpoint: Retrieve units metadata
# ------------------------------
class MetaResponse(BaseModel):
    language_code: str
    unit_types: List[UnitType]
    unit_names: List[UnitName]
    bed_types: List[BedType]
    property_categories: List[PropertyCategory]

@app.get("/rooms-api/meta")
async def get_units_meta(
    language_code: Optional[str] = Query("EN_GB"),
    show_inactive: bool = Query(True),
    accept_version: Optional[str] = Header(None)
):
    # Fetch data from DB
    unit_types_data = await db.unit_types.find().to_list(None)
    bed_types_data = await db.bed_types.find().to_list(None)
    unit_names_data = await db.unit_names.find().to_list(None)
    property_categories_data = await db.property_categories.find().to_list(None)

    # Apply filters
    if not show_inactive:
        unit_types_data = [u for u in unit_types_data if u.get("is_active", False)]
        bed_types_data = [b for b in bed_types_data if b.get("is_active", False)]

    # Convert to Pydantic models
    unit_types = [UnitType(**u) for u in unit_types_data]
    bed_types = [BedType(**b) for b in bed_types_data]
    unit_names = [UnitName(**n) for n in unit_names_data]
    property_categories = [PropertyCategory(**p) for p in property_categories_data]

    return {
        "data": MetaResponse(
            language_code=language_code,
            unit_types=unit_types,
            unit_names=unit_names,
            bed_types=bed_types,
            property_categories=property_categories
        ),
        "meta": {"ruid": str(uuid.uuid4())}
    }

# ----------------------------------
# Create Unit (Room) for Property
# ----------------------------------
@app.post("/rooms-api/properties/{property_id}/units")
async def create_unit(
    property_id: str,
    unit_data: UnitCreate = Body(...),
    content_type: str = Header(...),
    accept_version: Optional[str] = Header(None)
):
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    # Validate: property must exist
    property_doc = await db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")

    # Generate a unit_id
    unit_id = str(uuid.uuid4())

    # Create Unit object
    unit = Unit(
        unit_id=unit_id,
        property_id=property_id,
        **unit_data.dict()
    )

    # Store in Mongo
    await db.units.insert_one(unit.dict())

    # Response matches Booking.com format
    return {
        "data": unit,
        "warnings": [],
        "errors": [],
        "meta": {"ruid": str(uuid.uuid4())}
    }
async def update_property(
        property_id: str,
        unit_data: UnitCreate = Body(...),
        content_type: str = Header(...),
        accept_version: Optional[str] = Header(None)
    ):
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    # Validate: property must exist
    property_doc = await db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update the property
    await db.properties.update_one({"property_id": property_id}, {"$set": unit_data.dict()})

    return {
        "data": unit_data,
        "warnings": [],
        "errors": [],
        "meta": {"ruid": str(uuid.uuid4())}
    }