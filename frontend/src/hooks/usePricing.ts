// frontend/src/hooks/usePricing.ts - GÜNCELLENMİŞ (export eklendi)

import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface PricingPreview {
  endpoint: string;
  dataset_id: number;
  product_count: number;
  period_count: number;
  data_points: number;
  algorithm_weight: number;
  processing_score: number;
  estimated_credit_cost: number;
  current_balance: number;
  is_sufficient: boolean;
  calculation_method?: string;
  breakdown?: any;
}

// 📌 Global olarak dataset ID'yi tutalım
let cachedDatasetId: number | null = null;

export function usePricingPreview(endpoint: string, datasetId?: number | null) {
  return useQuery({
    queryKey: ['pricing-preview', endpoint, datasetId || cachedDatasetId],
    queryFn: async () => {
      // 1. Önce parametreden dene
      let activeDatasetId = datasetId || cachedDatasetId;
      
      // 2. Yoksa localStorage'dan dene
      if (!activeDatasetId) {
        const saved = localStorage.getItem('activeDatasetId');
        if (saved) {
          activeDatasetId = parseInt(saved);
          cachedDatasetId = activeDatasetId;
        }
      }
      
      // 3. Hala yoksa API'den al
      if (!activeDatasetId) {
        try {
          const res = await api.get('/api/upload/datasets');
          if (res.data.success && res.data.datasets?.length > 0) {
            const firstDataset = res.data.datasets[0];
            activeDatasetId = firstDataset.id;
            cachedDatasetId = activeDatasetId;
            localStorage.setItem('activeDatasetId', String(activeDatasetId));
          }
        } catch (error) {
          console.error('❌ Dataset alınamadı:', error);
        }
      }
      
      // 4. Hala yoksa fallback
      if (!activeDatasetId) {
        return { 
          is_sufficient: true, 
          estimated_credit_cost: 0,
          current_balance: 0,
          data_points: 0,
          processing_score: 0,
          product_count: 0,
          period_count: 0,
          algorithm_weight: 0,
          endpoint: endpoint,
          dataset_id: 0,
        } as PricingPreview;
      }
      
      // 5. Pricing Preview çağır
      try {
        const res = await api.get('/api/pricing/preview', { 
          params: { endpoint, dataset_id: activeDatasetId } 
        });
        return res.data as PricingPreview;
      } catch (error) {
        console.error('❌ Pricing preview hatası:', error);
        return { 
          is_sufficient: true, 
          estimated_credit_cost: 0,
          current_balance: 0,
          data_points: 0,
          processing_score: 0,
          product_count: 0,
          period_count: 0,
          algorithm_weight: 0,
          endpoint: endpoint,
          dataset_id: activeDatasetId,
        } as PricingPreview;
      }
    },
    enabled: true, // Her zaman çalışsın
    staleTime: 60000,
    retry: 1,
  });
}

// ✅ BU FONKSİYONU EXPORT ET
export function updateActiveDatasetId(datasetId: number) {
  cachedDatasetId = datasetId;
  localStorage.setItem('activeDatasetId', String(datasetId));
}

// ✅ Dataset ID'yi almak için yardımcı fonksiyon
export function getActiveDatasetId(): number | null {
  return cachedDatasetId || null;
}