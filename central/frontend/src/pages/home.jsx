import { useEffect, useState } from "react";
import LightControl from "./light-control";
import TemperatureControl from "./temp-control";
import Header from "../components/header/header";
import { fetchUserRoom } from "../utils/hotelService";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import HumidityControl from "./humidityControl";

const Home = () => {
  const [activePage, setActivePage] = useState(0);
  const [roomData, setRoomData] = useState({
    room_id: "",
    hotel_id: ""
  });

  const navigate = useNavigate();

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      navigate("/");
      return;
    }
    fetchUserRoom(user.user_id)
      .then((data) => {
        setRoomData(data);
        console.log("Room Data:", data);
      })
      .catch((err) => {
        console.error("Cannot get Information for user:", err);
        toast.error(
          "Cannot fetch room details. Kindly check your credentials or contact your admin"
        );
      });
  }, []);

  return (
    <>
      <Header />
      <div className="font-sans flex">
        {/* Main content */}
        <div className="flex-1 p-6">
          {/* Tabs */}
          <div className="flex justify-center mb-4">
            <div className="flex bg-gray-300 rounded-full p-1 relative w-96">
              {/* Slider indicator */}
              <div
                className={`absolute top-1 bottom-1 w-1/3 rounded-full bg-black transition-transform duration-300 ${
                  activePage === 0
                    ? "translate-x-0"
                    : activePage === 1
                    ? "translate-x-full"
                    : "translate-x-[200%]"
                }`}
              ></div>

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
              <button
                className={`flex-1 z-10 py-2 rounded-full transition ${
                  activePage === 2 ? "text-white" : "text-gray-700"
                }`}
                onClick={() => setActivePage(2)}
              >
                Humidity
              </button>
            </div>
          </div>

          {/* Tab content */}
          <div className="overflow-hidden rounded">
            <div
              className="flex transition-transform duration-500 ease-in-out"
              style={{ transform: `translateX(-${activePage * 100}%)` }}
            >
              <div className="w-full p-6 flex-shrink-0">
                <LightControl
                  hotelId={roomData.hotel_id}
                  roomId={roomData.room_id}
                />
              </div>
              <div className="w-full p-6 flex-shrink-0">
                <TemperatureControl
                  hotelId={roomData.hotel_id}
                  roomId={roomData.room_id}
                />
              </div>
              <div className="w-full p-6 flex-shrink-0">
                <HumidityControl
                  hotelId={roomData.hotel_id}
                  roomId={roomData.room_id}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;
