// SliderPageTailwind.jsx
import { useEffect, useState } from "react";
import LightControl from "./light-control";
import TemperatureControl from "./temp-control";
import Header from "../components/header/header";
import { fetchUserRoom } from "../utils/hotelService";
import { toast } from "react-toastify";

const Home = () => {
  const [activePage, setActivePage] = useState(0);
  const [disablePage, setDisablePage] = useState(false)

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user"));
    fetchUserRoom(user.user_id).then((data) => {
      console.log("User Room Data:", data);
    }).catch((err) => {
      console.error("Cannot get Information for user with id U001:", err);
      toast.error("Cannot fetch room details. Kindly check your credentials or contact your admin")
    });
  }
, []);

  const hotelId = "hotel_01"; // Example hotel ID
  const roomId = 101; // Example room ID

  return (
    <>
    <Header/>
    <div className="font-sans" >
      {/* Tabs */}
   <div className="flex justify-center mb-4">
  {/* Outer oval container */}
  <div className="flex bg-gray-300 rounded-full p-1 relative w-72">
    {/* Sliding highlight */}
    <div
      className={`absolute top-1 bottom-1 w-1/2 rounded-full bg-black transition-transform duration-300 ${
        activePage === 0 ? "translate-x-0" : "translate-x-full"
      }`}
    ></div>

    {/* Buttons */}
    <button
      className={`flex-1 z-10 py-2 rounded-full transition ${
        activePage === 0 ? "text-white" : "text-gray-700"
      }`}
      onClick={() => setActivePage(0)}
    >
      Light
    </button>
    <button
      className={`flex-1 z-10 py-2 rounded-full transition ${
        activePage === 1 ? "text-white" : "text-gray-700"
      }`}
      onClick={() => setActivePage(1)}
    >
      Temperature
    </button>
  </div>
</div>



      <div className="overflow-hidden rounded">
        <div
          className="flex transition-transform duration-500 ease-in-out"
          style={{ transform: `translateX(-${activePage * 100}%)` }}
        >
          <div className="w-full p-6 flex-shrink-0">
            <LightControl hotelId={hotelId} roomId={roomId}/>
          </div>
          <div className="w-full p-6 flex-shrink-0">
            <TemperatureControl hotelId={hotelId} roomId={roomId}/>
          </div>
        </div>
      </div>
    </div>
    </>
  );
};

export default Home;
