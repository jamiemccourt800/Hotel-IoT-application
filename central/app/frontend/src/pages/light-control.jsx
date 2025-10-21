import React, { useEffect, useState } from 'react'
import {Switch} from '@mui/material'
import LightBulb from '../components/lightbulb/light-bulb'
import TemperatureSlider from '../components/temperature-slider/temp-slider'
import axiosInstance from '../utils/axiosInstance'

const LightControl = ({on = false}) => {

    const [lightOn, setLightOn] = useState(on)

    useEffect(() => {
      axiosInstance.get('/health')
      .then((res) => console.log(res.data))
    }, [lightOn])

  return (
    <div className="flex flex-col items-center justify-center">
  <div className="p-8 bg-white rounded-2xl shadow-lg text-center">
    <LightBulb lighton={lightOn} />

    <div className="flex flex-col items-center space-y-2">
      <Switch
        defaultChecked
        onClick={() => setLightOn(!lightOn)}
        className="scale-125"
      />
    </div>
  </div>
</div>

  )
}

export default LightControl
