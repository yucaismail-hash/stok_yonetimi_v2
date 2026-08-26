// frontend/src/services/auth.ts

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
  company_name: string;
}

export const login = async (email: string, password: string) => {
  const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
  return res.data;
};

// ✅ GÜNCELLENMİŞ register fonksiyonu
export const register = async (data: RegisterData) => {
  const res = await axios.post(`${API_BASE}/auth/register`, {
    email: data.email,
    password: data.password,
    full_name: data.full_name || '',
    company_name: data.company_name,
  });
  return res.data;
};

export const getUser = async (token: string) => {
  const res = await axios.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};
