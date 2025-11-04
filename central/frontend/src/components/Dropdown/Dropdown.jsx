import React from "react";

const Dropdown = ({ hotelList, selectedHotel, onSelect }) => {
  return (
    <div className="relative w-60 mb-6 mx-auto">
      <select
        value={selectedHotel}
        onChange={(e) => onSelect(Number(e.target.value))}
        className="w-full px-4 py-2 border border-blue-200 rounded-xl bg-blue-50 text-blue-900 text-center focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition duration-200"
      >
        <option value="">Select a hotel</option>
        {hotelList.map((hotel) => (
          <option key={hotel.id} value={hotel.id}>
            {hotel.name}
          </option>
        ))}
      </select>

      <span className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-blue-500">
        ▼
      </span>
    </div>
  );
};

export default Dropdown;
