import { useState } from 'react'
import TemperatureSlider from '../components/temperature-slider/temp-slider'
import axiosInstance from '../utils/axiosInstance'
import { toast } from 'react-toastify'

const TemperatureControl = () => {

  const [updating, setIsUpdating] = useState(false)

  const setTemperature = async(value) => {
    axiosInstance.post(`/send_command/${process.env.REACT_APP_HOTELID}/${process.env.REACT_APP_ROOMID}/temperature/${value}`)
    .then((res) => console.log(res.data))
    .catch((error) => toast.error("Oops! There was an issue adjusting the temperature. Try again later!"))
    .finally(() => setIsUpdating(false))
  }
  return (
    <div className='flex flex-row items-center justify-center'>
      <TemperatureSlider
      initialValue={22}
      onSliderChange={setTemperature}
      disabled={updating}
      />
    </div>
  )
}

export default TemperatureControl
