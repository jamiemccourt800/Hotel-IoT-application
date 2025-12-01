import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: process.env.REACT_APP_COMMAND_SERVICE_URL || 'http://localhost:5000',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

const bookingApiAxiosInstance = axios.create({
    baseURL: process.env.REACT_APP_BOOKING_SERVICE_URL || 'http://localhost:3003',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export { axiosInstance, bookingApiAxiosInstance };