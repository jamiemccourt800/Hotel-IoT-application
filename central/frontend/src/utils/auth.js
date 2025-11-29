import { bookingApiAxiosInstance } from "./axiosInstance";

export const login = async (username, password) => {
 
  try{
  const res = await bookingApiAxiosInstance.post('/api/signin', {
    username,
    password
  })
  return res.data;
}  catch(error){
    console.error("Error during login:", error);
    return null;
  }
};

export const logout = () => {
  localStorage.removeItem("user");
};
