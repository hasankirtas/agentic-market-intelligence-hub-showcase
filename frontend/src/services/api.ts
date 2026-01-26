import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Proxy in vite.config.ts handles forwarding to localhost:8000
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response || error.message);
        return Promise.reject(error);
    }
);

export default api;
