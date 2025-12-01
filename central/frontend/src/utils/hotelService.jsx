import { bookingApiAxiosInstance } from "./axiosInstance";


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
    const room = await bookingApiAxiosInstance.get(`/api/getroom/${userId}`);
    return room.data
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