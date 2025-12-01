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
  hotelId,
  roomNumber,
  openDrawer,
  setOpenDrawer,
  occupancy
}) {


  return (
    <SwipeableDrawer
      anchor="right"
      open={openDrawer}
      onClose={() => setOpenDrawer(false)}
      style={{
        height: "100vh",
      }}
    >
      <Box sx={{ p: 2, flexShrink: 0 }}>
        <button
          className="bg-black text-white w-20 py-2 ml-auto rounded-md"
          onClick={() => setOpenDrawer(false)}
        >
          CLOSE
        </button>
      </Box>
      <Box
        sx={{
          height: "100vh",
        }}
      >
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
                alt={`${occupancy ? "occupied" : "unoccupied"} room`}
                src={occupancy ? closedDoor : openDoor}
                style={{ width: 40, height: 40 }}
              />
              <Typography variant="body2">
                {occupancy ? "Occupied" : "Unoccupied"}
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
              hotelId={hotelId}
              roomId={roomNumber}
            />
            <TemperatureControl
              hotelId={hotelId}
              roomId={roomNumber}
            />
          </Box>
        </Box>
      </Box>
    </SwipeableDrawer>
  );
}
