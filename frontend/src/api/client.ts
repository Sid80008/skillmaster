import axios from 'axios';

let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// If they provided just the domain without the /api/v1 path, append it
if (API_BASE_URL && !API_BASE_URL.endsWith('/api/v1') && !API_BASE_URL.includes('localhost')) {
    API_BASE_URL = `${API_BASE_URL.replace(/\/$/, '')}/api/v1`;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('skillquest_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('skillquest_token');
      window.dispatchEvent(new Event('unauthorized'));
    }
    return Promise.reject(error);
  }
);
