import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: process.env.REACT_APP_COMMAND_SERVICE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

const bookingApiAxiosInstance = axios.create({
    // baseURL: process.env.REACT_APP_BOOKING_SERVICE_URL,
    baseURL: 'http://localhost:8000',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export { axiosInstance, bookingApiAxiosInstance };