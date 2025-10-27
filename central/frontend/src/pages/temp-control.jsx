import { useEffect, useState } from "react";
import TemperatureSlider from "../components/temperature-slider/temp-slider";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";

const TemperatureControl = () => {
  const [updating, setIsUpdating] = useState(false);
  const [temp, setTemp] = useState(null);


  const getTemperature = async () => {
    try {
      const hotel = process.env.REACT_APP_HOTELID || "hotel_01";
      const room = process.env.REACT_APP_ROOMID || 101;
      const res = await axiosInstance.get(`/actuator/temperature/${hotel}/${room}/current`);
      const roundedTemp = Math.round(res.data.temperature * 2) / 2; // round to nearest .5
      setTemp(roundedTemp);
    } catch (err) {
      toast.error("Error fetching temperature details for current room");
    }
  };

  const setTemperature = async (value) => {
    setIsUpdating(true);
    try {
      const hotel = process.env.REACT_APP_HOTELID || "hotel_01";
      const room = process.env.REACT_APP_ROOMID || 101;
      const res = await axiosInstance.post(`/send_command/${hotel}/${room}/temperature/${value}`);
      setTemp(value); 
    } catch (error) {
      toast.error("Oops! There was an issue adjusting the temperature. Try again later!");
    } finally {
      setIsUpdating(false);
    }
  };

  useEffect(() => {
    getTemperature();
  }, []);

  return (
    <div className="flex flex-row items-center justify-center gap-4">
      {temp !== null && (
        <TemperatureSlider
          initialValue={temp}
          onSliderChange={setTemperature}
          disabled={updating}
        />
      )}
    </div>
  );
};

export default TemperatureControl;
