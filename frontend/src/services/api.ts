// frontend/src/services/api.ts - TAM DOSYA (GÜNCELLENMİŞ)
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

// ============================================================
// 🆕 YENİ API SERVİS FONKSİYONLARI
// ============================================================

// ----- PRICING PREVIEW -----
export const getPricingPreview = (endpoint: string, datasetId?: number) => {
  return api.get('/api/pricing/preview', { 
    params: { endpoint, dataset_id: datasetId } 
  });
};

// ----- DATASET BUILDER -----
export const buildDataset = () => {
  return api.post('/api/upload/build-dataset');
};

export const getDatasets = (limit: number = 10) => {
  return api.get('/api/upload/datasets', { params: { limit } });
};

export const getDatasetDetail = (datasetId: number) => {
  return api.get(`/api/upload/dataset/${datasetId}`);
};

export const deleteDataset = (datasetId: number) => {
  return api.delete(`/api/upload/dataset/${datasetId}`);
};

// ----- ADMIN - ENDPOINT PROFİLLERİ -----
export const getEndpointProfiles = () => api.get('/admin/endpoint-profiles');
export const createEndpointProfile = (data: any) => api.post('/admin/endpoint-profiles', data);
export const updateEndpointProfile = (id: number, data: any) => api.put(`/admin/endpoint-profiles/${id}`, data);
export const deleteEndpointProfile = (id: number) => api.delete(`/admin/endpoint-profiles/${id}`);
export const initDefaultEndpointProfiles = () => api.post('/admin/endpoint-profiles/init-defaults');

// ----- ADMIN - SCORE RANGES -----
export const getScoreRanges = () => api.get('/admin/score-ranges');
export const createScoreRange = (data: any) => api.post('/admin/score-ranges', data);
export const updateScoreRange = (id: number, data: any) => api.put(`/admin/score-ranges/${id}`, data);
export const deleteScoreRange = (id: number) => api.delete(`/admin/score-ranges/${id}`);
export const initDefaultScoreRanges = () => api.post('/admin/score-ranges/init-defaults');

// ----- ADMIN - PROCESSING TRANSACTIONS -----
export const getProcessingTransactions = (limit: number = 100, offset: number = 0) => {
  return api.get('/admin/processing-transactions', { params: { limit, offset } });
};

export const getUserProcessingTransactions = (userId: number, limit: number = 50, offset: number = 0) => {
  return api.get(`/admin/processing-transactions/user/${userId}`, { params: { limit, offset } });
};