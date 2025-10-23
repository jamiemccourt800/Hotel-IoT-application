import './App.css';
import LightControl from './pages/light-control';
import Home from './pages/home';
import {ToastContainer} from 'react-toastify'
import { useEffect } from 'react';
import axiosInstance from './utils/axiosInstance';

function App() {

useEffect(() => {
  axiosInstance.get(`/actuator/light/${process.env.REACT_APP_HOTELID}/${process.env.REACT_APP_ROOMID}/state`)
  .then((res) => console.log(res.data))
  .catch((err) => console.log(err))
}, [])

  return (
    <div className="App">
      <Home/>
      <ToastContainer/>
    </div>
  );
}

export default App;
