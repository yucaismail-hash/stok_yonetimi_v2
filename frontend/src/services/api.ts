import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 📌 İstekleri logla
api.interceptors.request.use((config) => {
  console.log(`📤 API İSTEK: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
  return config;
});

// 📌 Cevabı logla
api.interceptors.response.use(
  (response) => {
    console.log(`📥 API CEVAP: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ API HATA: ${error.response?.status} ${error.config?.url}`);
    return Promise.reject(error);
  }
);

// 📌 Auth hariç tüm isteklere token ekle
api.interceptors.request.use((config) => {
  // Login ve register isteklerinde token ekleme
  if (config.url?.includes('/auth/login') || config.url?.includes('/auth/register')) {
    return config;
  }
  
  const token = localStorage.getItem('auth-storage');
  if (token) {
    try {
      const parsed = JSON.parse(token);
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`;
        console.log('✅ Token eklendi');
      }
    } catch {
      // ignore
    }
  }
  return config;
});

export default api;