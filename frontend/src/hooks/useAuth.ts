import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { login as apiLogin, register as apiRegister, getUser } from '../services/auth';
import api from '../services/api';

interface AuthState {
  user: any | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, fullName?: string, companyName?: string, sectorId?: number | null) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  updateUser: (userData: any) => void;
  refreshToken: () => Promise<boolean>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,
      login: async (email, password) => {
        console.log('🔥 LOGIN FONKSİYONU ÇAĞRILDI!');  // BU SATIRI EKLE
        set({ isLoading: true, error: null });
        try {
          const data = await apiLogin(email, password);
          // Login'den gelen token ile /auth/me'yi çağır
          const userData = await getUser(data.access_token);
          console.log('👤 /auth/me cevabı:', userData);  // Konsolda gör
          set({
            token: data.access_token,
            user: userData,  // ✅ Direkt kullan
            isLoading: false,
          });
          return true;
        } catch (err: any) {
          console.error('Login error:', err);
          set({
            error: err.response?.data?.detail || 'Giriş başarısız',
            isLoading: false,
          });
          return false;
        }
      },

      register: async (email, password, fullName = '', companyName = '', sectorId = null) => {
        set({ isLoading: true, error: null });
        try {
          await apiRegister(email, password, fullName, companyName, sectorId);
          const success = await get().login(email, password);
          set({ isLoading: false });
          return success;
        } catch (err: any) {
          console.error('Register error:', err);
          set({
            error: err.response?.data?.detail || 'Kayıt başarısız',
            isLoading: false,
          });
          return false;
        }
      },
      logout: () => {
        set({ user: null, token: null, error: null });
        localStorage.removeItem('auth-storage');
      },
      fetchUser: async () => {
        const { token } = get();
        if (token) {
          try {
            const user = await getUser(token);
            set({ user });
          } catch {
            get().logout();
          }
        }
      },
      clearError: () => set({ error: null }),
      updateUser: (userData: any) => {
        set({ user: userData });
      },
      refreshToken: async () => {
        const { token } = get();
        if (!token) return false;
        try {
          const userData = await getUser(token);
          set({ user: userData });
          return true;
        } catch (error) {
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
);

// Token süresi dolduğunda otomatik yenileme için interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const { refreshToken, logout } = useAuth.getState();
      const success = await refreshToken();
      if (success) {
        const newToken = useAuth.getState().token;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } else {
        logout();
      }
    }
    return Promise.reject(error);
  }
);