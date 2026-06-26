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

// 📌 Tüm isteklere token ekle (login/register hariç)
api.interceptors.request.use((config) => {
  // Login ve register isteklerinde token ekleme
  if (config.url?.includes('/auth/login') || config.url?.includes('/auth/register')) {
    return config;
  }
  
  // ✅ Token'ı doğru yerden al
  let token = null;
  
  // 1. Önce direkt localStorage'dan dene
  token = localStorage.getItem('access_token');
  
  // 2. Yoksa auth-storage'dan dene
  if (!token) {
    const authStorage = localStorage.getItem('auth-storage');
    if (authStorage) {
      try {
        const parsed = JSON.parse(authStorage);
        // Zustand veya benzeri bir state yönetimi kullanılıyorsa
        token = parsed.state?.token || parsed.token || parsed.access_token;
      } catch {
        // ignore
      }
    }
  }
  
  // 3. Yoksa sessionStorage'dan dene
  if (!token) {
    token = sessionStorage.getItem('access_token');
  }
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('✅ Token eklendi:', token.substring(0, 20) + '...');
  } else {
    console.log('⚠️ Token bulunamadı!');
  }
  
  return config;
});

export default api;