from pydantic import BaseModel, Field
from typing import Optional, Literal

class RoomModel(BaseModel):
    number: int
    hotel_id: str
    status: Literal['booked', 'available']