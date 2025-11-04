const generateRooms = (count, start = 1) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    number: `${start + i}`,
    type: i % 3 === 0 ? "Single" : i % 3 === 1 ? "Double" : "Suite",
    occupied: Math.random() < 0.5, // randomized for now
  }));
};

// Simulated hotel data
const hotels = [
  {
    id: 1,
    name: "Hotel 1",
    rooms: generateRooms(5),
  },
  {
    id: 2,
    name: "Hotel 2",
    rooms: generateRooms(8),
  },
  {
    id: 3,
    name: "Hotel 3",
    rooms: generateRooms(3),
  },
];

// Simulate network delay
const simulateDelay = (ms = 700) =>
  new Promise((resolve) => setTimeout(resolve, ms));


export const fetchHotels = async () => {
  await simulateDelay();
  return hotels.map(({ id, name, location }) => ({ id, name, location }));
};

/** Fetch rooms for a specific hotel */
export const fetchRoomsByHotel = async (hotelId) => {
  await simulateDelay();
  const hotel = hotels.find((h) => h.id === hotelId);
  return hotel ? hotel.rooms : [];
};

/** Fetch a hotel with all details */
export const fetchHotelDetails = async (hotelId) => {
  await simulateDelay();
  return hotels.find((h) => h.id === hotelId) || null;
};
