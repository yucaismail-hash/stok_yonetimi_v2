import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const login = async (email: string, password: string) => {
  const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
  return res.data;
};

export const register = async (
  email: string,
  password: string,
  fullName: string = '',
  companyName: string = '',
  sectorId: number | null = null
) => {
  const res = await axios.post(`${API_BASE}/auth/register`, {
    email,
    password,
    full_name: fullName,
    company_name: companyName,
    sector_id: sectorId,
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