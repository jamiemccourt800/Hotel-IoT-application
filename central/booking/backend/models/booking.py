from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class BookingModel(BaseModel):
    user_id: str
    room_id: str
    hotel_id: str
    date_in: datetime
    date_out: datetime