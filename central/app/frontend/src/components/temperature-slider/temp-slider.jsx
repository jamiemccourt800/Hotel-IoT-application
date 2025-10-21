import React, { useState } from "react";
import Box from "@mui/joy/Box";
import Slider from "@mui/joy/Slider";

const marks = [
  { value: 15, label: "15°C" },
  { value: 20, label: "20°C" },
  { value: 25, label: "25°C" },
  { value: 30, label: "30°C" },
];

function valueText(value) {
  return `${value}°C`;
}

// Function to map temperature to color (blue → red)
const getColor = (temp) => {
  const minTemp = 15;
  const maxTemp = 30;
  const ratio = (temp - minTemp) / (maxTemp - minTemp);

  const r = Math.round(0 + ratio * (255 - 0)); // red increases
  const g = Math.round(0 + ratio * (100 - 0)); // optional slight green
  const b = Math.round(255 - ratio * 255); // blue decreases

  return `rgb(${r},${g},${b})`;
};

const TemperatureSlider = () => {
  const [temp, setTemp] = useState(22); // initial temperature

  return (
    <Box sx={{ mx: "auto", height: 250 }}>
      <Slider
        orientation="vertical"
        aria-label="Temperature"
        value={temp}
        onChange={(e, newValue) => setTemp(newValue)}
        getAriaValueText={valueText}
        step={0.5}
        marks={marks}
        valueLabelDisplay="on"
        min={15}
        max={30}
        sx={{
          "--Slider-thumb-size": "24px",
          "--Slider-track-size": "8px",
          "--Slider-thumb-color": getColor(temp),
          "--Slider-track-color": getColor(temp),
          "--Slider-track-radius": "6px",
          "--Slider-thumb-shadow": "0 0 0 8px rgba(0,0,0,0.05)",
        }}
      />
    </Box>
  );
};

export default TemperatureSlider;
