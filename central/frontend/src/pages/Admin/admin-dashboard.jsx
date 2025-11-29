import React, { useEffect, useState } from "react";
import Dropdown from "../../components/Dropdown/Dropdown";
import RoomTile from "../../components/adminroomTile/roomTile";
import RoomInfoDrawer from "../../components/adminroomTile/roomInfoDrawer";
import { fetchHotels } from "../../utils/hotelService";

const AdminDashboard = () => {
  const [hotels, setHotels] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [selectedHotel, setSelectedHotel] = useState("");
  const [openRoomInfo, setOpenRoomInfo] = useState(false);
  

  useEffect(() => {
   fetchHotels().then((data) => {
      setHotels(data);
   });
  }, []);

  const handleHotelSelect = async (hotelId) => {
    // setSelectedHotel(hotelId);
    // const data = await fetchRoomsByHotel(hotelId);
    // setRooms(data);
    // setSelectedHotel('hotel_01')
    // setRooms([101])
  };

  const getRoomData = async() => {
  }

  return (
    <div>
      <RoomInfoDrawer
  hotelId={selectedHotel}
  roomNumber={rooms[0]?.number}
  openDrawer={openRoomInfo}
  setOpenDrawer={setOpenRoomInfo}
/>
      <div className="p-6 background">
        {/* Dropdown */}
        <Dropdown
          hotelList={hotels}
          selectedHotel={selectedHotel}
          onSelect={handleHotelSelect}
        />
        {/* Rooms Section */        }
        {selectedHotel && (
          <div>
            <h2 className="text-2xl font-semibold text-blue-700 mb-4 text-center">
              Rooms
            </h2>

            <div className="grid grid-cols-3 gap-4">
              {rooms.map((room) => (
  <RoomTile
    key={room.id}
    room={room}
    number={room.number}
    occupied={room.occupied}
    roomInfoHandler={() => setOpenRoomInfo(true)}
  />
))}

</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
