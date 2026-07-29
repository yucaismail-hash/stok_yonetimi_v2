// frontend/src/hooks/useCompanyMemory.ts
// Company Memory Hook - Şirket hafızasındaki öğrenilmiş kuralları getirir

import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface CompanyRule {
  id: number;
  rule_id: string;
  rule_name: string;
  rule_type: 'seasonal' | 'intermittent' | 'lead_time' | 'trend' | 'supplier' | 'successful_method';
  description: string;
  pattern_data: Record<string, any>;
  confidence_score: number;
  usage_count: number;
  is_verified: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

export interface CompanyMemoryResponse {
  success: boolean;
  total: number;
  rules: CompanyRule[];
}

export const useCompanyMemory = (limit: number = 50) => {
  return useQuery({
    queryKey: ['company-memory', limit],
    queryFn: async (): Promise<CompanyRule[]> => {
      try {
        const response = await api.get<CompanyMemoryResponse>(`/api/learning/memory?limit=${limit}`);
        if (response.data.success) {
          return response.data.rules;
        }
        return [];
      } catch (error) {
        console.error('❌ Company Memory alınamadı:', error);
        return [];
      }
    },
    staleTime: 10 * 60 * 1000, // 10 dakika
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
};

export const useVerifiedRules = () => {
  return useQuery({
    queryKey: ['verified-rules'],
    queryFn: async (): Promise<CompanyRule[]> => {
      try {
        const response = await api.get<CompanyMemoryResponse>('/api/learning/memory/verified');
        if (response.data.success) {
          return response.data.rules;
        }
        return [];
      } catch (error) {
        console.error('❌ Doğrulanmış kurallar alınamadı:', error);
        return [];
      }
    },
    staleTime: 15 * 60 * 1000, // 15 dakika
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
};