import os
import uuid
from fastapi import FastAPI, HTTPException, Header, Body
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

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

app = FastAPI(title="Booking.com Mock Property API with MongoDB")

# ------------------------------
# Models
# ------------------------------

class Position(BaseModel):
    latitude: float
    longitude: float

class CheckIn(BaseModel):
    from_: str
    until: Optional[str] = None
    class Config:
        fields = {"from_": "from"}

class CheckOut(BaseModel):
    from_: Optional[str] = None
    until: Optional[str] = None
    class Config:
        fields = {"from_": "from"}

class PhysicalAddress(BaseModel):
    city_name: str
    country_code: str
    postal_code: Optional[str]
    address_line: str
    display_address: Optional[bool] = True

class Translation(BaseModel):
    city_name: str
    address_line: str
    language_code: str
    property_name: str

class PropertyRequest(BaseModel):
    position: Position
    check_in: CheckIn
    check_out: Optional[CheckOut]
    property_name: str
    property_category: Optional[int]
    booking_property_category: Optional[int]
    primary_language: Optional[str] = "en-gb"
    languages_spoken: Optional[List[str]]
    room_count: int
    floor_count: Optional[int]
    stars: Optional[str]
    target: str
    provider_property_id: Optional[str]
    currency_code: Optional[str]
    physical_address: PhysicalAddress
    translations: Optional[List[Translation]]
    legal_entity_id: int

# ------------------------------
# Property status rules
# ------------------------------

FORBIDDEN_STATUSES = {
    "ready_to_check",
    "ready_to_open",
    "closed_post_legal",
    "closed_forever",
    "duplicate"
}

RESTRICTED_FIELDS = {
    "currency_code",
    "primary_language",
    "physical_address",
    "city_name",
    "country_code",
    "postal_code",
    "address_line"
}

# ------------------------------
# Endpoints
# ------------------------------

@app.post("/property-api/properties")
async def create_property(body: PropertyRequest, content_type: str = Header(...), accept_version: Optional[str] = Header(None)):
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    property_id = str(uuid.uuid4())
    property_doc = body.dict()
    property_doc["property_id"] = property_id
    property_doc["status"] = "test_hotel"  # default mock status

    await db.properties.insert_one(property_doc)

    return {
        "data": {"property_id": property_id},
        "warnings": [],
        "meta": {"ruid": str(uuid.uuid4())}
    }

@app.patch("/property-api/properties/{property_id}")
async def update_property(property_id: str, body: Dict[str, Any], accept_version: Optional[str] = Header(None)):
    # Fetch property
    property_doc = await db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")

    status = property_doc.get("status", "test_hotel")

    # forbid updates in some statuses
    if status in FORBIDDEN_STATUSES:
        raise HTTPException(status_code=403, detail=f"Property cannot be updated in status: {status}")

    # restrict certain fields
    if status not in ["test_hotel", "being_built"]:
        for field in body.keys():
            if field in RESTRICTED_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' can only be updated if property is in Test Hotel or Being Built status"
                )

    # handle null → unset
    set_ops = {k: v for k, v in body.items() if v is not None}
    unset_ops = {k: "" for k, v in body.items() if v is None}

    update_query = {}
    if set_ops:
        update_query["$set"] = set_ops
    if unset_ops:
        update_query["$unset"] = unset_ops

    if update_query:
        await db.properties.update_one({"property_id": property_id}, update_query)

    return {
        "data": {"property_id": property_id},
        "warnings": [],
        "meta": {"ruid": str(uuid.uuid4())}
    }

@app.get("/property-api/properties/{property_id}")
async def get_property(property_id: str, accept_version: Optional[str] = Header(None)):
    property_doc = await db.properties.find_one({"property_id": property_id}, {"_id": 0})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")

    return {
        "data": property_doc,
        "meta": {"ruid": str(uuid.uuid4())}
    }

@app.post("/property-api/properties/{property_id}/settings")
async def set_property_settings(property_id: str, body: dict):
    property_doc = await db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    await db.property_settings.update_one(
        {"property_id": property_id},
        {"$set": {"settings": body}},
        upsert=True
    )
    return {"data": body, "meta": {"ruid": str(uuid.uuid4())}}

@app.get("/property-api/properties/{property_id}/settings")
async def get_property_settings(property_id: str):
    settings_doc = await db.property_settings.find_one({"property_id": property_id}, {"_id": 0})
    if not settings_doc:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"data": settings_doc.get("settings", {}), "meta": {"ruid": str(uuid.uuid4())}}

# ----------------------------------
# Property status transitions
# ----------------------------------

@app.post("/property-api/properties/{property_id}/status")
async def update_property_status(
    property_id: str,
    body: Dict[str, Any] = Body(...),
    content_type: str = Header(...),
):
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    property_doc = await db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")

    operation = body.get("operation")
    if not operation:
        raise HTTPException(status_code=400, detail="Missing 'operation' field")

    current_status = property_doc.get("status", "test_hotel")
    warnings, errors = [], []
    new_status = current_status

    # -------------------------------
    # Handle Check
    # -------------------------------
    if operation == "Check":
        # Mock: randomize outcome (or you can base on property fields)
        # Here we simulate always passing but add a warning if no stars
        if not property_doc.get("stars"):
            warnings.append({
                "message": "Missing stars",
                "code": 100,
                "description": "Property has no star rating"
            })
        if not property_doc.get("room_count"):
            errors.append({
                "message": "Invalid value",
                "code": 320,
                "description": "Property must have at least one room"
            })

        if errors:
            status_msg = "One or more checks have failed, please check the error array, resolve and try again."
        else:
            status_msg = "Checks have passed, property may now be opened."

        return {
            "data": {"status": status_msg},
            "warnings": warnings,
            "errors": errors,
            "meta": {"ruid": str(uuid.uuid4())}
        }

    # -------------------------------
    # Handle Open
    # -------------------------------
    elif operation == "Open":
        # all valid transitions go to "Open / bookable"
        new_status = "Open / bookable"
        await db.properties.update_one({"property_id": property_id}, {"$set": {"status": new_status}})
        return {
            "data": {"status": f"Property {property_id} is in {new_status} status"},
            "warnings": [],
            "errors": [],
            "meta": {"ruid": str(uuid.uuid4())}
        }

    # -------------------------------
    # Handle Close
    # -------------------------------
    elif operation == "Close":
        reason = body.get("reason", {})
        reason_type = reason.get("type")

        # Transition logic
        if current_status == "XML: Ready to check":
            new_status = "XML: Being built"
        elif current_status in ["XML: Ready to open", "Open / bookable", "Auto closed (availability)", "Closed - ready to reopen"]:
            new_status = "Closed (requested by hotel)"
        elif current_status == "XML: Auto closed content":
            new_status = "XML: Auto closed content"
        else:
            new_status = "Closed (requested by hotel)"

        await db.properties.update_one({"property_id": property_id}, {"$set": {"status": new_status}})

        return {
            "data": {"status": f"Property {property_id} is in {new_status} status"},
            "warnings": [],
            "errors": [],
            "meta": {"ruid": str(uuid.uuid4())}
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported operation: {operation}")