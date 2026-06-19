import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  // Sektör ve auth endpoint'leri için token zorunlu değil
  if (config.url?.includes('/sectors') || config.url?.includes('/auth')) {
    return config;
  }
  
  const token = localStorage.getItem('auth-storage');
  if (token) {
    try {
      const parsed = JSON.parse(token);
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`;
      }
    } catch {
      // ignore
    }
  }
  return config;
});

export default api;