import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: 'http://command.central.svc.cluster.local:5000',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default axiosInstance;