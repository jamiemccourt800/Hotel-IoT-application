import { Slider, Box, Typography } from "@mui/material";
import { useEffect, useState } from "react";

const VerticalLightSlider = ({ initialValue, onsliderChange }) => {
  const [brightness, setBrightness] = useState(initialValue);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleChange = (event, value) => {
    setBrightness(value);
  };

  const handleChangeCommitted = async (event, value) => {
    setIsUpdating(true);
     try {
    if (onsliderChange) await onsliderChange(value);
  } finally {
    setIsUpdating(false);
  }
  };

useEffect(() => {
  setBrightness(initialValue);
}, [initialValue]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      gap={2}
      height={200}
    >
      <Typography>{brightness}%</Typography>
      <Slider
        orientation="vertical"
        value={brightness}
        onChange={handleChange}
        onChangeCommitted={handleChangeCommitted}
        min={0}
        max={100}
        step={1}
        disabled={isUpdating}
        sx={{
          color: "#f5a623",
          height: 150,
          "& .MuiSlider-thumb": {
            width: 24,
            height: 24,
            backgroundColor: "#fff",
            border: "2px solid #f5a623",
          },
          "& .MuiSlider-track": {
            border: "none",
          },
          "& .MuiSlider-rail": {
            opacity: 0.3,
            backgroundColor: "#000",
          },
        }}
      />
    </Box>
  );
};

export default VerticalLightSlider;
