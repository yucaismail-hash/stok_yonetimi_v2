// frontend/src/services/auth.ts

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface RegisterData {
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
    company_name: data.company_name || '',
    sector_id: data.sector_id || null,
    billing_address: data.billing_address || '',
    billing_city: data.billing_city || '',
    billing_state: data.billing_state || '',
    billing_country: data.billing_country || 'TR',
    billing_postal_code: data.billing_postal_code || '',
    tax_id: data.tax_id || '',
    tax_office: data.tax_office || '',
    identity_number: data.identity_number || '',
  });
  return res.data;
};

export const getUser = async (token: string) => {
  const res = await axios.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  console.log('🔍 getUser cevabı:', res.data);
  return res.data;
};