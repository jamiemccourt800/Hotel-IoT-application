import React, { useEffect } from "react";

const Dropdown = ({ hotelList, selectedHotel, onSelect }) => {

  return (
    <div className="relative w-60 mb-6">
      <select
        value={selectedHotel}
        onChange={(e) => onSelect(e.target.value)}
        className="w-full px-4 py-4 border bg-black text-white text-center focus:outline-none focus:ring-2 focus:border-blue-400 transition duration-200"
      >
        <option value="">Select a hotel</option>
        {hotelList.map((hotel) => (
          <option key={hotel.hotel_id} value={hotel.hotel_id}>
            {hotel.name} {`(ID: ${hotel.hotel_id})`}
          </option>
        ))}
      </select>
    </div>
  );
};

export default Dropdown;
