// SliderPageTailwind.jsx
import { useState } from "react";
import LightControl from "./light-control";
import TemperatureControl from "./temp-control";

const Home = () => {
  const [activePage, setActivePage] = useState(0);

  return (
    <div className="w-full mx-auto mt-20 font-sans">
      {/* Tabs */}
      <div className="flex justify-center mb-4">
        <button
          className={`px-4 py-2 mx-1 rounded transition ${
            activePage === 0 ? "bg-blue-500 text-white" : "bg-gray-300"
          }`}
          onClick={() => setActivePage(0)}
        >
          Light
        </button>
        <button
          className={`px-4 py-2 mx-1 rounded transition ${
            activePage === 1 ? "bg-blue-500 text-white" : "bg-gray-300"
          }`}
          onClick={() => setActivePage(1)}
        >
          Temperature
        </button>
      </div>


      <div className="overflow-hidden rounded">
        <div
          className="flex transition-transform duration-500 ease-in-out"
          style={{ transform: `translateX(-${activePage * 100}%)` }}
        >
          <div className="w-full p-6 flex-shrink-0">
            <LightControl/>
          </div>
          <div className="w-full p-6 flex-shrink-0">
            <TemperatureControl/>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
