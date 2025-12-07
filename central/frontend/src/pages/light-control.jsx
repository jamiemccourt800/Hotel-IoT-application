import { useEffect, useState } from "react";
import { Switch } from "@mui/material";
import LightBulb from "../components/lightbulb/light-bulb";
import {axiosInstance} from "../utils/axiosInstance";
import { toast } from "react-toastify";
import BrightnessSlider from "../components/brightness-slide/brightness-slider";

const LightControl = ({hotelId, roomId }) => {
  const [isLightOn, setIsLightOn] = useState(false);
  const [brightness, setBrightness] = useState(50);
  const [isUpdating, setIsUpdating] = useState(false);

  // Fetch current light status
  const fetchLightStatus = async () => {
    try {
      const response = await axiosInstance.get(
        `/actuator/light/${hotelId}/${roomId}/state`
      );
      setIsLightOn(Number(response.data.state) === 1);
      console.log(response.data)
    } catch {
      toast.error("Error fetching light status for current room");
    }
  };

  // Fetch current brightness
  const fetchBrightness = async () => {
    try {

      const response = await axiosInstance.get(
        `/actuator/light/${hotelId}/${roomId}/brightness`
      );
      setBrightness(Number(response.data.state));
    } catch {
      toast.error("Error fetching brightness details for current room");
    }
  };

  useEffect(() => {
    fetchLightStatus();
    fetchBrightness();
  }, []);

  // Toggle light on/off
  const toggleLightStatus = async () => {
    const newStatus = !isLightOn;
    setIsLightOn(newStatus);
    const lightStatus = newStatus ? "on" : "off";

    try {
      await axiosInstance.post(
        `/actuator/light/${hotelId}/${roomId}/${lightStatus}`
      );
      toast.success(`Light turned ${lightStatus}`);
    } catch (error) {
      console.error(error);
      toast.error("Error changing light status");
      setIsLightOn(!newStatus);
    }
  };

  // Adjust brightness
  const updateBrightness = async (value) => {
    setIsUpdating(true);
    try {
      await axiosInstance.post(
        `/actuator/light/${hotelId}/${roomId}/brightness/${value}`
      );
      setBrightness(value);
      toast.success(`Brightness set to ${value}%`);
    } catch {
      toast.error("Oops! Could not update brightness. Try again.");
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="flex items-center justify-center">
      <div className="p-8 rounded-2xl shadow-xl text-center flex flex-row gap-6 max-w-md mx-auto bg-white">
        <div className="flex flex-col items-center space-y-3">
          <LightBulb lighton={isLightOn} />
          <Switch
            checked={isLightOn}
            onChange={toggleLightStatus}
            className="scale-125"
          />
          <p className="text-gray-600">
            Status:{" "}
            <span className="font-bold">
              {isLightOn ? "On" : "Off"}
            </span>
          </p>
        </div>

        <div className="w-full">
          <BrightnessSlider
            initialValue={brightness}
            onsliderChange={updateBrightness}
            disabled={isUpdating}
          />
          {isUpdating && (
            <p className="text-sm text-blue-500 mt-2">Updating brightness...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LightControl;
