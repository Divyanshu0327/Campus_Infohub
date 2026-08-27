import axios from 'axios';
import { mockAdapter } from './mock/index';

const USE_MOCK = false; // Toggle this to switch between real and mock backend

const API = axios.create({
  baseURL: import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000',
});

// Mock Adapter Logic
if (USE_MOCK) {
    API.defaults.adapter = mockAdapter;
}

// Add a request interceptor to include the token
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add a response interceptor to handle 401 Unauthorized
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized access - clearing token");
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('userId');

      const publicPaths = ['/', '/explore', '/login', '/register', '/forgot-password', '/admin/login'];
      const isPublicPath = publicPaths.includes(window.location.pathname);
      if (!isPublicPath) {
        window.location.href = '/login'; 
      }
    }
    return Promise.reject(error);
  }
);

export default API;
