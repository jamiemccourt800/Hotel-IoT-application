import React, { useEffect, useState } from "react";
import { axiosInstance } from "../utils/axiosInstance";

export default function HumidityControl({hotelId, roomId}) {
  const [featureEnabled, setFeatureEnabled] = useState(false);
  const [humidity, setHumidity] = useState(50);
  const [isLoading, setIsLoading] = useState(true);
  
  // Check if user is admin from localStorage
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const isAdmin = user.role === "admin";
  
  useEffect(() => {
    axiosInstance.get("/api/feature-flags")
    .then((res) => {
      setFeatureEnabled(res.data.feature_flags.humidity_control || false);
      setIsLoading(false);
    })
    .catch(() => { 
      setFeatureEnabled(false);
      setIsLoading(false);
    });
  }, [])

  useEffect(() => {
    if(hotelId && roomId){
      axiosInstance.get(`/actuator/humidity/${hotelId}/${roomId}/state`)
      .then((res) => setHumidity(res.data?.state || 50))
      .catch(() => setHumidity(50));
    }
  }, [hotelId, roomId]);

  const handleHumidityChange = (newValue) => {
    if (!featureEnabled && !isAdmin) return; // Can't change if not enabled and not admin
    
    setHumidity(newValue);
    
    // Make API call to update humidity
    if(hotelId && roomId){
      axiosInstance.post(`/actuator/humidity/${hotelId}/${roomId}/set_target/${newValue}`, {
        humidity: newValue
      }).catch((err) => {
        console.error("Failed to update humidity:", err);
      });
    }
  };

  const getHumidityColor = () => {
    if (humidity < 40) return "#F59E0B";
    if (humidity < 60) return "#60A5FA";
    return "#8C8CED";
  };

  const getHumidityLevel = () => {
    if (humidity < 40) return "Dry 🏜️";
    if (humidity < 60) return "Comfortable 😊";
    return "Humid 💧";
  };

  const canControl = featureEnabled || isAdmin;

  if (isLoading) {
    return (
      <div style={{
        backgroundColor: "#1A1A1A",
        borderRadius: "16px",
        padding: "24px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        maxWidth: "600px",
        margin: "0 auto",
        textAlign: "center",
        color: "rgba(255, 255, 255, 0.5)",
      }}>
        Loading...
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: "#1A1A1A",
      borderRadius: "16px",
      padding: "24px",
      border: "1px solid rgba(255, 255, 255, 0.1)",
      maxWidth: "600px",
      margin: "0 auto",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "20px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "40px",
            height: "40px",
            borderRadius: "10px",
            backgroundColor: getHumidityColor(),
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div>
            <h3 style={{ color: "white", margin: 0, fontSize: "1.25rem", fontWeight: 600 }}>
              Humidity Control
            </h3>
            <p style={{ color: "rgba(255, 255, 255, 0.6)", margin: 0, fontSize: "0.875rem" }}>
              {getHumidityLevel()}
            </p>
          </div>
        </div>

        {/* Status badge for non-admin when disabled */}
        {!isAdmin && !featureEnabled && (
          <div style={{
            padding: "6px 12px",
            borderRadius: "8px",
            backgroundColor: "#2A2A2A",
            color: "rgba(255, 255, 255, 0.6)",
            fontSize: "0.75rem",
            fontWeight: 600,
          }}>
            🔒 View Only
          </div>
        )}
      </div>

      {/* Humidity Display & Slider */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "24px",
        opacity: canControl ? 1 : 0.6,
        transition: "opacity 0.3s",
      }}>
        {/* Big Number */}
        <div style={{ textAlign: "center", minWidth: "100px" }}>
          <div style={{
            fontSize: "3rem",
            fontWeight: 700,
            color: getHumidityColor(),
            lineHeight: 1,
          }}>
            {humidity}
          </div>
          <div style={{ color: "rgba(255, 255, 255, 0.5)", fontSize: "0.875rem", marginTop: "4px" }}>
            {canControl ? "Target %" : "Current %"}
          </div>
        </div>

        {/* Slider */}
        <div style={{ flex: 1 }}>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "8px",
            fontSize: "0.75rem",
            color: "rgba(255, 255, 255, 0.5)",
          }}>
            <span>Dry</span>
            <span>Comfortable</span>
            <span>Humid</span>
          </div>
          
          <div style={{ position: "relative" }}>
            <input
              type="range"
              min="30"
              max="80"
              value={humidity}
              onChange={(e) => handleHumidityChange(Number(e.target.value))}
              disabled={!canControl}
              style={{
                width: "100%",
                height: "8px",
                borderRadius: "4px",
                appearance: "none",
                background: `linear-gradient(to right, #F59E0B 0%, #60A5FA 50%, #8C8CED 100%)`,
                cursor: canControl ? "pointer" : "not-allowed",
                outline: "none",
                opacity: canControl ? 1 : 0.5,
              }}
            />
            <div style={{
              position: "absolute",
              top: "0",
              left: `calc(${((humidity - 30) / 50) * 100}% - 10px)`,
              width: "20px",
              height: "20px",
              borderRadius: "50%",
              backgroundColor: "white",
              border: `3px solid ${getHumidityColor()}`,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.3)",
              transform: "translateY(-6px)",
              pointerEvents: "none",
              transition: "border-color 0.3s",
            }} />
          </div>

          <div style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: "8px",
            fontSize: "0.75rem",
            color: "rgba(255, 255, 255, 0.4)",
          }}>
            <span>30%</span>
            <span style={{ color: "#60A5FA" }}>Recommended: 40-60%</span>
            <span>80%</span>
          </div>
        </div>
      </div>

      {/* Info message for non-admin when disabled */}
      {!isAdmin && !featureEnabled && (
        <div style={{
          marginTop: "16px",
          padding: "12px",
          borderRadius: "8px",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          border: "1px solid rgba(245, 158, 11, 0.3)",
          color: "rgba(255, 255, 255, 0.7)",
          fontSize: "0.875rem",
          textAlign: "center",
        }}>
          ℹ️ Sorry, you do not have permission to adjust humidity settings.
        </div>
      )}

      <style>{`
        input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          width: 0;
          height: 0;
        }
        input[type="range"]::-moz-range-thumb {
          width: 0;
          height: 0;
          border: none;
          background: transparent;
        }
      `}</style>
    </div>
  );
}