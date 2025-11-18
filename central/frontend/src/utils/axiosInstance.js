import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: process.env.REACT_APP_COMMAND_SERVICE_URL || '/api',    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default axiosInstance;