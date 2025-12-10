import axios from 'axios';

// Access runtime config safely
const runtimeConfig = window.RUNTIME_CONFIG || {};

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_COMMAND_SERVICE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const bookingApiAxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_BOOKING_SERVICE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});


const grafanaUrl = process.env.REACT_APP_GRAFANA_URL

export { axiosInstance, bookingApiAxiosInstance, grafanaUrl };
