// frontend/src/utils/loadAnalysisResult.ts

import api from '../services/api';

export const fetchAndLoadResult = async (
  analysisId: number,
  setData: (data: any) => void,
  setPage: (page: number) => void,
  setSuccess: (msg: string) => void,
  setError: (msg: string) => void,
  setLoading: (loading: boolean) => void
) => {
  try {
    setLoading(true);
    const res = await api.get(`/api/upload/results?limit=100`);
    if (res.data.success) {
      const results = res.data.results || [];
      const found = results.find((item: any) => item.id === analysisId);
      if (found) {
        // 🔥 Her sayfa farklı data yapısına sahip olabilir
        // forecast: found.data.results
        // safety_stock: found.data.results
        // simulation: found.data.results
        // backtest: found.data.results
        // supplier: found.data.suppliers
        const resultData = found.data?.results || found.data?.suppliers || [];
        setData(resultData);
        setPage(0);
        setSuccess(`${resultData.length} sonuç yüklendi.`);
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError('Analiz sonucu bulunamadı.');
      }
    }
  } catch (err: any) {
    console.error('❌ Sonuç yükleme hatası:', err);
    setError(err.response?.data?.detail || 'Sonuç yüklenemedi.');
  } finally {
    setLoading(false);
  }
};

export const checkAndLoadAnalysis = (
  resultType: string,
  fetchAndLoadResultFn: (id: number) => void
) => {
  const loadId = sessionStorage.getItem('loadAnalysisId');
  const loadType = sessionStorage.getItem('loadAnalysisType');
  
  console.log(`🔍 checkAndLoadAnalysis: type=${resultType}, loadId=${loadId}, loadType=${loadType}`);
  
  if (loadId && loadType && loadType.includes(resultType)) {
    console.log(`✅ Analiz yükleniyor: ${resultType}, ID: ${loadId}`);
    fetchAndLoadResultFn(parseInt(loadId));
    sessionStorage.removeItem('loadAnalysisId');
    sessionStorage.removeItem('loadAnalysisType');
  }
};