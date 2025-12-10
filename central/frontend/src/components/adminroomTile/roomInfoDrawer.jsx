import { useState } from "react";
import Box from "@mui/material/Box";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Typography from "@mui/material/Typography";
import LightControl from "../../pages/light-control";
import TemperatureControl from "../../pages/temp-control";
import openDoor from "../../assets/open-door.png";
import closedDoor from "../../assets/closed-door.png";
import MetricChart from "../MetricChart/metricChart";
import HumidityControl from "../../pages/humidityControl";

const RoomInfoDrawer = ({
  hotelId,
  roomNumber,
  openDrawer,
  setOpenDrawer,
  occupancy,
}) => {
  const [activeTab, setActiveTab] = useState("light");

  if (!roomNumber) return null;

  const isOccupied = occupancy === "occupied" || occupancy === "booked";
  const doorIcon = isOccupied ? closedDoor : openDoor;

  const getStatusColor = () => {
    if (occupancy === "occupied") return "#8C8CED";
    if (occupancy === "booked") return "#6B6BD4";
    return "#4ADE80";
  };

  const tabs = [
    { id: "light", label: "Light", icon: "💡" },
    { id: "temperature", label: "Temperature", icon: "🌡️" },
    { id: "humidity", label: "Humidity", icon: "💧" },
  ];

  return (
    <SwipeableDrawer
      anchor="right"
      open={openDrawer}
      onClose={() => setOpenDrawer(false)}
      onOpen={() => {}}
      transitionDuration={250}
      PaperProps={{
        sx: {
          backgroundColor: "#0A0A0A",
          width: "70vw",
          maxWidth: 1200,
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 3,
          borderBottom: "2px solid rgba(140, 140, 237, 0.3)",
          backgroundColor: "#0A0A0A",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h5"
          sx={{
            color: "white",
            fontWeight: 600,
          }}
        >
          Room Information
        </Typography>

        <button
          onClick={() => setOpenDrawer(false)}
          style={{
            backgroundColor: "white",
            color: "#0A0A0A",
            padding: "10px 24px",
            borderRadius: "8px",
            fontWeight: 600,
            border: "none",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = "#8C8CED";
            e.target.style.color = "white";
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = "white";
            e.target.style.color = "#0A0A0A";
          }}
        >
          CLOSE
        </button>
      </Box>

      {/* Room Info Card */}
      <Box sx={{ p: 3, backgroundColor: "#0A0A0A" }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-around",
            alignItems: "center",
            backgroundColor: "#1A1A1A",
            borderRadius: "12px",
            p: 3,
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <Box sx={{ textAlign: "center" }}>
            <Typography
              sx={{
                color: "rgba(255, 255, 255, 0.6)",
                fontSize: "0.875rem",
                mb: 1,
              }}
            >
              Hotel
            </Typography>
            <Typography sx={{ color: "white", fontSize: "1.125rem", fontWeight: 600 }}>
              {hotelId}
            </Typography>
          </Box>

          <Box
            sx={{
              width: "1px",
              height: "50px",
              backgroundColor: "rgba(255, 255, 255, 0.1)",
            }}
          />

          <Box sx={{ textAlign: "center" }}>
            <Typography
              sx={{
                color: "rgba(255, 255, 255, 0.6)",
                fontSize: "0.875rem",
                mb: 1,
              }}
            >
              Room
            </Typography>
            <Typography sx={{ color: "white", fontSize: "1.125rem", fontWeight: 600 }}>
              {roomNumber}
            </Typography>
          </Box>

          <Box
            sx={{
              width: "1px",
              height: "50px",
              backgroundColor: "rgba(255, 255, 255, 0.1)",
            }}
          />

          <Box sx={{ textAlign: "center" }}>
            <img
              alt={`${occupancy} room`}
              src={doorIcon}
              style={{
                width: 48,
                height: 48,
                marginBottom: "8px",
              }}
            />
            <Box
              sx={{
                display: "inline-flex",
                alignItems: "center",
                gap: 1,
                px: 2,
                py: 0.75,
                borderRadius: "8px",
                backgroundColor: getStatusColor(),
                color: "white",
              }}
            >
              <Typography sx={{ fontSize: "0.875rem", fontWeight: 600 }}>
                {occupancy.charAt(0).toUpperCase() + occupancy.slice(1)}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Tab Navigation */}
      <Box
        sx={{
          px: 3,
          py: 2,
          backgroundColor: "#0A0A0A",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <Box sx={{ display: "flex", gap: 2 }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: activeTab === tab.id 
                  ? "2px solid #8C8CED" 
                  : "2px solid rgba(255, 255, 255, 0.1)",
                backgroundColor: activeTab === tab.id ? "#8C8CED" : "#1A1A1A",
                color: "white",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s",
                fontSize: "1rem",
              }}
              onMouseEnter={(e) => {
                if (activeTab !== tab.id) {
                  e.target.style.backgroundColor = "#2A2A2A";
                  e.target.style.borderColor = "#8C8CED";
                }
              }}
              onMouseLeave={(e) => {
                if (activeTab !== tab.id) {
                  e.target.style.backgroundColor = "#1A1A1A";
                  e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                }
              }}
            >
              <span style={{ marginRight: "8px" }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </Box>
      </Box>

      {/* Scrollable Content Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          px: 3,
          py: 3,
          backgroundColor: "#0A0A0A",
          "&::-webkit-scrollbar": {
            width: "10px",
          },
          "&::-webkit-scrollbar-track": {
            backgroundColor: "#1A1A1A",
          },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "#8C8CED",
            borderRadius: "5px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "#7A7ADB",
          },
        }}
      >
        {/* Light Tab */}
        {activeTab === "light" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <LightControl hotelId={hotelId} roomId={roomNumber} />
            <MetricChart
              hotelId={hotelId}
              room={roomNumber}
              metric={"light-state_brightness"}
              metric_title={"Brightness"}
            />
            <MetricChart
              hotelId={hotelId}
              room={roomNumber}
              metric={"light-status_mode"}
              metric_title={"Light Status"}
            />
          </Box>
        )}

        {/* Temperature Tab */}
        {activeTab === "temperature" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <TemperatureControl hotelId={hotelId} roomId={roomNumber} />
            <MetricChart
              hotelId={hotelId}
              room={roomNumber}
              metric={"temperature_temperatureC"}
              metric_title={"Temperature"}
            />
          </Box>
        )}

        {/* Humidity Tab */}
        {activeTab === "humidity" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <HumidityControl hotelId={hotelId} roomId={roomNumber} />
            <MetricChart
              hotelId={hotelId}
              room={roomNumber}
              metric={"humidity_humidityPercent"}
              metric_title={"Humidity"}
            />
          </Box>
        )}
      </Box>
    </SwipeableDrawer>
  );
};

export default RoomInfoDrawer;