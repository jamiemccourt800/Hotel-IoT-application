// Unauthorized.jsx
import React from "react";
import { Box, Typography, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

const Unauthorized = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        p: 3,
        textAlign: "center",
      }}
    >
      <Typography sx={{ fontSize: 80, mb: 2 }}>⚠️</Typography>
      <Typography variant="h3" color="error" gutterBottom>
        Unauthorized
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={3}>
        Sorry! You don't have permission to access this page.
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={() => navigate("/home")}
      >
        Go Back Home
      </Button>
    </Box>
  );
};

export default Unauthorized;
