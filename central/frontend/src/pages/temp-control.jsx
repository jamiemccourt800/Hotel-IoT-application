import { useEffect, useState } from "react";
import TemperatureSlider from "../components/temperature-slider/temp-slider";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";

const TemperatureControl = () => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [temperature, setTemperature] = useState(15);

  // Fetch current room temperature
  const fetchTemperature = async () => {
    try {
      const hotelId = process.env.REACT_APP_HOTELID || "hotel_01";
      const roomId = process.env.REACT_APP_ROOMID || 101;

      const response = await axiosInstance.get(
        `/actuator/temperature/${hotelId}/${roomId}/current`
      );

      const roundedTemp = Math.round(response.data.temperature * 2) / 2; // round to nearest 0.5
      setTemperature(roundedTemp);
    } catch {
      toast.error("Error fetching temperature details for current room");
    }
  };

  // Update room temperature
  const updateTemperature = async (value) => {
    setIsUpdating(true);
    try {
      const hotelId = process.env.REACT_APP_HOTELID || "hotel_01";
      const roomId = process.env.REACT_APP_ROOMID || 101;

      await axiosInstance.post(
        `/send_command/${hotelId}/${roomId}/temperature/${value}`
      );

      setTemperature(value);
      toast.success(`Temperature set to ${value}°C`);
    } catch {
      toast.error("Oops! There was an issue adjusting the temperature. Try again later!");
    } finally {
      setIsUpdating(false);
    }
  };

  useEffect(() => {
    fetchTemperature();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center gap-6 rounded-2xl shadow-xl p-10 max-w-md mx-auto bg-white">
      <p className="text-gray-600 mb-4">
        Current Temperature: <span className="font-bold">{temperature}°C</span>
      </p>
      <TemperatureSlider
        initialValue={temperature}
        onSliderChange={updateTemperature}
        disabled={isUpdating}
      />
      {isUpdating && (
        <p className="text-sm text-blue-500 mt-2">Updating temperature...</p>
      )}
    </div>
  );
};

export default TemperatureControl;
