import { bookingApiAxiosInstance } from "./axiosInstance";

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
  try {
    const response = await bookingApiAxiosInstance.get('/api/get_hotels');
    return response.data.hotels;
  } catch (error) {
    console.error("Error fetching hotels from booking service:", error);
    return [];
  }
};

export const fetchUserRoom = async(userId) => {
  try{
    const room = bookingApiAxiosInstance.get(`/api/getroom/${userId}`);
    console.log("Fetched user room:", room);
  }catch(error){
    console.error("Error fetching user room from booking service:", error);
    return null;
}
}

export const fetchHotelRoomsFromAPI = async (hotelId) => {
  try {
    const response = await bookingApiAxiosInstance.get(`/api/get_rooms/${hotelId}`);
    return response.data;
  }
  catch (error) {
    console.error("Error fetching rooms from booking service:", error);
    return [];
  }
}

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
