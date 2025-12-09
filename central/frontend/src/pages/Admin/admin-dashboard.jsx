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
  }
  return (
    <div>
     {
      openRoomInfo && selectedRoom && (
         <RoomInfoDrawer
        hotelId={selectedHotel}
        roomNumber={selectedRoom?.room_id}
        occupancy= {selectedRoom?.status}
        openDrawer={openRoomInfo}
        setOpenDrawer={setOpenRoomInfo}
      />
      )
     }
      <div className="p-6 background">
        <Dropdown
          hotelList={hotels}
          selectedHotel={selectedHotel}
          onSelect={handleHotelSelect}
        />
        {selectedHotel && (
          <div>
            <h2 className="text-4xl font-semibold text-white  mb-7 text-center">
              Rooms
            </h2>
            <div className="grid grid-cols-4 gap-4">
              {rooms.map((room) => {
                return (
                  <RoomTile
                  key={room.room_id}
                  room={room}
                  number={room.room_id}
                  status={room.status}
                  roomInfoHandler={() => {
                    setSelectedRoom(room);
                    setOpenRoomInfo(true);
                  }}
                />
                )
})}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard