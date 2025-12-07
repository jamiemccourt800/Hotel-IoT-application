import React, { useEffect, useState } from "react";
import { axiosInstance } from "../../utils/axiosInstance";

export default function HumidityControl({hotelId, roomId}) {
  const [enabled, setEnabled] = useState(false);
  const [humidity, setHumidity] = useState(50);

  useEffect(() => {
    axiosInstance.get(`/actuator/humidity/${hotelId}/${roomId}/state`)
    .then((res) => setHumidity(res.data?.state))
  }, [])

  const getHumidityColor = () => {
    if (humidity < 40) return "#F59E0B";
    if (humidity < 60) return "#60A5FA";
    return "#8C8CED";
  };

  const getHumidityLevel = () => {
    if (humidity < 40) return "Dry";
    if (humidity < 60) return "Comfortable";
    return "Humid";
  };

  return (
    <div style={{
      backgroundColor: "#1A1A1A",
      borderRadius: "16px",
      padding: "24px",
      border: "1px solid rgba(255, 255, 255, 0.1)",
      maxWidth: "1200px",
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
            {enabled && (
              <p style={{ color: "rgba(255, 255, 255, 0.6)", margin: 0, fontSize: "0.875rem" }}>
                {getHumidityLevel()}
              </p>
            )}
          </div>
        </div>

        {/* Power Toggle */}
        <button
          onClick={() => setEnabled(!enabled)}
          style={{
            width: "56px",
            height: "32px",
            borderRadius: "16px",
            border: "none",
            backgroundColor: enabled ? getHumidityColor() : "#2A2A2A",
            position: "relative",
            cursor: "pointer",
            transition: "all 0.3s",
          }}
        >
          <div style={{
            width: "24px",
            height: "24px",
            borderRadius: "50%",
            backgroundColor: "white",
            position: "absolute",
            top: "4px",
            left: enabled ? "28px" : "4px",
            transition: "all 0.3s",
            boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
          }} />
        </button>
      </div>

      {/* Humidity Display & Slider */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "24px",
        opacity: enabled ? 1 : 0.4,
        transition: "opacity 0.3s",
      }}>
        {/* Big Number */}
        <div style={{ textAlign: "center", minWidth: "100px" }}>
          <div style={{
            fontSize: "3rem",
            fontWeight: 700,
            color: enabled ? getHumidityColor() : "#666",
            lineHeight: 1,
          }}>
            {humidity}
          </div>
          <div style={{ color: "rgba(255, 255, 255, 0.5)", fontSize: "0.875rem", marginTop: "4px" }}>
            Target %
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
              onChange={(e) => setHumidity(Number(e.target.value))}
              disabled={!enabled}
              style={{
                width: "100%",
                height: "8px",
                borderRadius: "4px",
                appearance: "none",
                background: enabled
                  ? `linear-gradient(to right, #F59E0B 0%, #60A5FA 50%, #8C8CED 100%)`
                  : "#2A2A2A",
                cursor: enabled ? "pointer" : "not-allowed",
                outline: "none",
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
              border: `3px solid ${enabled ? getHumidityColor() : "#666"}`,
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