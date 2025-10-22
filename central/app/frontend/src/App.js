import './App.css';
import LightControl from './pages/light-control';
import Home from './pages/home';
import {ToastContainer} from 'react-toastify'

function App() {
  return (
    <div className="App">

      <Home/>
      <ToastContainer/>
    </div>
  );
}

export default App;
