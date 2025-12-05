import Box from "@mui/material/Box";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Divider from "@mui/material/Divider";
import Typography from "@mui/material/Typography";
import LightControl from "../../pages/light-control";
import TemperatureControl from "../../pages/temp-control";
import openDoor from "../../assets/open-door.png";
import closedDoor from "../../assets/closed-door.png";
import MetricChart from "../MetricChart/metricChart";

const RoomInfoDrawer = ({
  hotelId,
  roomNumber,
  openDrawer,
  setOpenDrawer,
  occupancy, // "available" | "occupied" | "booked"
}) => {
  if (!roomNumber) return null; // don't render if no room is selected

  const isOccupied = occupancy === "occupied" || occupancy === "booked";
  const doorIcon = isOccupied ? closedDoor : openDoor;

  return (
    <SwipeableDrawer
      anchor="right"
      open={openDrawer}
      onClose={() => setOpenDrawer(false)}
      onOpen={() => {}}
      transitionDuration={250}
    >
      <Box
        sx={{
          width: "70vw",
          maxWidth: 800,
          height: "100vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Close button */}
        <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
          <button
            className="bg-black text-white w-20 py-2 rounded-md"
            onClick={() => setOpenDrawer(false)}
          >
            CLOSE
          </button>
        </Box>

        <Box sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Room Information
          </Typography>

          <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 4, mt: 1, mx: 10,}}>
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
                alt={`${occupancy} room`}
                src={doorIcon}
                style={{ width: 40, height: 40 }}
              />
              <Typography variant="body2">
                {occupancy.charAt(0).toUpperCase() + occupancy.slice(1)}
              </Typography>
            </Box>
          </Box>
        </Box>

        <Divider />

        <Box sx={{ p: 3, flexGrow: 1 }}>
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
            <LightControl hotelId={hotelId} roomId={roomNumber} />
            <TemperatureControl hotelId={hotelId} roomId={roomNumber} />
              <MetricChart hotelId={hotelId} room={roomNumber} metric={"light-state_brightness"} metric_title={"Brightness"}/>
              <MetricChart hotelId={hotelId} room={roomNumber} metric={"temperature_temperatureC"} metric_title={"Temperature"}/>
               <MetricChart hotelId={hotelId} room={roomNumber} metric={"light-status_mode"} metric_title={"Light Status"}/>
              
          </Box>
        </Box>
      </Box>
    </SwipeableDrawer>
  );
};

export default RoomInfoDrawer;
