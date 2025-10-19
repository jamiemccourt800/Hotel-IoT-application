import React, { useEffect, useState } from 'react'
import {Switch} from '@mui/material'
import LightBulb from '../components/lightbulb/light-bulb'
import TemperatureSlider from '../components/temperature-slider/temp-slider'

const LightControl = ({on = false}) => {

    const [lightOn, setLightOn] = useState(on)

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-blue-100 to-blue-50">
  <div className="p-8 bg-white rounded-2xl shadow-lg text-center space-y-6">
    <LightBulb lighton={lightOn} />

    <div className="flex flex-col items-center space-y-2">
      <Switch
        defaultChecked
        onClick={() => setLightOn(!lightOn)}
        className="scale-125"
      />
      {/* <TemperatureSlider/> */}
    </div>
  </div>
</div>

  )
}

export default LightControl
