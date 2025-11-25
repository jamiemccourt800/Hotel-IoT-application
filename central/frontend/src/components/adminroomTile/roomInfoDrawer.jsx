import React, { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Divider from "@mui/material/Divider";
import Typography from "@mui/material/Typography";

import LightControl from "../../pages/light-control";
import TemperatureControl from "../../pages/temp-control";
import openDoor from "../../assets/open-door.png";
import closedDoor from "../../assets/closed-door.png";

export default function RoomInfoDrawer({
  hotelId = 1,
  roomNumber = 101,
  openDrawer,
  setOpenDrawer,
}) {
  const [roomData, setRoomData] = useState({ occupancy: false });

  useEffect(() => {
    async function fetchRoomData() {
      try {
        const res = await fetch(`/api/hotels/${hotelId}/rooms/${roomNumber}`);
        const data = await res.json();
        setRoomData(data);
      } catch (err) {
        console.error("Failed to fetch room data", err);
      }
    }
    if (openDrawer) fetchRoomData();
  }, [hotelId, roomNumber]);

  const list = () => (
    <Box sx={{ width: 800, bgcolor: "background.default", height: "100%" }}>
      {/* Room Info */}
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Room Information
        </Typography>

        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 4,
            mt: 1,
            mx: 10,
          }}
        >
          <Box>
            <Typography fontWeight="bold">Hotel</Typography>
            <Typography>{hotelId}</Typography>
          </Box>

          <Box>
            <Typography fontWeight="bold">Room</Typography>
            <Typography>{roomNumber}</Typography>
          </Box>

          <Box sx={{ textAlign: "center" }}>
            <img
              alt={`${roomData?.occupancy ? "occupied" : "unoccupied"} room`}
              src={roomData?.occupancy ? closedDoor : openDoor}
              style={{ width: 40, height: 40 }}
            />
            <Typography variant="body2">
              {roomData?.occupancy ? "Occupied" : "Unoccupied"}
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider />

      {/* Controls */}
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Controls
        </Typography>
        <Box
          sx={{
            display: "flex",
            gap: 4,
            flexWrap: "wrap",
            justifyContent: "center",
            mt: 1,
          }}
        >
          <LightControl
            isOn={roomData?.lightOn}
            onToggle={(newState) => console.log("Light toggled:", newState)}
          />
          <TemperatureControl
            value={roomData?.temperature}
            onChange={(val) => console.log("Temperature changed:", val)}
          />
        </Box>
      </Box>
    </Box>
  );

  return (
    <div>
      <SwipeableDrawer anchor="right" open={openDrawer}>
        <button
          className="bg-black text-white w-20 py-2 m-4 ml-auto rounded-md"
          onClick={() => setOpenDrawer(false)}
        >
          CLOSE
        </button>
        {list()}
      </SwipeableDrawer>
    </div>
  );
}
