import React from "react";

const Dropdown = ({ hotelList, selectedHotel, onSelect }) => {
  return (
    <div className="relative w-60 mb-6">
      <select
        value={selectedHotel}
        onChange={(e) => onSelect(Number(e.target.value))}
        className="w-full px-4 py-4 border bg-gray-900 text-white text-center focus:outline-none focus:ring-2 focus:border-blue-400 transition duration-200"
      >
        <option value="">Select a hotel</option>
        {hotelList.map((hotel) => (
          <option key={hotel.id} value={hotel.id}>
            {hotel.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default Dropdown;
