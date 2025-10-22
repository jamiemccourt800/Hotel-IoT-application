import React, { useEffect, useState, useRef } from 'react'
import {Switch} from '@mui/material'
import LightBulb from '../components/lightbulb/light-bulb'
import TemperatureSlider from '../components/temperature-slider/temp-slider'
import axiosInstance from '../utils/axiosInstance'
import {toast} from 'react-toastify'
import BrightnessSlider from '../components/brightness-slide/brightness-slider'

const LightControl = ({on = false}) => {


    const [lightOn, setLightOn] = useState(on)
    const [updating, setIsUpdating] = useState(false)

    const changeLightStatus = () => {
      const newStatus = !lightOn
      setLightOn(newStatus)
      const lightStatus = newStatus?'on':'off'
      axiosInstance.post(`/actuator/light/${process.env.REACT_APP_HOTELID}/${process.env.REACT_APP_ROOMID}/${lightStatus}`)
      .catch((error) => toast.error("Oops! There was an issue changing the light. Please try again later!"))
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
    initialValue={50}
    onsliderChange={changeBrightness}
   />
   </div>
</div>

  )
}

export default LightControl
