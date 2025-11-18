import './App.css';
import LightControl from './pages/light-control';
import Home from './pages/home';
import {ToastContainer} from 'react-toastify'
import { useEffect } from 'react';
import axiosInstance from './utils/axiosInstance';

function App() {

  const checkCommandService = async () => {
    try {
      await axiosInstance.get('/health');
    } catch (error) {
      console.error('Command Service is not reachable:', error);
    }
  }

  useEffect(() => {
    checkCommandService();
  }, []);

  return (
    <div className="App">
      <Home/>
      <ToastContainer/>
    </div>
  );
}

export default App;
