// frontend/src/hooks/useLearningScore.ts - GÜNCELLENDİ

import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface LearningScoreData {
  score: number;
  level: 'Uzman' | 'İleri' | 'Orta' | 'Başlangıç' | 'Öğreniyor' | 'Hata';
  percentage: number;
  components: {
    analysis_count: {
      score: number;
      max: number;
      value: number;
      label: string;
    };
    verified_rules: {
      score: number;
      max: number;
      value: number;
      label: string;
    };
    data_quality: {
      score: number;
      max: number;
      value: number;
      label: string;
    };
    forecast_accuracy: {
      score: number;
      max: number;
      value: number;
      label: string;
    };
    ai_confidence: {
      score: number;
      max: number;
      value: number;
      label: string;
    };
  };
  error?: string;
}

export interface LearningScoreResponse {
  success: boolean;
  data: LearningScoreData;
}

export const useLearningScore = () => {
  return useQuery({
    queryKey: ['learning-score'],
    queryFn: async (): Promise<LearningScoreData | null> => {
      try {
        const response = await api.get<LearningScoreResponse>('/api/learning/score');
        console.log('📊 Learning Score API Yanıtı:', response.data);
        
        if (response.data.success) {
          return response.data.data;
        }
        return null;
      } catch (error) {
        console.error('❌ Learning Score alınamadı:', error);
        return null;
      }
    },
    // ✅ CACHE SÜRESİNİ AZALT - Her seferinde taze veri al
    staleTime: 0, // Her zaman taze veri al
    gcTime: 0, // Cache'leme yapma
    refetchOnWindowFocus: true, // Pencere odaklandığında yenile
    refetchOnMount: true, // Mount olduğunda yenile
    refetchOnReconnect: true, // Yeniden bağlandığında yenile
  });
};