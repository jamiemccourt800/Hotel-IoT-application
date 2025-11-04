import React, { useEffect, useState } from "react";
import Dropdown from "../../components/Dropdown/Dropdown";
import {
  fetchHotels,
  fetchRoomsByHotel,
} from "../../utils/hotelService";
import RoomTile from "../../components/adminroomTile/roomTile";
import { Link } from "react-router-dom";

const AdminDashboard = () => {
  const [hotels, setHotels] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [selectedHotel, setSelectedHotel] = useState("");

  useEffect(() => {
    fetchHotels().then(setHotels);

  }, []);

  const handleHotelSelect = async (hotelId) => {
    setSelectedHotel(hotelId);
    const data = await fetchRoomsByHotel(hotelId);
    setRooms(data);
  };

  return (
    <div className="p-6">
      {/* Dropdown */}
      <Dropdown
        hotelList={hotels}
        selectedHotel={selectedHotel}
        onSelect={handleHotelSelect}
      />

      <Link to="/admin/grafana" className="block mt-4 mb-6 text-center text-blue-600 hover:underline">
        View Grafana Dashboard
      </Link>
      {/* Rooms Section */}
      {selectedHotel && (
        <div>
          <h2 className="text-2xl font-semibold text-blue-700 mb-4 text-center">
            Rooms
          </h2>

          <div className="grid grid-cols-3 gap-4">
            {rooms.map((room) => <RoomTile key={room.id} room={room} number={room.number} occupied={room.occupied} hotel={selectedHotel}/>)}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
