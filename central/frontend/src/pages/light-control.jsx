import { useEffect, useState } from 'react'
import {Switch} from '@mui/material'
import LightBulb from '../components/lightbulb/light-bulb'
import axiosInstance from '../utils/axiosInstance'
import {toast} from 'react-toastify'
import BrightnessSlider from '../components/brightness-slide/brightness-slider'

const LightControl = ({on = false}) => {
  

    const [lightOn, setLightOn] = useState(on)
    const [brightness, setBrightness] = useState(50)
    const [updating, setIsUpdating] = useState(false)

    const getLightStatus = async () => {
      try{
      const hotel = process.env.REACT_APP_HOTELID || "hotel_01";
      const room = process.env.REACT_APP_ROOMID || 101;

      const res = await axiosInstance.get(`/actuator/light/${hotel}/${room}/state`);
      setLightOn(Number(res.data.state) === 1);
      }

    catch (err) {
      toast.error("Error fetching temperature details for current room");
    }
    }

    const getBrightness = async () => {
      try{
      const hotel = process.env.REACT_APP_HOTELID || "hotel_01";
      const room = process.env.REACT_APP_ROOMID || 101;
      const res = await axiosInstance.get(`/actuator/light/${hotel}/${room}/brightness`);
      setBrightness(Number(res.data.state));
      }
    catch (err) {
      toast.error("Error fetching brightness details for current room");
    }
    }
      

    useEffect(() => {
      getLightStatus()
      getBrightness()
    }, []);

const changeLightStatus = async () => {
  
  const newStatus = !lightOn
  setLightOn(newStatus)
  const lightStatus = newStatus ? 'on' : 'off'
  try {
    await axiosInstance.post(`/actuator/light/${process.env.REACT_APP_HOTELID}/${process.env.REACT_APP_ROOMID}/${lightStatus}`)
  } catch(error) {
    console.error(error)
    toast.error("Error changing light")
    setLightOn(!newStatus)
  }
}



    const changeBrightness = async(value) => {
          try {
      const res = await axiosInstance.post(
        `/actuator/light/${process.env.REACT_APP_HOTELID}/${process.env.REACT_APP_ROOMID}/brightness/${value}`
      );
      console.log(res.data);
    } catch (err) {
      toast.error("Oops! Could not update brightness. Try again.");
    } finally {
      setIsUpdating(false);
    }
    }


  return (
    <div className="flex flex-row items-center justify-center">
  <div className="p-8 bg-white rounded-2xl shadow-lg text-center">
    <LightBulb lighton={lightOn} />

    <div className="flex flex-col items-center space-y-2">
      <Switch
        checked={lightOn}
        onChange={changeLightStatus}
        className="scale-125"
      />
    </div>
  </div>
  <div>
   <BrightnessSlider
    initialValue={brightness}
    onsliderChange={changeBrightness}
   />
   </div>
</div>

  )
}

export default LightControl
