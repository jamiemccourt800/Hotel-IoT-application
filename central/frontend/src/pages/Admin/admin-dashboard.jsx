import React, { useEffect, useState } from "react";
import Dropdown from "../../components/Dropdown/Dropdown";
import RoomTile from "../../components/adminroomTile/roomTile";
import RoomInfoDrawer from "../../components/adminroomTile/roomInfoDrawer";
import { fetchHotelRoomsFromAPI, fetchHotels } from "../../utils/hotelService";

const AdminDashboard = () => {
  const [hotels, setHotels] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [selectedHotel, setSelectedHotel] = useState("");
  const [openRoomInfo, setOpenRoomInfo] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);

  useEffect(() => {
    fetchHotels().then((data) => setHotels(data));
  }, []);

  const handleHotelSelect = async (hotelId) => {
    setSelectedHotel(hotelId);
    const rooms = await fetchHotelRoomsFromAPI(hotelId);
    setRooms(rooms.rooms);
  };

  return (
    <div>
      <RoomInfoDrawer
        hotelId={selectedHotel}
        roomNumber={selectedRoom?.room_id}
        occupancy= {selectedRoom?.status}
        openDrawer={openRoomInfo}
        setOpenDrawer={setOpenRoomInfo}
      />
      <div className="p-6 background">
        <Dropdown
          hotelList={hotels}
          selectedHotel={selectedHotel}
          onSelect={handleHotelSelect}
        />
        {selectedHotel && (
          <div>
            <h2 className="text-2xl font-semibold text-blue-700 mb-4 text-center">
              Rooms
            </h2>
            <div className="grid grid-cols-3 gap-4">
              {rooms.map((room) => (
                <RoomTile
                  key={room.room_id}
                  room={room}
                  number={room.room_id}
                  occupied={room.status}
                  roomInfoHandler={() => {
                    setSelectedRoom(room);
                    setOpenRoomInfo(true);
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard