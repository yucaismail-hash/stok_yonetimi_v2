// frontend/src/pages/BacktestPage.tsx - TAM VE DÜZELTİLMİŞ

import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  TablePagination,
  Tooltip,
  Stack,
  Slider,
  LinearProgress,
  Snackbar,
  Avatar,
  alpha,
  // ✅ EKSİK IMPORT'LAR
  Stepper,
  Step,
  StepLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  School,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  AutoAwesome,
  CloudDone,
  CloudOff,
  Inventory,
  AttachMoney,
  Lightbulb,
  Speed,
  Psychology,
  Warning as WarningIcon,
  TrendingUp,
  TrendingDown,
  Timeline,
  Analytics,
  Star,
  ShowChart,
  AccountBalanceWallet,
  ExpandMore,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import { usePricingPreview } from '../../hooks/usePricing';
import { fetchAndLoadResult, checkAndLoadAnalysis } from '../../utils/loadAnalysisResult';

// ✅ YENİ BİLEŞENLER
import DecisionReasoning from '../../components/Results/DecisionReasoning';
import TechnicalAnalysisDetail from '../../components/Results/TechnicalAnalysisDetail';
import LearningScoreBadge from '../../components/Dashboard/LearningScoreBadge';

// ============================================================
// 📌 STRATEJİ LABELLARI VE RENKLERİ (DOSYA İÇİNDE TANIMLA)
// ============================================================

const strategyLabels: Record<string, string> = {
  ai: 'AI',
  classic: 'Klasik',
  croston: 'Croston',
  syntetos_boylan: 'SB',
  ml: 'ML',
  hybrid: 'Hibrit',
  simple_moving_avg: 'MA',
  last_value: 'Naif',
};

const strategyColors: Record<string, string> = {
  ai: '#9c27b0',
  classic: '#1976d2',
  croston: '#2e7d32',
  syntetos_boylan: '#ed6c02',
  ml: '#d32f2f',
  hybrid: '#1f4e79',
  simple_moving_avg: '#00897b',
  last_value: '#6d4c41',
};

// ============================================================
// 📌 STRATEJİ DETAYLARI (DOSYA İÇİNDE TANIMLA)
// ============================================================

interface StrategyDetail {
  key: string;
  label: string;
  icon: React.ReactNode;
  short: string;
  tooltip: {
    title: string;
    when: string;
    example: string;
    advantage: string;
  };
  isRecommended?: boolean;
}

const strategyDetails: StrategyDetail[] = [
  {
    key: 'ai',
    label: 'AI',
    icon: <Psychology fontSize="small" />,
    short: 'Yapay zeka kararı',
    tooltip: {
      title: 'AI Stratejisi',
      when: 'Karmaşık talep yapısı, pattern multiplier kullanır.',
      example: 'Değişken talep, çoklu SKU, e-ticaret.',
      advantage: 'Geçmiş verilerden öğrenir, kullanıldıkça gelişir.',
    },
  },
  {
    key: 'classic',
    label: 'Klasik',
    icon: <Timeline fontSize="small" />,
    short: 'Normal dağılım',
    tooltip: {
      title: 'Klasik Strateji',
      when: 'Normal dağılım gösteren istikrarlı talepler.',
      example: 'Temel tüketim ürünleri, gıda maddeleri.',
      advantage: 'Basit, anlaşılır, sektörde yaygın kabul görür.',
    },
  },
  {
    key: 'croston',
    label: 'Croston',
    icon: <Analytics fontSize="small" />,
    short: 'Aralıklı talep',
    tooltip: {
      title: 'Croston Stratejisi',
      when: 'Aralıklı ve seyrek talep gösteren ürünler.',
      example: 'Yedek parçalar, bakım ekipmanları.',
      advantage: 'Talep olmayan dönemleri hesaba katar.',
    },
  },
  {
    key: 'syntetos_boylan',
    label: 'SB',
    icon: <Analytics fontSize="small" />,
    short: 'Croston gelişmiş',
    tooltip: {
      title: 'Syntetos-Boylan Stratejisi',
      when: 'Aralıklı talep (Croston\'un gelişmiş hali).',
      example: 'Nadir satılan ürünler, mevsimlik ürünler.',
      advantage: 'Croston\'un sistematik hatasını düzeltir.',
    },
  },
  {
    key: 'ml',
    label: 'ML',
    icon: <Psychology fontSize="small" />,
    short: 'Makine öğrenmesi',
    tooltip: {
      title: 'ML Stratejisi',
      when: 'CV, zero_ratio, trend ile desteklenir.',
      example: 'Veri zengini ürünler, büyük veri setleri.',
      advantage: 'Geçmiş verilerden öğrenir, adaptif.',
    },
  },
  {
    key: 'hybrid',
    label: 'Hibrit',
    icon: <Star fontSize="small" />,
    short: '⭐ Önerilen',
    tooltip: {
      title: 'Hibrit Strateji',
      when: 'Tüm talep türleri için uygun, en çok önerilen.',
      example: 'Tüm ürün grupları için ideal başlangıç.',
      advantage: 'Tüm stratejileri değerlendirir, en uygununu seçer.',
    },
    isRecommended: true,
  },
  {
    key: 'simple_moving_avg',
    label: 'MA',
    icon: <ShowChart fontSize="small" />,
    short: 'Basit hareketli ortalama',
    tooltip: {
      title: 'Simple Moving Average',
      when: 'Son 4 hafta ortalaması ile hızlı tahmin.',
      example: 'Yeni ürünler, az geçmişi olan ürünler.',
      advantage: 'Basit ve hızlı, az veri ile çalışabilir.',
    },
  },
  {
    key: 'last_value',
    label: 'Naif',
    icon: <TrendingUp fontSize="small" />,
    short: 'Son değer (naif)',
    tooltip: {
      title: 'Naif Strateji',
      when: 'En son değeri gelecek tahmini olarak kullanır.',
      example: 'Yeni ürünler, hiç geçmişi olmayan ürünler.',
      advantage: 'En basit yöntem, başlangıç için idealdir.',
    },
  },
];

// ============================================================
// 📌 INTERFACES
// ============================================================

interface BacktestResult {
  material_code: string;
  group: string;
  best_strategy: string;
  service_level: number;
  total_cost: number;
  holding_cost: number;
  shortage_cost: number;
  stockout_probability: number;
  tail_risk: number;
  tail_risk_level: string;
  total_shortage: number;
  strategies_tested: number;
  strategy_details: any;
  recommendation: string;
  current_rop: number;
  recommended_rop: number;
  ai_decision?: {
    decision: string;
    priority: string;
    confidence: number;
    reasons: string[];
    expected_impact: Record<string, string>;
    next_review_days: number;
    explanation: string;
    analysis_type: string;
  };
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

interface AnalysisStep {
  label: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  timestamp?: string;
}

interface AnalysisSummary {
  totalMaterials: number;
  mostUsedModel: string;
  mostUsedModelPercent: number;
  avgRMSE: number;
  trendUpCount: number;
  trendDownCount: number;
  modelDistribution: Record<string, number>;
  bestMaterial: string;
  worstMaterial: string;
  bestRMSE: number;
  worstRMSE: number;
  seasonalityLevel: string;
}

interface AIComment {
  summary: string;
  trend: string;
  seasonality: string;
  confidence: string;
  recommendation: string;
}

// ============================================================
// 📌 AI REASONING SECTION BİLEŞENİ
// ============================================================

const AIReasoningSection = ({ result }: { result: BacktestResult }) => {
  const aiDecision = result.ai_decision;
  
  if (!aiDecision) {
    return null;
  }

  const reasoning = {
    recommended_ss: result.recommended_rop || 0,
    current_ss: result.current_rop || 0,
    reasons: aiDecision.reasons || [
      result.service_level < 0.85 ? 'Servis seviyesi düşük' : '',
      result.tail_risk > 0.5 ? 'Tail risk yüksek' : '',
      result.stockout_probability > 10 ? 'Stok tükenme riski yüksek' : '',
      result.best_strategy ? `En iyi strateji: ${result.best_strategy}` : '',
    ].filter(Boolean),
    conclusion: aiDecision.decision === 'change_forecast_model' 
      ? `En iyi strateji: ${result.best_strategy}` 
      : aiDecision.decision === 'maintain_current'
      ? 'Mevcut strateji yeterli.'
      : 'Detaylı analiz önerilir.',
    confidence: aiDecision.confidence || 0.5,
    factors: {
      cv: 0,
      lead_time: 0,
      intermittent: false,
      seasonal: false,
      risk_score: result.tail_risk || 0,
      pattern: result.tail_risk > 0.5 ? 'Yüksek Risk' : 'Düşük Risk',
    }
  };

  return (
    <Box sx={{ mt: 1 }}>
      <DecisionReasoning
        materialCode={result.material_code}
        reasoning={reasoning}
      />
    </Box>
  );
};

// ============================================================
// 📌 TEKNİK ANALİZ BÖLÜMÜ - ACCORDION
// ============================================================

const TechnicalAnalysisSection = ({ result }: { result: BacktestResult }) => {
  const [expanded, setExpanded] = useState(false);

  const technicalData = {
    material_code: result.material_code,
    cv: result.tail_risk || 0,
    pattern: result.tail_risk > 0.5 ? 'YUKSEK_RISK' : 'DUSUK_RISK',
    pattern_label: result.tail_risk > 0.5 ? 'Yüksek Risk' : 'Düşük Risk',
    pattern_color: result.tail_risk > 0.5 ? 'error' : 'success',
    abc: 'C',
    abc_label: 'Backtest',
    xyz: result.tail_risk > 0.5 ? 'Z' : 'X',
    xyz_label: result.tail_risk > 0.5 ? 'Yüksek Risk' : 'Düşük Risk',
    forecast_model: result.best_strategy || 'hybrid',
    forecast_model_label: result.best_strategy || 'Hibrit',
    seasonality: false,
    seasonality_label: 'Yok',
    seasonality_strength: 0,
    trend_direction: result.service_level > 0.95 ? 'Artış' : 'Azalış',
    trend_percent: 0,
    lead_time_days: 14,
    zero_ratio: 0,
    risk_score: result.tail_risk || 0,
    risk_level: result.tail_risk > 0.5 ? 'Yüksek' : 'Düşük',
  };

  return (
    <Accordion 
      expanded={expanded} 
      onChange={() => setExpanded(!expanded)}
      sx={{ 
        mt: 1, 
        '&:before': { display: 'none' },
        border: '1px solid #e8f0fe',
        borderRadius: 1,
      }}
    >
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.7rem', color: '#1f4e79' }}>
          📊 Teknik Analizi Göster
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        <TechnicalAnalysisDetail data={technicalData} />
      </AccordionDetails>
    </Accordion>
  );
};

// ============================================================
// 📌 ANALİZ AŞAMALARI BİLEŞENİ
// ============================================================

const AnalysisProgress = ({ 
  steps, 
  activeStep, 
  isComplete,
  compact = false,
}: { 
  steps: AnalysisStep[]; 
  activeStep: number; 
  isComplete: boolean;
  compact?: boolean;
}) => {
  return (
    <Box sx={{ width: '100%' }}>
      <Stepper 
        activeStep={activeStep} 
        orientation="vertical" 
        sx={{ 
          '& .MuiStepConnector-line': { display: 'none' },
          '& .MuiStep-root': { 
            padding: compact ? '2px 0' : '4px 0',
          },
        }}
      >
        {steps.map((step, index) => {
          const isActive = index === activeStep;
          const isCompleted = index < activeStep || (isComplete && index === activeStep);
          const isError = step.status === 'error';

          const getStepIcon = () => {
            if (isError) return <Error color="error" fontSize="small" />;
            if (isCompleted) return <CheckCircle color="success" fontSize="small" />;
            if (isActive) return <CircularProgress size={14} />;
            return <Pending color="disabled" fontSize="small" />;
          };

          return (
            <Step key={index} completed={isCompleted}>
              <StepLabel
                icon={getStepIcon()}
                sx={{
                  '& .MuiStepLabel-label': {
                    color: isActive ? '#1f4e79' : isCompleted ? '#2e7d32' : '#9e9e9e',
                    fontWeight: isActive ? 600 : 400,
                    fontSize: compact ? '0.7rem' : '0.75rem',
                  },
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                  <Typography variant="body2" sx={{ fontWeight: isActive ? 600 : 400, fontSize: compact ? '0.7rem' : '0.75rem' }}>
                    {step.label}
                  </Typography>
                  {step.timestamp && (
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 1, fontSize: '0.55rem' }}>
                      {step.timestamp}
                    </Typography>
                  )}
                </Box>
                {!compact && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25, fontSize: '0.6rem' }}>
                    {step.description}
                  </Typography>
                )}
              </StepLabel>
            </Step>
          );
        })}
      </Stepper>
    </Box>
  );
};

// ============================================================
// 📌 ANA SAYFA BİLEŞENİ
// ============================================================

export default function BacktestPage() {
  const { user, fetchUser } = useAuth();

  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [materialCount, setMaterialCount] = useState(0);
  const [maxAvailableWeeks, setMaxAvailableWeeks] = useState(0);

  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDataValid, setIsDataValid] = useState<boolean>(true);
  const [testWindow, setTestWindow] = useState(8);

  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // 🆕 Dataset ID için state
  const [activeDatasetId, setActiveDatasetId] = useState<number | null>(() => {
    const saved = localStorage.getItem('activeDatasetId');
    return saved ? parseInt(saved) : null;
  });

  // 🆕 Pricing Preview Hook
  const { data: pricingPreview, isLoading: pricingLoading } = usePricingPreview(
    '/api/backtest/batch',
    activeDatasetId || undefined
  );
    
    // 🆕 Dataset ID'yi al
  useEffect(() => {
    const fetchDataset = async () => {
      if (!activeDatasetId) {
        try {
          const res = await api.get('/api/upload/datasets');
          if (res.data.success && res.data.datasets?.length > 0) {
            const firstDataset = res.data.datasets[0];
            setActiveDatasetId(firstDataset.id);
            localStorage.setItem('activeDatasetId', String(firstDataset.id));
          }
        } catch (error) {
          console.error('❌ Dataset alınamadı:', error);
        }
      }
    };
    fetchDataset();
  }, [activeDatasetId]);

  // fetchAndLoadResult fonksiyonunu tanımla
  const handleFetchAndLoad = (id: number) => {
    fetchAndLoadResult(id, setResults, setPage, setSuccess, setError, setLoading);
  };

  useEffect(() => {
    checkAndLoadAnalysis('backtest', handleFetchAndLoad);
  }, []);


  const validateDataForBacktest = (testWindowValue: number, availableWeeks: number) => {
    const minRequired = Math.max(8, testWindowValue + 4);

    if (availableWeeks === 0) {
      setValidationError('📊 Veri yüklenmemiş! Lütfen önce Excel dosyası yükleyin.');
      setIsDataValid(false);
      return false;
    }

    if (availableWeeks < minRequired) {
      setValidationError(
        `⚠️ Yetersiz veri! Yüklenen veriniz ${availableWeeks} hafta, backtest için en az ${minRequired} hafta gerekiyor. ` +
          `(Test penceresi: ${testWindowValue} hafta)`
      );
      setIsDataValid(false);
      return false;
    }

    setValidationError(null);
    setIsDataValid(true);
    return true;
  };

  const checkDataAvailability = async () => {
    try {
      const res = await api.get('/api/upload/status');
      if (res.data.has_data) {
        const weekCount = res.data.week_count || 0;
        setMaxAvailableWeeks(weekCount);
        setMaterialCount(res.data.materials_count || 0);
        validateDataForBacktest(testWindow, weekCount);
      } else {
        setMaxAvailableWeeks(0);
        setValidationError('📊 Henüz Excel dosyası yüklenmemiş!');
        setIsDataValid(false);
      }
    } catch (error) {
      console.error('❌ Veri kontrol hatası:', error);
    }
  };

  const checkUploadedData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/upload/status');
      const hasData = res.data.has_data === true;
      setHasUploadedData(hasData);

      if (hasData) {
        await checkDataAvailability();
      } else {
        setError('Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard\'dan dosya yükleyin.');
        setValidationError('📊 Henüz Excel dosyası yüklenmemiş!');
        setIsDataValid(false);
      }
    } catch (error) {
      console.error('❌ Veri kontrolü hatası:', error);
      setHasUploadedData(false);
      setError('Veri kontrolü sırasında hata oluştu.');
    } finally {
      setIsCheckingData(false);
    }
  };

  const handleSliderChange = (_event: Event, value: number | number[]) => {
    const newValue = Array.isArray(value) ? value[0] : value;
    setTestWindow(newValue);

    if (maxAvailableWeeks > 0) {
      validateDataForBacktest(newValue, maxAvailableWeeks);
    } else {
      setValidationError('📊 Henüz Excel dosyası yüklenmemiş! Lütfen önce veri yükleyin.');
      setIsDataValid(false);
    }
  };

  useEffect(() => {
    checkUploadedData();
  }, []);

  // 📌 SENKRON Backtest
  const backtestMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Backtest başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/backtest/batch', {
        test_window: testWindow,
      });
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla test edildi.`);
        setTimeout(() => setSuccess(null), 5000);
        await fetchUser();
        
        // ✅ Yeni: credit_cost ve balance_after'i göster
        if (data.credit_cost !== undefined) {
          setSnackbar({
            open: true,
            message: `💰 ${data.credit_cost} kredi harcandı. Kalan: ${data.balance_after} kredi. Processing Score: ${data.processing_score || '-'}`,
            severity: 'info',
          });
        }
      } else {
        setError(data.error || 'Backtest başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Backtest hatası:', err);
      setError(err.response?.data?.detail || 'Backtest sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Backtest
  const asyncBacktestMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async backtest başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/backtest/batch/async', {
        test_window: testWindow,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setActiveAsyncTask(data.task_id);
      setSnackbar({
        open: true,
        message: `✅ Rapor talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0, 8)}\n💰 Kredi: ${data.credit_cost || 0}, Kalan: ${data.balance_after || 0}`,
        severity: 'success',
      });
      setProgress(10);
      setProgressLabel('İşlem kuyruğa alındı.');
      setIsProcessing(false);

      const intervalId = setInterval(() => {
        checkAsyncProgress(data.task_id);
      }, 3000);

      setTimeout(() => {
        clearInterval(intervalId);
        if (isProcessing) {
          setIsProcessing(false);
          setActiveAsyncTask(null);
          setError('Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.');
        }
      }, 300000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Async backtest başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
    },
  });

  const checkAsyncProgress = async (taskId: string) => {
    if (!taskId) return;
    try {
      const res = await api.get(`/api/tasks/async/${taskId}`);
      const status = res.data.task;

      setProgress(status.progress || 50);
      setProgressLabel(status.message || 'İşleniyor...');

      if (status.status === 'completed') {
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(100);
        setProgressLabel('Tamamlandı!');

        const resultsRes = await api.get(`/api/tasks/async/${taskId}`);
        if (resultsRes.data.task?.results) {
          setResults(resultsRes.data.task.results || []);
          setPage(0);
          setSuccess(`${resultsRes.data.task.total || 0} malzeme başarıyla test edildi.`);
          setTimeout(() => setSuccess(null), 5000);
          await fetchUser();
        }
        return;
      }

      if (status.status === 'failed' || status.status === 'error') {
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(0);
        setProgressLabel('Hata!');
        setError(status.message || 'Async backtest başarısız oldu');
      }
    } catch (error) {
      console.error('Async durum kontrol hatası:', error);
      setIsProcessing(false);
      setActiveAsyncTask(null);
      setError('Async durum kontrolü başarısız');
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'backtest_batch', limit: 10000 },
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        const batchResults = rawResults.filter((item: any) => item.is_batch === true);

        const historyItems = batchResults.map((item: any) => {
          const data = item.data || {};
          const totalMaterials = item.total_materials || data.total || 0;
          const testWindowVal = data?.test_window || 8;

          let bestStrategy = 'hybrid';
          const resultsData = data?.results || [];
          if (resultsData.length > 0) {
            const counts: Record<string, number> = {};
            resultsData.forEach((r: any) => {
              const strat = r.best_strategy || 'hybrid';
              counts[strat] = (counts[strat] || 0) + 1;
            });
            const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
            bestStrategy = sorted[0]?.[0] || 'hybrid';
          }

          const bestStrategyLabel = strategyLabels[bestStrategy] || bestStrategy;
          const reportName = `Backtest (${testWindowVal} hafta) - ${bestStrategyLabel} - ${totalMaterials} Malzeme`;

          return {
            id: item.id,
            created_at: item.created_at,
            data: {
              total: totalMaterials,
              results: data.results || [],
              report_name: reportName,
              status: item.status || 'completed',
              test_window: testWindowVal,
              best_strategy: bestStrategy,
            },
          };
        });

        setHistoryData(historyItems);
        setHistoryDialogOpen(true);
        setError(null);
      } else {
        setError('Geçmiş sonuçlar yüklenemedi');
      }
    } catch (err: any) {
      console.error('❌ Geçmiş hatası:', err);
      setError(err.response?.data?.detail || 'Geçmiş sonuçlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleViewHistory = (item: HistoryItem) => {
    const historyResults = item.data?.results || [];
    if (historyResults.length > 0) {
      setResults(historyResults);
      setPage(0);
      setHistoryDialogOpen(false);
      setSuccess(`${historyResults.length} malzeme geçmiş sonuçları yüklendi.`);
      setTimeout(() => setSuccess(null), 3000);
    } else {
      setError('Bu kayıtta görüntülenecek sonuç yok');
    }
  };

  const handleExport = async () => {
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }
    try {
      const response = await api.post(
        '/api/export/backtest-results',
        { results: results },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backtest_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Excel dosyası başarıyla indirildi.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Excel dosyası oluşturulamadı');
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => setPage(newPage);
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const paginatedResults = results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getRiskColor = (value: number) => {
    if (value <= 0.2) return 'success';
    if (value <= 0.4) return 'warning';
    return 'error';
  };

  return (
    <Box>
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={8000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          sx={{ whiteSpace: 'pre-line' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Hero Header */}
      <Card
        sx={{
          mb: 3,
          borderRadius: 2,
          bgcolor: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)',
          border: '1px solid #d0e0ff',
        }}
      >
        <CardContent sx={{ py: 2.5, px: 3 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              alignItems: { md: 'center' },
              justifyContent: 'space-between',
            }}
          >
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <School sx={{ fontSize: 24, color: '#1f4e79' }} />
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.3rem' }}>
                  Backtest Analizi
                </Typography>
                <Chip
                  label="Backtest"
                  size="small"
                  sx={{ height: 20, fontSize: '0.55rem', bgcolor: '#1f4e79', color: 'white' }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                8 farklı stratejiyi geçmiş veri üzerinde test eder. En iyi stratejiyi otomatik seçer.
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1.5, mt: { xs: 1.5, md: 0 }, flexWrap: 'wrap' }}>
              <Chip
                icon={<CheckCircle sx={{ fontSize: 14 }} />}
                label="8 strateji"
                size="small"
                variant="outlined"
                sx={{ height: 24, fontSize: '0.6rem' }}
              />
              <Chip
                icon={<AutoAwesome sx={{ fontSize: 14 }} />}
                label="Otomatik seçim"
                size="small"
                variant="outlined"
                sx={{ height: 24, fontSize: '0.6rem' }}
              />
              <Chip
                icon={<Speed sx={{ fontSize: 14 }} />}
                label="Performans analizi"
                size="small"
                variant="outlined"
                sx={{ height: 24, fontSize: '0.6rem' }}
              />
              <Chip
                icon={<Download sx={{ fontSize: 14 }} />}
                label="Excel raporu"
                size="small"
                variant="outlined"
                sx={{ height: 24, fontSize: '0.6rem' }}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Alert'ler */}
      {error && (
        <Alert
          severity={error.includes('Excel') ? 'warning' : 'error'}
          sx={{ mb: 2, fontSize: '0.8rem' }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2, fontSize: '0.8rem' }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* KPI KARTLARI */}
      <Grid container spacing={1.5} sx={{ mb: 2 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Inventory sx={{ fontSize: 18, color: '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: '#1f4e79' }}>
              {results.length || materialCount || 0}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Malzeme</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: results.length > 0 ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AttachMoney sx={{ fontSize: 18, color: results.length > 0 ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: results.length > 0 ? '#2e7d32' : '#1f4e79' }}>
              {results.length > 0 ? (results.reduce((acc, r) => acc + (r.total_cost || 0), 0) / results.length).toFixed(0) : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama Maliyet</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: results.length > 0 ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <TrendingUp sx={{ fontSize: 18, color: results.length > 0 ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: results.length > 0 ? '#2e7d32' : '#1f4e79' }}>
              {results.length > 0 ? (results.reduce((acc, r) => acc + (r.service_level || 0), 0) / results.length * 100).toFixed(1) + '%' : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama Servis</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: results.length > 0 ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Speed sx={{ fontSize: 18, color: results.length > 0 ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: results.length > 0 ? '#2e7d32' : '#1f4e79' }}>
              {results.length > 0 ? (() => {
                const counts: Record<string, number> = {};
                results.forEach((r) => {
                  counts[r.best_strategy] = (counts[r.best_strategy] || 0) + 1;
                });
                const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
                return strategyLabels[sorted[0]?.[0] || 'hybrid'] || '-';
              })() : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>En İyi Strateji</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* ANA GRID */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        {/* SOL SÜTUN - Veri Durumu */}
        <Grid size={{ xs: 12, md: 5 }}>
          {/* Veri Durumu Kartı */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {isCheckingData ? (
                  <CircularProgress size={18} />
                ) : hasUploadedData ? (
                  <CloudDone sx={{ fontSize: 20, color: '#2e7d32' }} />
                ) : (
                  <CloudOff sx={{ fontSize: 20, color: '#d32f2f' }} />
                )}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  Veri Durumu
                </Typography>
                <Chip
                  label={isCheckingData ? 'Kontrol ediliyor...' : hasUploadedData ? '✅ Yüklü' : '❌ Yüklenmemiş'}
                  size="small"
                  color={hasUploadedData ? 'success' : 'error'}
                  sx={{ height: 20, fontSize: '0.55rem' }}
                />
              </Box>

              {hasUploadedData && (
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5, mt: 0.5 }}>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                    <strong>{materialCount}</strong> Malzeme
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                    <strong>{maxAvailableWeeks || 0}</strong> Hafta Veri
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      fontSize: '0.65rem',
                      color: isDataValid ? '#2e7d32' : '#d32f2f',
                      gridColumn: 'span 2',
                      fontWeight: isDataValid ? 400 : 600,
                    }}
                  >
                    {isDataValid
                      ? `✅ ${maxAvailableWeeks} hafta veri ile ${testWindow} haftalık test yapılabilir.`
                      : `⚠️ ${maxAvailableWeeks} hafta veri yetersiz (Test için ${Math.max(8, testWindow + 4)} hafta gerekli)`}
                  </Typography>
                </Box>
              )}

              {!hasUploadedData && !isCheckingData && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                  Lütfen Dashboard'dan Excel yükleyin
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Validasyon Uyarısı */}
          {validationError && (
            <Alert
              severity={isDataValid ? 'info' : 'warning'}
              sx={{ mb: 2, fontSize: '0.8rem' }}
              icon={isDataValid ? <Info /> : <WarningIcon />}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>
                    {validationError}
                  </Typography>
                  {!isDataValid && maxAvailableWeeks > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      💡 Test penceresini {Math.max(8, maxAvailableWeeks - 4)} hafta veya daha düşük seçin,
                      veya daha uzun veri içeren bir Excel dosyası yükleyin.
                    </Typography>
                  )}
                </Box>
              </Box>
            </Alert>
          )}
        </Grid>

        {/* SAĞ SÜTUN - Parametreler ve Butonlar */}
        <Grid size={{ xs: 12, md: 7 }}>
          {/* Parametre Kartı */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <Speed sx={{ fontSize: 18, color: '#1f4e79' }} />
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
                  Test Penceresi: {testWindow} Hafta
                </Typography>
                {maxAvailableWeeks > 0 && (
                  <Chip
                    label={`📊 ${maxAvailableWeeks} hafta veri`}
                    size="small"
                    color={isDataValid ? 'success' : 'warning'}
                    sx={{ height: 18, fontSize: '0.5rem' }}
                  />
                )}
              </Box>

              <Slider
                value={testWindow}
                onChange={handleSliderChange}
                min={4}
                max={Math.min(26, maxAvailableWeeks || 26)}
                step={2}
                marks={[
                  { value: 4, label: '4' },
                  { value: 8, label: '8' },
                  { value: 13, label: '13' },
                  { value: 26, label: '26' },
                ]}
                valueLabelDisplay="auto"
                size="small"
                sx={{
                  color: isDataValid ? '#1f4e79' : '#d32f2f',
                  '& .MuiSlider-markLabel': { fontSize: '0.5rem', color: '#9e9e9e' },
                  '& .MuiSlider-thumb': { width: 16, height: 16, zIndex: 10 },
                  '& .MuiSlider-track': { height: 4 },
                  '& .MuiSlider-rail': { height: 4 },
                }}
              />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e' }}>
                  Hızlı
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>
                  Orta
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#2e7d32' }}>
                  Derinlemesine
                </Typography>
              </Box>

              {maxAvailableWeeks > 0 && (
                <Box
                  sx={{
                    mt: 1.5,
                    p: 1,
                    bgcolor: isDataValid ? '#e8f5e9' : '#fff3e0',
                    borderRadius: 1,
                    border: `1px solid ${isDataValid ? '#a5d6a7' : '#ffcc80'}`,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{ fontSize: '0.6rem', color: isDataValid ? '#2e7d32' : '#e65100' }}
                  >
                    {isDataValid
                      ? `✅ ${maxAvailableWeeks} hafta veri ile ${testWindow} haftalık test yapılabilir.`
                      : `⚠️ Test için ${Math.max(8, testWindow + 4)} hafta veri gerekli. Mevcut: ${maxAvailableWeeks} hafta. ` +
                        `Test penceresini ${Math.max(8, maxAvailableWeeks - 4)} hafta veya daha düşük seçin.`}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Butonlar */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Button
                  variant="contained"
                  size="medium"
                  startIcon={
                    backtestMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />
                  }
                  onClick={() => backtestMutation.mutate()}
                  disabled={backtestMutation.isPending || !hasUploadedData || isProcessing || !isDataValid}
                  sx={{
                    fontSize: '0.75rem',
                    textTransform: 'none',
                    bgcolor: '#1f4e79',
                    '&:hover': { bgcolor: '#1a3d5c' },
                    py: 0.75,
                    px: 2.5,
                    borderRadius: 2,
                    flex: 1,
                    minWidth: 120,
                    opacity: !isDataValid ? 0.6 : 1,
                  }}
                >
                  {backtestMutation.isPending
                    ? 'Test Ediliyor...'
                    : 'Testi Başlat'}
                </Button>

                <Button
                  variant="contained"
                  size="medium"
                  color="secondary"
                  startIcon={
                    asyncBacktestMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />
                  }
                  onClick={() => asyncBacktestMutation.mutate()}
                  disabled={asyncBacktestMutation.isPending || !hasUploadedData || isProcessing || !isDataValid}
                  sx={{
                    fontSize: '0.75rem',
                    textTransform: 'none',
                    py: 0.75,
                    px: 2.5,
                    borderRadius: 2,
                    flex: 1,
                    minWidth: 120,
                    opacity: !isDataValid ? 0.6 : 1,
                  }}
                >
                  {asyncBacktestMutation.isPending
                    ? 'Başlatılıyor...'
                    : 'Arka Planda Çalıştır'}
                </Button>

                <Button
                  variant="outlined"
                  size="medium"
                  startIcon={<History sx={{ fontSize: 18 }} />}
                  onClick={fetchHistory}
                  disabled={loading}
                  sx={{
                    fontSize: '0.75rem',
                    textTransform: 'none',
                    py: 0.75,
                    px: 2.5,
                    borderRadius: 2,
                    borderColor: '#d0d0d0',
                    flex: 0.5,
                    minWidth: 80,
                  }}
                >
                  {loading ? 'Yükleniyor...' : 'Geçmiş'}
                </Button>
              </Stack>
            </CardContent>
          </Card>

          {/* ✅ Kredi Bakiyesi ve Maliyet Önizleme */}
          <Card sx={{ mb: 2, bgcolor: 'grey.50', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Grid container spacing={1.5} sx={{ alignItems: 'center' }}>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AccountBalanceWallet sx={{ fontSize: 20, color: '#f57c00' }} />
                    <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                      Kredi Bakiyesi: <strong>{user?.token_balance || 0}</strong>
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid size={{ xs: 12, sm: 4 }}>
                  {pricingLoading ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={16} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        Maliyet hesaplanıyor...
                      </Typography>
                    </Box>
                  ) : pricingPreview && pricingPreview.estimated_credit_cost > 0 ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AttachMoney sx={{ fontSize: 18, color: pricingPreview.is_sufficient ? '#2e7d32' : '#d32f2f' }} />
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        Tahmini Maliyet: <strong style={{ color: pricingPreview.is_sufficient ? '#2e7d32' : '#d32f2f' }}>
                          {pricingPreview.estimated_credit_cost} Kredi
                        </strong>
                      </Typography>
                      {!pricingPreview.is_sufficient && (
                        <Chip 
                          label="Yetersiz Bakiye!" 
                          size="small" 
                          color="error" 
                          sx={{ height: 20, fontSize: '0.55rem' }}
                        />
                      )}
                      {pricingPreview.is_sufficient && pricingPreview.processing_score > 0 && (
                        <Chip 
                          label={`Score: ${pricingPreview.processing_score}`} 
                          size="small" 
                          variant="outlined"
                          sx={{ height: 18, fontSize: '0.5rem' }}
                        />
                      )}
                      {pricingPreview.calculation_method === 'dataset_complexity' && (
                        <Chip 
                          label="🧩 Complex" 
                          size="small" 
                          variant="outlined"
                          sx={{ height: 16, fontSize: '0.45rem', color: '#9c27b0' }}
                        />
                      )}
                    </Box>
                  ) : (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {activeDatasetId ? 'Analiz sonrası maliyet görünecek' : 'Dataset oluşturun'}
                    </Typography>
                  )}
                </Grid>

                <Grid size={{ xs: 12, sm: 4 }}>
                  {pricingPreview && pricingPreview.calculation_method === 'dataset_complexity' && pricingPreview.breakdown ? (
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block' }}>
                        🧩 Dataset Complexity: {pricingPreview.breakdown.total || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.5rem', display: 'block' }}>
                        📊 {pricingPreview.product_count} ürün × {pricingPreview.period_count} dönem = {pricingPreview.data_points} 
                        {pricingPreview.breakdown.relation && ` + ${pricingPreview.breakdown.relation.score} ilişki`}
                        {pricingPreview.breakdown.lookup && ` + ${pricingPreview.breakdown.lookup.score} referans`}
                      </Typography>
                    </Box>
                  ) : pricingPreview && pricingPreview.data_points > 0 ? (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block', textAlign: 'right' }}>
                      📊 {pricingPreview.product_count} ürün × {pricingPreview.period_count} dönem = {pricingPreview.data_points} veri noktası
                    </Typography>
                  ) : null}
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Bilgi Kartı */}
          <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#f0f7ff', border: '1px solid #d0e0ff' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Info sx={{ fontSize: 18, color: '#1f4e79' }} />
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
                  📌 Backtest için Minimum Veri Gereksinimi
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#374151', mt: 0.5 }}>
                Backtest analizi için en az <strong>8 haftalık</strong> geçmiş veri gereklidir.
                Test penceresi + 4 hafta buffer ile çalışır. Örneğin 8 haftalık test için en az 12 hafta veri gerekir.
                {maxAvailableWeeks > 0 && (
                  <span>
                    {' '}Mevcut veriniz: <strong>{maxAvailableWeeks} hafta</strong>.
                    {isDataValid ? ' ✅ Yeterli.' : ' ⚠️ Yetersiz.'}
                  </span>
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 8 STRATEJİ - TANITIM KARTLARI */}
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#fafcff', border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          {/* Bilgi Kutusu */}
          <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#f0f7ff', border: '1px solid #d0e0ff' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Lightbulb sx={{ fontSize: 20, color: '#1f4e79', mt: 0.25 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                    Stokonomi Akıllı Seçim
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#374151', mt: 0.25 }}>
                    Stokonomi, her malzeme için bu stratejilerin <strong>tamamını</strong> değerlendirir 
                    ve geçmiş veriye en uygun stratejiyi <strong>otomatik olarak önerir</strong>.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Strateji Kartları */}
          <Grid container spacing={1.5}>
            {strategyDetails.map((strategy) => (
              <Grid size={{ xs: 6, sm: 4, md: 3 }} key={strategy.key}>
                <Tooltip
                  title={
                    <Box sx={{ p: 1.5, maxWidth: 280 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem', mb: 0.5 }}>
                        {strategy.tooltip.title}
                      </Typography>
                      <Divider sx={{ mb: 1 }} />
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.75 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>📌</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>
                            Ne zaman kullanılır?
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                            {strategy.tooltip.when}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.75 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>🏭</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>
                            Örnek ürünler
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                            {strategy.tooltip.example}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>✅</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>
                            Avantajı
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                            {strategy.tooltip.advantage}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  }
                  arrow
                  placement="top"
                  enterDelay={200}
                  leaveDelay={100}
                  slotProps={{
                    tooltip: {
                      sx: {
                        bgcolor: 'white',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                        border: '1px solid #e8f0fe',
                        borderRadius: 2,
                        p: 0,
                        maxWidth: 300,
                        zIndex: 1300,
                      },
                    },
                    popper: {
                      sx: { zIndex: 1300 },
                    },
                  }}
                >
                  <Paper
                    sx={{
                      p: 1,
                      textAlign: 'center',
                      bgcolor: strategy.isRecommended ? alpha('#1f4e79', 0.06) : 'white',
                      border: strategy.isRecommended ? '2px solid #1f4e79' : '1px solid #e8f0fe',
                      borderRadius: 2,
                      cursor: 'default',
                      transition: 'all 0.2s',
                      position: 'relative',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                        borderColor: strategy.isRecommended ? '#1f4e79' : '#b0b0b0',
                      },
                    }}
                  >
                    {strategy.isRecommended && (
                      <Chip
                        label="⭐ Önerilen"
                        size="small"
                        color="primary"
                        sx={{
                          position: 'absolute',
                          top: -8,
                          right: -8,
                          height: 18,
                          fontSize: '0.5rem',
                          fontWeight: 600,
                          boxShadow: '0 2px 8px rgba(31,78,121,0.2)',
                        }}
                      />
                    )}
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      {strategy.icon}
                      <Typography variant="caption" sx={{ fontWeight: strategy.isRecommended ? 700 : 500, fontSize: '0.65rem' }}>
                        {strategy.label}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ fontSize: '0.55rem', color: strategy.isRecommended ? '#1f4e79' : '#6b7280', display: 'block', mt: 0.25, fontWeight: strategy.isRecommended ? 500 : 400 }}>
                      {strategy.short}
                    </Typography>
                    {strategy.isRecommended && (
                      <Box
                        sx={{
                          mt: 0.5,
                          height: 2,
                          bgcolor: '#1f4e79',
                          borderRadius: 1,
                          width: '60%',
                          mx: 'auto',
                        }}
                      />
                    )}
                  </Paper>
                </Tooltip>
              </Grid>
            ))}
          </Grid>

          <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center' }}>
            <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', textAlign: 'center' }}>
              💡 Backtest sırasında sekiz stratejinin tamamı test edilir. 
              En düşük hata oranına sahip strateji otomatik seçilir.
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* İlerleme Durumu */}
      {isProcessing && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, justifyContent: 'center' }}>
            <CircularProgress variant="determinate" value={progress} size={40} />
            <Typography variant="body2" color="text.secondary">
              {progressLabel}
            </Typography>
            {activeAsyncTask && (
              <Typography variant="caption" color="text.secondary">
                (ID: {activeAsyncTask.slice(0, 8)})
              </Typography>
            )}
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ mt: 1, maxWidth: 400, mx: 'auto', height: 6, borderRadius: 3 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            8 strateji test ediliyor...
          </Typography>
        </Box>
      )}

      {/* Sonuçlar Tablosu */}
      {results.length > 0 && (
        <Card>
          <CardContent sx={{ py: 1.5, px: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                📊 Sonuçlar ({results.length} malzeme)
              </Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download sx={{ fontSize: 16 }} />}
                onClick={handleExport}
                sx={{ fontSize: '0.65rem', textTransform: 'none' }}
              >
                Excel
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f0f7ff' }}>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      Malzeme
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      Grup
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      En İyi Strateji
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">
                      Servis %
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">
                      Tail Risk
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">
                      Maliyet
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      Tavsiye
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#f8faff' } }}>
                      <TableCell sx={{ fontSize: '0.7rem' }}>{result.material_code}</TableCell>
                      <TableCell sx={{ fontSize: '0.7rem' }}>{result.group}</TableCell>
                      <TableCell>
                        <Chip
                          label={strategyLabels[result.best_strategy] || result.best_strategy}
                          size="small"
                          sx={{
                            bgcolor: strategyColors[result.best_strategy] || '#1976d2',
                            color: 'white',
                            fontWeight: 'bold',
                            height: 20,
                            fontSize: '0.55rem',
                          }}
                        />
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                        {(result.service_level * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.7rem' }}>
                        <Chip
                          label={result.tail_risk?.toFixed(2) || '-'}
                          size="small"
                          color={getRiskColor(result.tail_risk || 0)}
                          sx={{ minWidth: 40, height: 20, fontSize: '0.5rem' }}
                        />
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.7rem' }}>
                        {result.total_cost?.toFixed(0) || '-'}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem' }}>
                        <Tooltip title={result.recommendation || ''} arrow>
                          <Typography
                            variant="caption"
                            sx={{
                              cursor: 'pointer',
                              display: 'block',
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              fontSize: '0.65rem',
                            }}
                          >
                            {result.recommendation?.split(' | ')[0] || '-'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[25, 50, 100, 200]}
                component="div"
                count={results.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                labelRowsPerPage="Satır:"
                sx={{
                  '& .MuiTablePagination-select': { fontSize: '0.7rem' },
                  '& .MuiTablePagination-displayedRows': { fontSize: '0.7rem' },
                }}
              />
            </TableContainer>

            {/* Özet */}
            {results.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={1.5}>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                        Ortalama Servis
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(
                          results.reduce((acc, r) => acc + (r.service_level || 0), 0) / results.length *
                          100
                        ).toFixed(1)}
                        %
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                        Ortalama Tail Risk
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(
                          results.reduce((acc, r) => acc + (r.tail_risk || 0), 0) / results.length
                        ).toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                        Ortalama Maliyet
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(
                          results.reduce((acc, r) => acc + (r.total_cost || 0), 0) / results.length
                        ).toFixed(0)}{' '}
                        TL
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'primary.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                        En Çok Strateji
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(() => {
                          const counts: Record<string, number> = {};
                          results.forEach((r) => {
                            counts[r.best_strategy] = (counts[r.best_strategy] || 0) + 1;
                          });
                          const entries = Object.entries(counts);
                          if (entries.length === 0) return '-';
                          const sorted = entries.sort((a, b) => b[1] - a[1]);
                          return strategyLabels[sorted[0][0]] || sorted[0][0];
                        })()}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Boş Durum */}
      {!isProcessing && results.length === 0 && !error && hasUploadedData && !isCheckingData && (
        <Card sx={{ borderRadius: 2, border: '1px dashed #e0e0e0', bgcolor: '#fafcff' }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <School sx={{ fontSize: 40, color: '#b0b0b0', mb: 1 }} />
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
              Henüz backtest yapılmadı
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              "Testi Başlat" veya "Arka Planda Çalıştır" butonuna tıklayın
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Geçmiş Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.95rem' }}>
              📜 Geçmiş Analizler
            </Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)} size="small">
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          {loading ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress size={32} />
            </Box>
          ) : historyData.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4, fontSize: '0.8rem' }}>
              Henüz geçmiş analiz bulunmuyor.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f8faff' }}>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      📅 Tarih
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      📄 Rapor Adı
                    </TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      📦 Malzeme Sayısı
                    </TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      ⏳ Durum
                    </TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>
                      🔍 İşlem
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {historyData.map((item) => {
                    const itemDate = new Date(item.created_at);
                    const dateStr = itemDate.toLocaleDateString('tr-TR');
                    const timeStr = itemDate.toLocaleTimeString('tr-TR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    });
                    const status = item.data?.status || 'completed';
                    const statusConfig = {
                      completed: { label: '✅ Tamamlandı', color: 'success' },
                      processing: { label: '🔄 İşleniyor', color: 'warning' },
                      pending: { label: '⏳ Bekliyor', color: 'info' },
                      failed: { label: '❌ Başarısız', color: 'error' },
                    };
                    const statusInfo =
                      statusConfig[status as keyof typeof statusConfig] || statusConfig.completed;

                    return (
                      <TableRow key={item.id} hover>
                        <TableCell sx={{ fontSize: '0.7rem' }}>
                          <Box>
                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                              {dateStr}
                            </Typography>
                            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#9e9e9e' }}>
                              {timeStr}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                          {item.data?.report_name || 'Backtest Analizi'}
                        </TableCell>
                        <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600 }}>
                          {item.data?.total || 0}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={statusInfo.label}
                            size="small"
                            color={statusInfo.color as any}
                            sx={{ height: 20, fontSize: '0.55rem' }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleViewHistory(item)}
                            startIcon={<Visibility sx={{ fontSize: 14 }} />}
                            sx={{ fontSize: '0.6rem', textTransform: 'none' }}
                          >
                            Görüntüle
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1.5 }}>
          <Button onClick={() => setHistoryDialogOpen(false)} size="small" sx={{ fontSize: '0.7rem', textTransform: 'none' }}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}