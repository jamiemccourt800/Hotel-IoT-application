import axios from 'axios';

// Access runtime config safely
const runtimeConfig = window.RUNTIME_CONFIG || {};

const axiosInstance = axios.create({
  baseURL: runtimeConfig.REACT_APP_COMMAND_SERVICE_URL || process.env.REACT_APP_C|| 'http://localhost:5000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const bookingApiAxiosInstance = axios.create({
  baseURL: runtimeConfig.REACT_APP_COMMAND_SERVICE_URL || process.env.REACT_APP_BOOKING_SERVICE_URL || 'http://localhost:3003',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});


const grafanaUrl = runtimeConfig.REACT_APP_COMMAND_SERVICE_URL || process.env.REACT_APP_GRAFANA_URL || 'http://localhost:3000';

export { axiosInstance, bookingApiAxiosInstance, grafanaUrl };
