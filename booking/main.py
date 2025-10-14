import uvicorn
from fastapi import FastAPI
import api.rooms_api as rooms_api_mod
import api.property_api as property_api_mod

# Import the two apps defined in the repository



app = FastAPI(title="Combined Booking Mock APIs")

# Mount the two existing FastAPI apps at their root paths
app.mount("/property-api", property_api_mod.app)
app.mount("/rooms-api", rooms_api_mod.app)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Run with: python booking/main.py or better: uvicorn booking.main:app --reload
    uvicorn.run("booking.main:app", host="0.0.0.0", port=8000, log_level="info")
