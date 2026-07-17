// frontend/src/hooks/useAuth.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { login as apiLogin, register as apiRegister, getUser } from '../services/auth';
import api from '../services/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  company_name: string;
  token_balance: number;
  sector_id: number | null;
  sector_name?: string | null;
  created_at: string;
  polar_customer_id?: string;
  billing_address?: string;
  billing_city?: string;
  billing_state?: string;
  billing_country?: string;
  billing_postal_code?: string;
  tax_id?: string;
  tax_office?: string;
  identity_number?: string;
}

interface RegisterParams {
  email: string;
  password: string;
  full_name?: string;
  company_name?: string;
  sector_id?: number | null;
  billing_address?: string;
  billing_city?: string;
  billing_state?: string;
  billing_country?: string;
  billing_postal_code?: string;
  tax_id?: string;
  tax_office?: string;
  identity_number?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (params: RegisterParams) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  updateUser: (userData: Partial<User>) => void;
  refreshToken: () => Promise<boolean>;
  refreshUser: () => Promise<void>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const data = await apiLogin(email, password);
          const userData = await getUser(data.access_token);
          console.log('👤 Login sonrası user:', userData);
          set({
            token: data.access_token,
            user: userData,
            isLoading: false,
          });
          return true;
        } catch (err: unknown) {
          console.error('Login error:', err);
          let errorMessage = 'Giriş başarısız';
          if (err && typeof err === 'object' && 'response' in err) {
            const axiosError = err as { response?: { data?: { detail?: string } } };
            if (axiosError.response?.data?.detail) {
              errorMessage = axiosError.response.data.detail;
            }
          } else if (err instanceof Error) {
            errorMessage = err.message;
          }
          set({
            error: errorMessage,
            isLoading: false,
          });
          return false;
        }
      },

      // ✅ GÜNCELLENMİŞ register fonksiyonu
      register: async (params: RegisterParams) => {
        set({ isLoading: true, error: null });
        try {
          await apiRegister({
            email: params.email,
            password: params.password,
            full_name: params.full_name || '',
            company_name: params.company_name || '',
            sector_id: params.sector_id || null,
            billing_address: params.billing_address || '',
            billing_city: params.billing_city || '',
            billing_state: params.billing_state || '',
            billing_country: params.billing_country || 'TR',
            billing_postal_code: params.billing_postal_code || '',
            tax_id: params.tax_id || '',
            tax_office: params.tax_office || '',
            identity_number: params.identity_number || '',
          });
          const success = await get().login(params.email, params.password);
          set({ isLoading: false });
          return success;
        } catch (err: unknown) {
          console.error('Register error:', err);
          let errorMessage = 'Kayıt başarısız';
          if (err && typeof err === 'object' && 'response' in err) {
            const axiosError = err as { response?: { data?: { detail?: string } } };
            if (axiosError.response?.data?.detail) {
              errorMessage = axiosError.response.data.detail;
            }
          } else if (err instanceof Error) {
            errorMessage = err.message;
          }
          set({
            error: errorMessage,
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

      refreshUser: async () => {
        const { token } = get();
        if (!token) {
          set({ user: null });
          return;
        }
        try {
          const userData = await getUser(token);
          set({ user: userData });
          console.log('🔄 Kullanıcı bilgileri yenilendi:', userData);
        } catch (err: unknown) {
          console.error('❌ Kullanıcı bilgisi yenilenemedi:', err);
          if (err && typeof err === 'object' && 'response' in err) {
            const axiosError = err as { response?: { status?: number } };
            if (axiosError.response?.status === 401) {
              get().logout();
            }
          }
        }
      },

      clearError: () => set({ error: null }),

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } });
        }
      },

      refreshToken: async () => {
        const { token } = get();
        if (!token) return false;
        try {
          const userData = await getUser(token);
          set({ user: userData });
          return true;
        } catch (err: unknown) {
          console.error('Token yenileme hatası:', err);
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

export default useAuth;