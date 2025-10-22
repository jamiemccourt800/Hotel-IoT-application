import { useState } from "react";
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

const getColor = (temp) => {
  const minTemp = 15;
  const maxTemp = 30;
  const ratio = (temp - minTemp) / (maxTemp - minTemp);

  const r = Math.round(ratio * 255);
  const g = Math.round(ratio * 100);
  const b = Math.round(255 - ratio * 255);

  return `rgb(${r},${g},${b})`;
};

const TemperatureSlider = ({ initialValue = 22, onSliderChange, disabled }) => {
  const [temp, setTemp] = useState(initialValue);

  const handleChange = (event, value) => {
    setTemp(value);
  };

  const handleChangeCommitted = async (event, value) => {
    if (onSliderChange) await onSliderChange(value);
  };

  return (
    <Box sx={{ mx: "auto", height: 250 }}>
      <Slider
        orientation="vertical"
        aria-label="Temperature"
        value={temp}
        onChange={handleChange}
        onChangeCommitted={handleChangeCommitted}
        getAriaValueText={valueText}
        step={0.5}
        marks={marks}
        valueLabelDisplay="on"
        min={15}
        max={30}
        disabled={disabled}
        slotProps={{
          thumb: {
            sx: { bgcolor: getColor(temp) },
          },
          track: {
            sx: { bgcolor: getColor(temp) },
          },
        }}
        sx={{
          "--Slider-thumb-size": "24px",
          "--Slider-track-size": "8px",
          "--Slider-track-radius": "6px",
          "--Slider-thumb-shadow": "0 0 0 8px rgba(0,0,0,0.05)",
        }}
      />
    </Box>
  );
};

export default TemperatureSlider;
