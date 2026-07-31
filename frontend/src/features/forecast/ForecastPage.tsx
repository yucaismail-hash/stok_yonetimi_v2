// frontend/src/pages/ForecastPage.tsx - TAM VE GÜNCEL
// Yeni bileşenler: DecisionReasoning, TechnicalAnalysisDetail, LearningScoreBadge

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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Slider,
  LinearProgress,
  Snackbar,
  Stepper,
  Step,
  StepLabel,
  Avatar,
  alpha,
  RadioGroup,
  FormControlLabel,
  Radio,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ShowChart,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  Analytics,
  Timeline,
  AutoAwesome,
  CloudDone,
  CloudOff,
  Inventory,
  AttachMoney,
  Lightbulb,
  Star,
  TrendingUp as TrendingUpIcon,
  Speed,
  CalendarToday,
  Assessment,
  Psychology,
  AccountBalanceWallet,
  ExpandMore,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import { fetchAndLoadResult, checkAndLoadAnalysis } from '../../utils/loadAnalysisResult';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
} from 'recharts';
import { usePricingPreview, updateActiveDatasetId } from '../../hooks/usePricing';

// ✅ YENİ BİLEŞENLER
import DecisionReasoning from '../../components/Results/DecisionReasoning';
import TechnicalAnalysisDetail from '../../components/Results/TechnicalAnalysisDetail';
import LearningScoreBadge from '../../components/Dashboard/LearningScoreBadge';

// ✅ AI Neden Bu Kararı Verdi? - Bileşeni
const AIReasoningSection = ({ result }: { result: ForecastResult }) => {
  const aiDecision = (result as any).ai_decision;
  
  if (!aiDecision) {
    return null;
  }

  const reasoning = {
    recommended_ss: 0, // Forecast için SS yok
    current_ss: 0,
    reasons: aiDecision.reasons || [
      (result.model_rmse || 0) > 30 ? 'RMSE yüksek' : '',
      result.outlier_info?.has_outliers ? 'Aykırı değerler var' : '',
      result.trend_direction === 'Artış' ? 'Yükselen trend' : '',
      result.trend_direction === 'Azalış' ? 'Azalan trend' : '',
      result.pattern === 'ARALIKLI_YUKSEK' ? 'Aralıklı talep' : '',
    ].filter(Boolean),
    conclusion: aiDecision.decision === 'change_forecast_model' 
      ? `En iyi model: ${result.best_model_label} önerildi.` 
      : aiDecision.decision === 'maintain_current'
      ? 'Mevcut model yeterli.'
      : 'Detaylı analiz önerilir.',
    confidence: aiDecision.confidence || 0.5,
    factors: {
      cv: result.cv || 0,
      lead_time: 0,
      intermittent: result.pattern === 'ARALIKLI_YUKSEK' || result.pattern === 'ARALIKLI_DUSUK',
      seasonal: result.model_params?.seasonal_periods ? true : false,
      risk_score: result.model_rmse ? Math.min(1, result.model_rmse / 100) : 0.5,
      pattern: result.pattern_label || 'DEGISKEN',
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

// ✅ Teknik Analiz Bölümü - Accordion içinde
const TechnicalAnalysisSection = ({ result }: { result: ForecastResult }) => {
  const [expanded, setExpanded] = useState(false);

  const technicalData = {
    material_code: result.material_code,
    cv: result.cv || 0,
    pattern: result.pattern || 'DEGISKEN',
    pattern_label: result.pattern_label || 'Değişken',
    pattern_color: result.pattern_color || 'default',
    abc: 'C',
    abc_label: 'Düşük Maliyetli',
    xyz: result.cv && result.cv < 0.3 ? 'X' : result.cv && result.cv < 0.6 ? 'Y' : 'Z',
    xyz_label: result.cv && result.cv < 0.3 ? 'Düzenli Talep' : result.cv && result.cv < 0.6 ? 'Değişken Talep' : 'Düzensiz Talep',
    forecast_model: result.selected_model || 'auto',
    forecast_model_label: result.best_model_label || 'Otomatik',
    seasonality: result.model_params?.seasonal_periods ? true : false,
    seasonality_label: result.model_params?.seasonal_periods ? 'Güçlü' : 'Yok',
    seasonality_strength: result.model_params?.seasonal_periods ? 0.7 : 0,
    trend_direction: result.trend_direction || 'Yok',
    trend_percent: result.trend_percent || 0,
    lead_time_days: 14,
    zero_ratio: result.zero_ratio || 0,
    risk_score: result.model_rmse ? Math.min(1, result.model_rmse / 100) : 0.5,
    risk_level: (result.model_rmse || 0) < 20 ? 'Düşük' : (result.model_rmse || 0) < 40 ? 'Orta' : 'Yüksek',
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

interface ForecastResult {
  material_code: string;
  group: string;
  horizon: number;
  selected_model: string;
  best_model_label: string;
  model_description: string;
  selection_reason: string;
  forecast: number[];
  lower_80: number[];
  upper_80: number[];
  lower_95: number[];
  upper_95: number[];
  trend_direction: string;
  trend_percent: number;
  model_rmse: number | null;
  model_comparison: Record<string, any>;
  model_params: Record<string, any>;
  outlier_info: { has_outliers: boolean; outlier_count: number; outliers: any[] };
  historical_data?: number[];
  pattern?: string;
  pattern_label?: string;
  pattern_color?: string;
  cv?: number;
  zero_ratio?: number;
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

// ✅ Model Detayları
interface ModelDetail {
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

const modelDetails: ModelDetail[] = [
  {
    key: 'holt_winters',
    label: 'Holt-Winters',
    icon: <Timeline fontSize="small" />,
    short: 'Mevsimsel talep',
    tooltip: {
      title: 'Holt-Winters Yöntemi',
      when: 'Mevsimsel desenlere sahip ürünler (52+ hafta veri).',
      example: 'Mevsimlik ürünler, tatil dönemi satışları, yılbaşı ürünleri.',
      advantage: 'Mevsimsel dalgalanmaları yakalar, trend ve mevsimselliği birlikte modeller.',
    },
  },
  {
    key: 'arima',
    label: 'ARIMA',
    icon: <Analytics fontSize="small" />,
    short: 'Otoregresif',
    tooltip: {
      title: 'ARIMA Yöntemi',
      when: 'Trend ve otokorelasyon gösteren ürünler (26+ hafta veri).',
      example: 'Büyüyen ürünler, düzenli satış trendi olan ürünler.',
      advantage: 'Geçmiş değerlerle geleceği tahmin eder, istatistiksel olarak güçlüdür.',
    },
  },
  {
    key: 'simple',
    label: 'Basit MA',
    icon: <ShowChart fontSize="small" />,
    short: 'Hızlı tahmin',
    tooltip: {
      title: 'Basit Hareketli Ortalama',
      when: 'Az veri veya hızlı tahmin ihtiyacı (4+ hafta veri).',
      example: 'Yeni ürünler, az geçmişi olan ürünler, hızlı analiz.',
      advantage: 'Basit ve hızlı, az veri ile çalışabilir.',
    },
  },
  {
    key: 'auto',
    label: 'Otomatik',
    icon: <AutoAwesome fontSize="small" />,
    short: '⭐ Varsayılan Öneri',
    tooltip: {
      title: 'Otomatik Model Seçimi',
      when: 'Tüm ürünler için uygun, en çok önerilen yöntem.',
      example: 'Tüm ürün grupları için ideal başlangıç noktası.',
      advantage: '4 modeli de değerlendirir, talep yapısına en uygun olanı seçer.',
    },
    isRecommended: true,
  },
];

// ✅ Analiz Aşamaları Bileşeni
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

export default function ForecastPage() {
  const { user, fetchUser } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [results, setResults] = useState<ForecastResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [horizon, setHorizon] = useState(4);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState<ForecastResult | null>(null);
  const [materialCount, setMaterialCount] = useState(0);
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null);
  const [aiComment, setAiComment] = useState<AIComment | null>(null);
  const [weekCount, setWeekCount] = useState(0);
  const [lastUploadDate, setLastUploadDate] = useState<string | null>(null);

  const [selectedReasoning, setSelectedReasoning] = useState<ForecastResult | null>(null);

  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);
  
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  
  const intervalIdRef = useRef<number | null>(null);
  const queryClient = useQueryClient();

  // ✅ Normal Analiz Aşamaları State'leri
  const [steps, setSteps] = useState<AnalysisStep[]>([
    { label: 'Veri okunuyor...', description: 'Excel dosyası kontrol ediliyor', status: 'pending' },
    { label: 'Talep geçmişi hazırlanıyor...', description: 'Malzeme verileri işleniyor', status: 'pending' },
    { label: 'Pattern analizi yapılıyor...', description: 'Talep desenleri belirleniyor', status: 'pending' },
    { label: 'Tahmin modelleri çalıştırılıyor...', description: '4 model ile tahmin yapılıyor', status: 'pending' },
    { label: 'Sonuçlar doğrulanıyor...', description: 'Veriler kontrol ediliyor', status: 'pending' },
    { label: 'Rapor oluşturuluyor...', description: 'Excel dosyası hazırlanıyor', status: 'pending' },
  ]);
  const [activeStep, setActiveStep] = useState(-1);
  const [isAnalysisComplete, setIsAnalysisComplete] = useState(false);

  // ✅ Async Analiz Aşamaları State'leri
  const [asyncSteps, setAsyncSteps] = useState<AnalysisStep[]>([
    { label: 'Analiz Ediliyor...', description: 'Veriler işleniyor', status: 'pending' },
    { label: 'Görev Oluşturuluyor...', description: 'Arka plan işlemi başlatılıyor', status: 'pending' },
    { label: 'Görevlere Eklendi ✓', description: 'İlerlemeyi ASYNC Görevler sayfasından takip edin', status: 'pending' },
  ]);
  const [asyncActiveStep, setAsyncActiveStep] = useState(-1);
  const [isAsyncComplete, setIsAsyncComplete] = useState(false);

  // 🆕 Dataset ID için state
  const [activeDatasetId, setActiveDatasetId] = useState<number | null>(() => {
    const saved = localStorage.getItem('activeDatasetId');
    return saved ? parseInt(saved) : null;
  });

  // 🆕 Pricing Preview Hook
  const { data: pricingPreview, isLoading: pricingLoading } = usePricingPreview(
    '/api/forecast/batch',
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

  useEffect(() => {
    checkUploadedData();
    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, []);

  const checkUploadedData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/upload/status');
      const hasData = res.data.has_data === true;
      setHasUploadedData(hasData);
      setMaterialCount(res.data.materials_count || 0);
      setWeekCount(res.data.week_count || 0);
      setLastUploadDate(res.data.last_upload_date || null);
      if (!hasData) {
        setError('Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard\'dan dosya yükleyin.');
      }
    } catch (error) {
      console.error('❌ Veri kontrolü hatası:', error);
      setHasUploadedData(false);
      setError('Veri kontrolü sırasında hata oluştu.');
    } finally {
      setIsCheckingData(false);
    }
  };

  const handleFetchAndLoad = (id: number) => {
    fetchAndLoadResult(id, setResults, setPage, setSuccess, setError, setLoading);
  };

  useEffect(() => {
    checkAndLoadAnalysis('forecast', handleFetchAndLoad);
  }, []);

  const updateStep = (index: number, status: 'pending' | 'active' | 'completed' | 'error', description?: string) => {
    setSteps(prev => prev.map((step, i) => {
      if (i === index) {
        return {
          ...step,
          status,
          description: description || step.description,
          timestamp: status === 'completed' || status === 'active' ? new Date().toLocaleTimeString() : undefined,
        };
      }
      return step;
    }));
    setActiveStep(index);
  };

  const updateAsyncStep = (index: number, status: 'pending' | 'active' | 'completed' | 'error', description?: string) => {
    setAsyncSteps(prev => prev.map((step, i) => {
      if (i === index) {
        return {
          ...step,
          status,
          description: description || step.description,
          timestamp: status === 'completed' || status === 'active' ? new Date().toLocaleTimeString() : undefined,
        };
      }
      return step;
    }));
    setAsyncActiveStep(index);
  };

  const resetSteps = () => {
    setSteps(prev => prev.map(step => ({
      ...step,
      status: 'pending',
      timestamp: undefined,
    })));
    setActiveStep(-1);
    setIsAnalysisComplete(false);
  };

  const resetAsyncSteps = () => {
    setAsyncSteps(prev => prev.map(step => ({
      ...step,
      status: 'pending',
      timestamp: undefined,
    })));
    setAsyncActiveStep(-1);
    setIsAsyncComplete(false);
  };

  const clearAllSteps = () => {
    resetSteps();
    resetAsyncSteps();
    setProgress(0);
    setProgressLabel('Hazır');
    setAnalysisSummary(null);
    setAiComment(null);
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const generateSummary = (resultsData: ForecastResult[]) => {
    if (!resultsData || resultsData.length === 0) return null;

    const modelCount: Record<string, number> = {};
    resultsData.forEach(r => {
      const model = r.selected_model || 'auto';
      modelCount[model] = (modelCount[model] || 0) + 1;
    });
    const sortedModels = Object.entries(modelCount).sort((a, b) => b[1] - a[1]);
    const mostUsed = sortedModels[0] || ['auto', 0];
    const mostUsedPercent = resultsData.length > 0 ? (mostUsed[1] / resultsData.length) * 100 : 0;

    let rmseSum = 0, rmseCount = 0;
    let trendUp = 0, trendDown = 0;
    let bestRMSE = Infinity, worstRMSE = -Infinity;
    let bestMaterial = '', worstMaterial = '';

    resultsData.forEach(r => {
      if (r.model_rmse) { 
        rmseSum += r.model_rmse; 
        rmseCount++;
        if (r.model_rmse < bestRMSE) { bestRMSE = r.model_rmse; bestMaterial = r.material_code; }
        if (r.model_rmse > worstRMSE) { worstRMSE = r.model_rmse; worstMaterial = r.material_code; }
      }
      if (r.trend_direction === 'Artış') trendUp++;
      else if (r.trend_direction === 'Azalış') trendDown++;
    });

    let seasonalityLevel = 'Düşük';
    if (resultsData.filter(r => r.selected_model === 'holt_winters').length > resultsData.length * 0.3) {
      seasonalityLevel = 'Yüksek';
    } else if (resultsData.filter(r => r.selected_model === 'holt_winters').length > resultsData.length * 0.15) {
      seasonalityLevel = 'Orta';
    }

    return {
      totalMaterials: resultsData.length,
      mostUsedModel: mostUsed[0],
      mostUsedModelPercent: mostUsedPercent,
      avgRMSE: rmseCount > 0 ? rmseSum / rmseCount : 0,
      trendUpCount: trendUp,
      trendDownCount: trendDown,
      modelDistribution: modelCount,
      bestMaterial: bestMaterial || '-',
      worstMaterial: worstMaterial || '-',
      bestRMSE: bestRMSE !== Infinity ? bestRMSE : 0,
      worstRMSE: worstRMSE !== -Infinity ? worstRMSE : 0,
      seasonalityLevel: seasonalityLevel,
    };
  };

  const generateAIComment = (summary: AnalysisSummary) => {
    if (!summary) return null;

    let trendText = '';
    const trendRatio = summary.trendUpCount / (summary.trendUpCount + summary.trendDownCount || 1);
    if (trendRatio > 0.6) {
      trendText = `Önümüzdeki dönemde talepte güçlü artış beklenmektedir. ${summary.trendUpCount} üründe yükseliş, ${summary.trendDownCount} üründe düşüş öngörülüyor.`;
    } else if (trendRatio > 0.4) {
      trendText = `Talep trendi dengeli seyretmektedir. ${summary.trendUpCount} üründe artış, ${summary.trendDownCount} üründe azalış bekleniyor.`;
    } else {
      trendText = `Önümüzdeki dönemde talepte düşüş eğilimi görülmektedir. ${summary.trendDownCount} üründe azalış, ${summary.trendUpCount} üründe artış öngörülüyor.`;
    }

    let seasonalityText = '';
    if (summary.seasonalityLevel === 'Yüksek') {
      seasonalityText = 'Mevsimsel etkiler belirgin seviyededir. Holt-Winters modeli sık tercih edilmiştir.';
    } else if (summary.seasonalityLevel === 'Orta') {
      seasonalityText = 'Orta düzeyde mevsimsel etkiler tespit edilmiştir.';
    } else {
      seasonalityText = 'Mevsimsel etkiler düşük seviyededir. Basit modeller yeterli olabilir.';
    }

    let confidenceText = '';
    const avgRMSE = summary.avgRMSE;
    if (avgRMSE < 20) {
      confidenceText = 'Tahmin güvenilirliği yüksektir. Stok planlaması için güvenle kullanılabilir.';
    } else if (avgRMSE < 30) {
      confidenceText = 'Tahmin güvenilirliği iyi seviyededir. Düzenli takip önerilir.';
    } else {
      confidenceText = 'Tahmin güvenilirliği orta seviyededir. Veri kalitesinin iyileştirilmesi önerilir.';
    }

    return {
      summary: `${summary.totalMaterials} ürün analiz edildi. En çok tercih edilen model "${modelLabels[summary.mostUsedModel] || summary.mostUsedModel}" (%${summary.mostUsedModelPercent.toFixed(0)}).`,
      trend: trendText,
      seasonality: seasonalityText,
      confidence: confidenceText,
      recommendation: `En iyi tahmin: ${summary.bestMaterial} (RMSE: ${summary.bestRMSE.toFixed(2)}), En yüksek hata: ${summary.worstMaterial} (RMSE: ${summary.worstRMSE.toFixed(2)}).`,
    };
  };

  const startAnalysis = async () => {
    clearAllSteps();
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    
    try {
      updateStep(0, 'active', 'Excel dosyası kontrol ediliyor...');
      await sleep(600);
      updateStep(0, 'completed', 'Veri başarıyla okundu');
      setProgress(15);
      
      updateStep(1, 'active', 'Malzeme verileri işleniyor...');
      await sleep(800);
      updateStep(1, 'completed', 'Malzeme verileri hazırlandı');
      setProgress(30);
      
      updateStep(2, 'active', 'Pattern analizi yapılıyor...');
      await sleep(1000);
      updateStep(2, 'completed', 'Pattern analizi tamamlandı');
      setProgress(50);
      
      updateStep(3, 'active', '4 model ile tahmin yapılıyor...');
      const response = await forecastMutation.mutateAsync();
      updateStep(3, 'completed', `${response.total || response.results?.length || 0} malzeme tahmin edildi`);
      setProgress(75);
      
      if (response.results) {
        const summary = generateSummary(response.results);
        setAnalysisSummary(summary);
        if (summary) {
          const comment = generateAIComment(summary);
          setAiComment(comment);
        }
      }
      
      updateStep(4, 'active', 'Veriler kontrol ediliyor...');
      await sleep(500);
      updateStep(4, 'completed', 'Tüm sonuçlar doğrulandı');
      setProgress(90);
      
      updateStep(5, 'active', 'Excel dosyası hazırlanıyor...');
      await sleep(600);
      updateStep(5, 'completed', 'Rapor hazır');
      
      setIsAnalysisComplete(true);
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      
    } catch (err: any) {
      console.error('❌ Analiz hatası:', err);
      const errorIndex = steps.findIndex(s => s.status === 'active');
      if (errorIndex !== -1) {
        updateStep(errorIndex, 'error', err.response?.data?.detail || 'Hata oluştu!');
      } else {
        setSteps(prev => prev.map((step, i) => {
          if (i === 0) {
            return { ...step, status: 'error', description: err.message || 'Hata oluştu!' };
          }
          return step;
        }));
        setActiveStep(0);
      }
      setError(err.response?.data?.detail || err.message || 'Analiz sırasında hata oluştu');
    } finally {
      setIsProcessing(false);
    }
  };

  const startAsyncAnalysis = async () => {
    clearAllSteps();
    setIsProcessing(true);
    setError(null);
    
    try {
      updateAsyncStep(0, 'active', 'Veriler işleniyor...');
      await sleep(1000);
      updateAsyncStep(0, 'completed', 'Analiz başlatıldı');
      
      updateAsyncStep(1, 'active', 'Arka plan işlemi başlatılıyor...');
      
      const response = await asyncForecastMutation.mutateAsync();
      
      updateAsyncStep(1, 'completed', `İşlem ID: #${response.task_id.slice(0,8)}`);
      
      updateAsyncStep(2, 'active', 'Görevlere ekleniyor...');
      await sleep(600);
      updateAsyncStep(2, 'completed', '✅ Görevlere Eklendi');
      
      setIsAsyncComplete(true);
      
    } catch (err: any) {
      console.error('❌ Async analiz hatası:', err);
      const errorIndex = asyncSteps.findIndex(s => s.status === 'active');
      if (errorIndex !== -1) {
        updateAsyncStep(errorIndex, 'error', err.response?.data?.detail || 'Hata oluştu!');
      } else {
        setAsyncSteps(prev => prev.map((step, i) => {
          if (i === 0) {
            return { ...step, status: 'error', description: err.message || 'Hata oluştu!' };
          }
          return step;
        }));
        setAsyncActiveStep(0);
      }
      setError(err.response?.data?.detail || err.message || 'Async analiz başlatılamadı');
    } finally {
      setIsProcessing(false);
    }
  };

  // 📌 SENKRON Forecast
  const forecastMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/forecast/batch', {
        horizon: horizon,
        model_type: selectedModel,
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
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
        await fetchUser();
        
        if (data.credit_cost !== undefined) {
          setSnackbar({
            open: true,
            message: `💰 ${data.credit_cost} kredi harcandı. Kalan: ${data.balance_after} kredi. Processing Score: ${data.processing_score || '-'}`,
            severity: 'info',
          });
        }
      } else {
        setError(data.error || 'Analiz başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Forecast hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Forecast
  const asyncForecastMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/forecast/batch/async', {
        horizon: horizon,
        model_type: selectedModel,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setActiveAsyncTask(data.task_id);
      setSnackbar({
        open: true,
        message: `✅ Rapor talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0,8)}\n💰 Kredi: ${data.credit_cost || 0}, Kalan: ${data.balance_after || 0}`,
        severity: 'success',
      });
      setProgress(10);
      setProgressLabel('İşlem kuyruğa alındı.');
      
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      
      intervalIdRef.current = setInterval(() => {
        checkAsyncProgress(data.task_id);
      }, 3000);
      
      setTimeout(() => {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
          if (isProcessing) {
            setIsProcessing(false);
            setActiveAsyncTask(null);
            setError('Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.');
          }
        }
      }, 300000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    },
  });

  const checkAsyncProgress = async (taskId: string) => {
    if (!taskId) return;
    try {
      const res = await api.get(`/api/forecast/async/status/${taskId}`);
      const status = res.data;
      setProgress(status.progress || 50);
      setProgressLabel(status.message || 'İşleniyor...');
      
      if (status.status === 'completed') {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(100);
        setProgressLabel('Tamamlandı!');
        
        try {
          const resultsRes = await api.get(`/api/forecast/async/result/${taskId}`);
          if (resultsRes.data.success) {
            setResults(resultsRes.data.results || []);
            setPage(0);
            const count = resultsRes.data.total || resultsRes.data.results?.length || 0;
            setSuccess(`${count} malzeme başarıyla analiz edildi.`);
            setTimeout(() => setSuccess(null), 5000);
            await fetchUser();
          }
        } catch (err) {
          console.error('❌ Sonuç getirme hatası:', err);
          setError('Sonuçlar alınamadı');
        }
        return;
      }
      
      if (status.status === 'failed' || status.status === 'error') {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(0);
        setProgressLabel('Hata!');
        setError(status.message || 'Async analiz başarısız oldu');
        return;
      }
    } catch (error) {
      console.error('Async durum kontrol hatası:', error);
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      setIsProcessing(false);
      setActiveAsyncTask(null);
      setError('Async durum kontrolü başarısız');
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { 
          result_type: 'forecast_batch', 
          limit: 10000 
        }
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        const batchResults = rawResults.filter((item: any) => item.is_batch === true);
        
        const historyItems = batchResults.map((item: any) => {
          const data = item.data || {};
          const totalMaterials = item.total_materials || data.total || 0;
          const model = data?.selected_model || data?.model_type || 'Otomatik';
          const horizonVal = data?.horizon || 4;
          
          const modelLabelsLocal: Record<string, string> = {
            'holt_winters': 'Holt-Winters',
            'arima': 'ARIMA',
            'simple': 'Basit MA',
            'auto': 'Otomatik',
          };
          const modelLabel = modelLabelsLocal[model] || model;
          const reportName = `Talep Tahmini (${modelLabel}) - ${horizonVal} Hafta (${totalMaterials} Malzeme)`;
          
          return {
            id: item.id,
            created_at: item.created_at,
            data: {
              total: totalMaterials,
              results: data.results || [],
              report_name: reportName,
              status: item.status || 'completed',
              model: model,
              horizon: horizonVal,
            }
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
      const response = await api.post('/api/export/forecast-results', {
        results: results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_${new Date().toISOString().slice(0, 10)}.xlsx`);
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

  const handleChangePage = (event: unknown, newPage: number) => setPage(newPage);
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const paginatedResults = results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const modelColors: Record<string, string> = {
    holt_winters: '#9c27b0',
    arima: '#1976d2',
    simple: '#2e7d32',
    auto: '#ed6c02',
  };

  const modelLabels: Record<string, string> = {
    holt_winters: 'Holt-Winters',
    arima: 'ARIMA',
    simple: 'Basit MA',
    auto: 'Otomatik',
  };

  const getPatternColor = (color: string) => {
    switch(color) {
      case 'success': return 'success';
      case 'info': return 'info';
      case 'warning': return 'warning';
      case 'error': return 'error';
      case 'primary': return 'primary';
      case 'secondary': return 'secondary';
      default: return 'default';
    }
  };

  const getMapeStatus = (mape: number) => {
    if (mape < 30) return { color: '#2e7d32', label: '✅ İyi', bgColor: '#e8f5e9', borderColor: '#a5d6a7' };
    if (mape < 50) return { color: '#ed6c02', label: '⚠️ Orta', bgColor: '#fff3e0', borderColor: '#ffcc80' };
    return { color: '#d32f2f', label: '❌ Zayıf', bgColor: '#ffebee', borderColor: '#ef9a9a' };
  };

  const handleCompare = (result: ForecastResult) => {
    setSelectedMaterial(result);
    setShowComparison(true);
  };

  const prepareChartData = (result: ForecastResult) => {
    const historical = result.historical_data || [];
    const forecast = result.forecast || [];
    const lower_80 = result.lower_80 || [];
    const upper_80 = result.upper_80 || [];
    const data: any[] = [];
    historical.forEach((val, idx) => {
      data.push({
        week: idx + 1,
        historical: val,
        forecast: null,
        lower_80: null,
        upper_80: null,
      });
    });
    forecast.forEach((val, idx) => {
      const weekIndex = historical.length + idx + 1;
      data.push({
        week: weekIndex,
        historical: null,
        forecast: val,
        lower_80: lower_80[idx] || null,
        upper_80: upper_80[idx] || null,
      });
    });
    return data;
  };

  const ForecastChart = ({ result }: { result: ForecastResult }) => {
    const data: any[] = prepareChartData(result);
    return (
      <Box sx={{ width: '100%', height: 300, mt: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
          📈 Tahmin Grafiği
        </Typography>
        <ResponsiveContainer>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" label={{ value: 'Hafta', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Talep', angle: -90, position: 'insideLeft' }} />
            <RechartsTooltip />
            <Legend />
            <Area type="monotone" dataKey="upper_80" stroke="none" fill="#8884d8" fillOpacity={0.2} name="%80 Güven Aralığı" />
            <Area type="monotone" dataKey="lower_80" stroke="none" fill="#8884d8" fillOpacity={0.2} />
            <Line type="monotone" dataKey="historical" stroke="#1976d2" strokeWidth={2} dot={{ r: 3 }} name="Geçmiş Talep" connectNulls={false} />
            <Line type="monotone" dataKey="forecast" stroke="#ed6c02" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} name="Tahmin" />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  const ModelParams = ({ result }: { result: ForecastResult }) => {
    const params = result.model_params;
    if (!params || Object.keys(params).length === 0) {
      return (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          <strong>Parametreler:</strong> Detay mevcut değil.
        </Typography>
      );
    }
    let paramDetails: { key: string; value: any }[] = [];

    if (params.pattern) {
      paramDetails.push({
        key: '📊 Talep Patterni',
        value: (
          <Chip
            label={params.pattern_label || params.pattern}
            size="small"
            color={getPatternColor(params.pattern_color)}
            variant="outlined"
          />
        )
      });
      if (params.cv !== undefined) {
        paramDetails.push({ key: 'Değişkenlik (CV)', value: params.cv });
      }
      if (params.zero_ratio !== undefined) {
        paramDetails.push({ key: 'Sıfır Talep Oranı', value: params.zero_ratio });
      }
    }

    if (result.selected_model === 'holt_winters') {
      paramDetails.push(
        { key: 'Mevsimsellik Periyodu', value: `${params.seasonal_periods || '52'} hafta` },
        { key: 'Trend', value: params.trend || 'Toplanabilir (add)' },
        { key: 'Mevsimsellik', value: params.seasonal || 'Toplanabilir (add)' }
      );
      if (params.damping_trend !== undefined) {
        paramDetails.push({ key: 'Trend Sönümleme', value: params.damping_trend ? 'Aktif' : 'Pasif' });
      }
    } else if (result.selected_model === 'arima') {
      const order = params.order || '(1,1,1)';
      paramDetails.push(
        { key: 'ARIMA Order (p,d,q)', value: order },
        { key: 'Mevsimsellik', value: params.seasonal_order ? `${params.seasonal_order}` : 'Yok' }
      );
      if (params.trend !== undefined) {
        paramDetails.push({ key: 'Trend', value: params.trend ? 'Evet' : 'Hayır' });
      }
    } else if (result.selected_model === 'simple') {
      paramDetails.push(
        { key: 'Hareketli Ortalama Penceresi', value: `${params.window || 4} hafta` },
        { key: 'Ağırlıklandırma', value: params.weighted ? 'Evet (Ağırlıklı)' : 'Hayır (Eşit)' }
      );
    } else if (result.selected_model === 'auto') {
      paramDetails.push(
        { key: 'Seçim Kriteri', value: params.selection_method || 'MAPE' },
        { key: 'Test Edilen Model Sayısı', value: params.models_tested || 0 },
        { key: 'En İyi Model', value: params.best_model || 'Belirlenemedi' }
      );
      if (params.best_mape) {
        paramDetails.push({ key: 'En Düşük MAPE', value: `${params.best_mape}%` });
      }
    }

    if (params.selection_reason) {
      paramDetails.push({ key: 'Seçim Nedeni', value: params.selection_reason });
    }

    return (
      <Box sx={{ mt: 0.5, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: 'bold' }}>
          ⚙️ Model Parametreleri:
        </Typography>
        {paramDetails.length > 0 ? (
          <Table size="small" sx={{ '& .MuiTableCell-root': { border: 'none', py: 0.5, px: 1 } }}>
            <TableBody>
              {paramDetails.map((detail) => (
                <TableRow key={detail.key}>
                  <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '40%' }}>
                    {detail.key}
                  </TableCell>
                  <TableCell>{String(detail.value)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Typography variant="caption" color="text.secondary">
            Parametre bilgisi bulunamadı.
          </Typography>
        )}
      </Box>
    );
  };

  // ✅ Hero Header
  const HeroHeader = () => (
    <Card sx={{ mb: 3, borderRadius: 2, bgcolor: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)', border: '1px solid #d0e0ff' }}>
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { md: 'center' }, justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <ShowChart sx={{ fontSize: 24, color: '#1f4e79' }} />
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.3rem' }}>
                Talep Tahmini
              </Typography>
              <Chip label="Forecast" size="small" sx={{ height: 20, fontSize: '0.55rem', bgcolor: '#1f4e79', color: 'white' }} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
              Geçmiş satış verilerinizi analiz ederek önümüzdeki haftalar için talep tahmini üretir.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5, mt: { xs: 1.5, md: 0 }, flexWrap: 'wrap' }}>
            <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label="4 model" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<AutoAwesome sx={{ fontSize: 14 }} />} label="Otomatik seçim" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<TrendingUpIcon sx={{ fontSize: 14 }} />} label="Güven aralıkları" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Download sx={{ fontSize: 14 }} />} label="Excel raporu" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // ✅ KPI Kartları
  const KpiCards = () => {
    const summary = analysisSummary;
    const modelLabel = summary ? (modelLabels[summary.mostUsedModel] || summary.mostUsedModel) : '-';
    
    return (
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
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <CalendarToday sx={{ fontSize: 18, color: '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: '#1f4e79' }}>
              {horizon} Hafta
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Tahmin Ufku</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AutoAwesome sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? modelLabel : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>En Başarılı Model</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Assessment sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.avgRMSE.toFixed(2) : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama RMSE</Typography>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  // ✅ AI Yorumu Kartı
  const AICommentCard = () => {
    if (!aiComment) return null;

    return (
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#f3e5f5', border: '1px solid #ce93d8' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Psychology sx={{ fontSize: 18, color: '#6a1b9a' }} />
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#6a1b9a', fontSize: '0.8rem' }}>
              🤖 AI Analiz Özeti
            </Typography>
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 1.5 }}>
            <Box>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c' }}>
                📊 {aiComment.summary}
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c', mt: 0.5 }}>
                📈 {aiComment.trend}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c' }}>
                📅 {aiComment.seasonality}
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c', mt: 0.5 }}>
                ✅ {aiComment.confidence}
              </Typography>
            </Box>
          </Box>
          <Divider sx={{ my: 1 }} />
          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#6a1b9a', display: 'block' }}>
            💡 {aiComment.recommendation}
          </Typography>
        </CardContent>
      </Card>
    );
  };

  const isNormalAnalysisActive = activeStep >= 0 && !isAsyncComplete && !activeAsyncTask;
  const isAsyncAnalysisActive = asyncActiveStep >= 0 || isAsyncComplete;

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

      {/* Learning Score Badge - ÜSTTE */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <LearningScoreBadge variant="compact" />
      </Box>

      {/* ✅ Hero Header */}
      <HeroHeader />

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

      {/* ✅ KPI Kartları */}
      <KpiCards />

      {/* ✅ AI Yorumu (varsa) */}
      <AICommentCard />

      {/* ✅ ANA GRID - 2 SÜTUN */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        {/* ✅ SOL SÜTUN - İşlem Akışı ve Veri Durumu */}
        <Grid size={{ xs: 12, md: 5 }}>
          {/* 📦 Veri Durumu Kartı - Zenginleştirilmiş */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
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
              {hasUploadedData ? (
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5 }}>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                    <strong>{materialCount}</strong> Malzeme
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                    <strong>{weekCount}</strong> Hafta Veri
                  </Typography>
                  {lastUploadDate && (
                    <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#6b7280', gridColumn: 'span 2' }}>
                      📅 Son yükleme: {new Date(lastUploadDate).toLocaleDateString('tr-TR')}
                    </Typography>
                  )}
                </Box>
              ) : (
                !isCheckingData && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                    Lütfen Dashboard'dan Excel yükleyin
                  </Typography>
                )
              )}
            </CardContent>
          </Card>

          {/* 📋 İşlem Akışı Kartı */}
          <Card sx={{ borderRadius: 2, border: '1px solid #e8f0fe', minHeight: 200 }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <PlayArrow sx={{ fontSize: 18, color: '#1f4e79' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  İşlem Akışı
                </Typography>
                {isProcessing && (
                  <Chip
                    label={activeAsyncTask ? 'Async' : 'Normal'}
                    size="small"
                    color={activeAsyncTask ? 'secondary' : 'primary'}
                    sx={{ height: 18, fontSize: '0.5rem' }}
                  />
                )}
              </Box>

              {isNormalAnalysisActive && (
                <>
                  <AnalysisProgress 
                    steps={steps} 
                    activeStep={activeStep} 
                    isComplete={isAnalysisComplete}
                    compact={true}
                  />
                  <LinearProgress
                    variant="determinate"
                    value={progress || activeStep * 17 + 10}
                    sx={{ mt: 1, height: 3, borderRadius: 2, bgcolor: '#e8f0fe' }}
                  />
                </>
              )}

              {isAsyncAnalysisActive && (
                <AnalysisProgress 
                  steps={asyncSteps} 
                  activeStep={asyncActiveStep} 
                  isComplete={isAsyncComplete}
                  compact={true}
                />
              )}

              {!isNormalAnalysisActive && !isAsyncAnalysisActive && !isProcessing && (
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <ShowChart sx={{ fontSize: 28, color: '#b0b0b0', mb: 0.5 }} />
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', display: 'block' }}>
                    Henüz analiz yapılmadı.
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                    Tahmin üretmek için <strong>"Analiz Et"</strong> veya <strong>"Arka Planda Çalıştır"</strong> butonunu kullanın.
                  </Typography>
                </Box>
              )}

              {!isProcessing && (isAnalysisComplete || isAsyncComplete) && (
                <Box sx={{ textAlign: 'center', py: 1 }}>
                  <Chip
                    icon={<CheckCircle sx={{ fontSize: 14 }} />}
                    label="✅ Analiz tamamlandı"
                    color="success"
                    size="small"
                    sx={{ height: 24, fontSize: '0.65rem' }}
                  />
                  {activeAsyncTask && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.6rem' }}>
                      İlerlemeyi ASYNC Görevler sayfasından takip edin
                    </Typography>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* ✅ SAĞ SÜTUN - Butonlar, Model Seçimi, Ufuk */}
        <Grid size={{ xs: 12, md: 7 }}>
          {/* ✅ Butonlar */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Button
                  variant="contained"
                  size="medium"
                  startIcon={forecastMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAnalysis}
                  disabled={forecastMutation.isPending || !hasUploadedData || isProcessing}
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
                  }}
                >
                  {forecastMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
                </Button>

                <Button
                  variant="contained"
                  size="medium"
                  color="secondary"
                  startIcon={asyncForecastMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAsyncAnalysis}
                  disabled={asyncForecastMutation.isPending || !hasUploadedData || isProcessing}
                  sx={{
                    fontSize: '0.75rem',
                    textTransform: 'none',
                    py: 0.75,
                    px: 2.5,
                    borderRadius: 2,
                    flex: 1,
                    minWidth: 120,
                  }}
                >
                  {asyncForecastMutation.isPending ? 'Başlatılıyor...' : 'Arka Planda Çalıştır'}
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

          {/* ✅ Model Seçimi - Radio Card */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.7rem', mb: 1, display: 'block' }}>
                Model Seçimi
              </Typography>
              <RadioGroup
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                sx={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 1 }}
              >
                <FormControlLabel
                  value="auto"
                  control={<Radio size="small" sx={{ color: '#1f4e79' }} />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AutoAwesome sx={{ fontSize: 14, color: '#ed6c02' }} />
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: selectedModel === 'auto' ? 600 : 400 }}>
                        Otomatik ⭐
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0 }}
                />
                <FormControlLabel
                  value="holt_winters"
                  control={<Radio size="small" sx={{ color: '#1f4e79' }} />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Timeline sx={{ fontSize: 14, color: '#9c27b0' }} />
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: selectedModel === 'holt_winters' ? 600 : 400 }}>
                        Holt-Winters
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0 }}
                />
                <FormControlLabel
                  value="arima"
                  control={<Radio size="small" sx={{ color: '#1f4e79' }} />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Analytics sx={{ fontSize: 14, color: '#1976d2' }} />
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: selectedModel === 'arima' ? 600 : 400 }}>
                        ARIMA
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0 }}
                />
                <FormControlLabel
                  value="simple"
                  control={<Radio size="small" sx={{ color: '#1f4e79' }} />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ShowChart sx={{ fontSize: 14, color: '#2e7d32' }} />
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: selectedModel === 'simple' ? 600 : 400 }}>
                        Basit MA
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0 }}
                />
              </RadioGroup>
            </CardContent>
          </Card>

          {/* ✅ Tahmin Ufku - Slider */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.7rem' }}>
                  Tahmin Ufku: {horizon} Hafta
                </Typography>
              </Box>
              <Slider
                value={horizon}
                onChange={(_, val) => setHorizon(val as number)}
                min={4}
                max={52}
                step={1}
                marks={[
                  { value: 4, label: '4' },
                  { value: 12, label: '12' },
                  { value: 26, label: '26' },
                  { value: 52, label: '52' },
                ]}
                valueLabelDisplay="auto"
                size="small"
                sx={{ color: '#1f4e79' }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e' }}>
                  Kısa
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>
                  Orta
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#2e7d32' }}>
                  Uzun
                </Typography>
              </Box>
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
                    </Box>
                  ) : (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {activeDatasetId ? 'Analiz sonrası maliyet görünecek' : 'Dataset oluşturun'}
                    </Typography>
                  )}
                </Grid>

                <Grid size={{ xs: 12, sm: 4 }}>
                  {pricingPreview && pricingPreview.data_points > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block', textAlign: 'right' }}>
                      📊 {pricingPreview.product_count} ürün × {pricingPreview.period_count} dönem = {pricingPreview.data_points} veri noktası
                    </Typography>
                  )}
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Analiz Özeti (varsa) */}
          {analysisSummary && (
            <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#e8f5e9', border: '1px solid #a5d6a7' }}>
              <CardContent sx={{ py: 1.5, px: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CheckCircle sx={{ fontSize: 18, color: '#2e7d32' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2e7d32', fontSize: '0.8rem' }}>
                    Analiz Özeti
                  </Typography>
                </Box>
                <Grid container spacing={1}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      <strong>{analysisSummary.totalMaterials}</strong> ürün analiz edildi
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      En çok kullanılan model: <strong>{modelLabels[analysisSummary.mostUsedModel] || analysisSummary.mostUsedModel}</strong>
                      <Chip 
                        label={`%${analysisSummary.mostUsedModelPercent.toFixed(0)}`} 
                        size="small" 
                        color="success" 
                        sx={{ height: 18, fontSize: '0.5rem', ml: 0.5 }}
                      />
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Ortalama RMSE: <strong>{analysisSummary.avgRMSE.toFixed(2)}</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Trend: <strong>{analysisSummary.trendUpCount} Artış</strong> / <strong>{analysisSummary.trendDownCount} Azalış</strong>
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* ✅ 4 MODEL - Zenginleştirilmiş */}
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#fafcff', border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#f0f7ff', border: '1px solid #d0e0ff' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Lightbulb sx={{ fontSize: 20, color: '#1f4e79', mt: 0.25 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                    Stokonomi Akıllı Seçim
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#374151', mt: 0.25 }}>
                    Stokonomi, her malzeme için bu modellerin <strong>tamamını</strong> değerlendirir 
                    ve talep yapısına en uygun tahmin modelini <strong>otomatik olarak önerir</strong>.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Grid container spacing={1.5}>
            {modelDetails.map((model) => (
              <Grid size={{ xs: 6, sm: 3 }} key={model.key}>
                <Tooltip
                  title={
                    <Box sx={{ p: 1.5, maxWidth: 280 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem', mb: 0.5 }}>
                        {model.tooltip.title}
                      </Typography>
                      <Divider sx={{ mb: 1 }} />
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.75 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>📌</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>Ne zaman kullanılır?</Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>{model.tooltip.when}</Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.75 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>🏭</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>Örnek ürünler</Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>{model.tooltip.example}</Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>✅</Typography>
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>Avantajı</Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>{model.tooltip.advantage}</Typography>
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
                      sx: {
                        zIndex: 1300,
                      },
                    },
                  }}
                >
                  <Paper
                    sx={{
                      p: 1,
                      textAlign: 'center',
                      bgcolor: model.isRecommended ? alpha('#1f4e79', 0.06) : 'white',
                      border: model.isRecommended ? '2px solid #1f4e79' : '1px solid #e8f0fe',
                      borderRadius: 2,
                      cursor: 'default',
                      transition: 'all 0.2s',
                      position: 'relative',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                        borderColor: model.isRecommended ? '#1f4e79' : '#b0b0b0',
                      },
                    }}
                  >
                    {model.isRecommended && (
                      <Chip
                        label="⭐ Varsayılan Öneri"
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
                      {model.icon}
                      <Typography variant="caption" sx={{ fontWeight: model.isRecommended ? 700 : 500, fontSize: '0.65rem' }}>
                        {model.label}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ fontSize: '0.55rem', color: model.isRecommended ? '#1f4e79' : '#6b7280', display: 'block', mt: 0.25, fontWeight: model.isRecommended ? 500 : 400 }}>
                      {model.short}
                    </Typography>
                    {model.isRecommended && (
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
              💡 Bu analizde 4 model paralel çalıştırılır. En düşük hata oranına sahip model otomatik seçilir.
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* ✅ Sonuçlar */}
      {results.length > 0 ? (
        <Card sx={{ borderRadius: 2 }}>
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
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Malzeme</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Grup</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Model</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Outlier</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Trend</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">RMSE</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">AI Kararı</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Açıklama</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Güven</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">İncele</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => {
                    const status = getMapeStatus(result.model_rmse || 999);
                    const modelColor = modelColors[result.selected_model] || '#1976d2';
                    const aiDecision = (result as any).ai_decision;
                    
                    return (
                      <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#f8faff' } }}>
                        <TableCell sx={{ fontSize: '0.7rem' }}>{result.material_code}</TableCell>
                        <TableCell sx={{ fontSize: '0.7rem' }}>{result.group}</TableCell>
                        <TableCell>
                          <Tooltip title={`RMSE: ${result.model_rmse?.toFixed(2) || '-'}`} arrow>
                            <Chip
                              label={result.best_model_label}
                              size="small"
                              sx={{
                                bgcolor: modelColor,
                                color: 'white',
                                fontWeight: 'bold',
                                height: 20,
                                fontSize: '0.55rem',
                              }}
                            />
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">
                          {result.outlier_info?.has_outliers ? (
                            <Tooltip title={`${result.outlier_info.outlier_count} aykırı değer var`} arrow>
                              <Chip 
                                label="⚠️" 
                                size="small" 
                                sx={{ 
                                  height: 20, 
                                  fontSize: '0.5rem',
                                  bgcolor: '#fff3e0',
                                  color: '#ed6c02',
                                  border: '1px solid #ffcc80',
                                  fontWeight: 600,
                                }} 
                              />
                            </Tooltip>
                          ) : (
                            <Chip 
                              label="✅" 
                              size="small" 
                              sx={{ 
                                height: 20, 
                                fontSize: '0.5rem',
                                bgcolor: '#e8f5e9',
                                color: '#2e7d32',
                                border: '1px solid #a5d6a7',
                                fontWeight: 600,
                              }} 
                            />
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            icon={result.trend_direction === 'Artış' ? <TrendingUp sx={{ fontSize: 14 }} /> : <TrendingDown sx={{ fontSize: 14 }} />}
                            label={`${result.trend_percent > 0 ? '+' : ''}${result.trend_percent}%`}
                            size="small"
                            color={result.trend_direction === 'Artış' ? 'error' : 'success'}
                            variant="outlined"
                            sx={{ height: 18, fontSize: '0.5rem' }}
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                          {result.model_rmse?.toFixed(2) || '-'}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={aiDecision?.decision === 'change_forecast_model' ? '📊 Model Değiştir' :
                                   aiDecision?.decision === 'maintain_current' ? '✅ Koru' :
                                   aiDecision?.decision === 'investigate_variability' ? '🔍 Araştır' : '🔍 İncele'}
                            size="small"
                            color={aiDecision?.decision === 'change_forecast_model' ? 'warning' :
                                   aiDecision?.decision === 'maintain_current' ? 'success' : 'default'}
                            sx={{ height: 18, fontSize: '0.5rem' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Button
                            size="small"
                            variant="text"
                            onClick={() => setSelectedReasoning(result)}
                            sx={{ fontSize: '0.5rem', textTransform: 'none', minWidth: 'auto' }}
                          >
                            Neden?
                          </Button>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={`%${Math.round((aiDecision?.confidence || 0.5) * 100)}`}
                            size="small"
                            color={(aiDecision?.confidence || 0) > 0.7 ? 'success' : 'warning'}
                            sx={{ height: 18, fontSize: '0.45rem', fontWeight: 600 }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleCompare(result)}
                            sx={{ fontSize: '0.55rem', textTransform: 'none' }}
                          >
                            İncele
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
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
          </CardContent>
        </Card>
      ) : (
        !isProcessing && !activeAsyncTask && !error && hasUploadedData && !isCheckingData && (
          <Card sx={{ borderRadius: 2, border: '1px dashed #e0e0e0', bgcolor: '#fafcff' }}>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <ShowChart sx={{ fontSize: 40, color: '#b0b0b0', mb: 1 }} />
              <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
                Henüz analiz yapılmadı
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                "Analiz Et" veya "Arka Planda Çalıştır" butonuna tıklayın
              </Typography>
            </CardContent>
          </Card>
        )
      )}

      {/* ✅ AI Neden Bu Kararı Verdi? - Dialog */}
      <Dialog
        open={!!selectedReasoning}
        onClose={() => setSelectedReasoning(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.95rem' }}>
              🤖 AI Karar Açıklaması
            </Typography>
            <IconButton onClick={() => setSelectedReasoning(null)} size="small">
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          {selectedReasoning && (
            <Box>
              <AIReasoningSection result={selectedReasoning} />
              <Box sx={{ mt: 2 }}>
                <TechnicalAnalysisSection result={selectedReasoning} />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1.5 }}>
          <Button onClick={() => setSelectedReasoning(null)} size="small" sx={{ fontSize: '0.7rem', textTransform: 'none' }}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>

      {/* 📊 Model Karşılaştırma Dialog */}
      <Dialog open={showComparison} onClose={() => setShowComparison(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.95rem' }}>
              📊 Model Karşılaştırması
            </Typography>
            <IconButton onClick={() => setShowComparison(false)} size="small">
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedMaterial && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, fontSize: '0.8rem' }}>
                Malzeme: {selectedMaterial.material_code} - {selectedMaterial.group}
              </Typography>

              {selectedMaterial.outlier_info?.has_outliers && (
                <Alert severity="warning" sx={{ mb: 2, fontSize: '0.75rem' }}>
                  ⚠️ Veride {selectedMaterial.outlier_info.outlier_count} aykırı değer tespit edildi!
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.65rem' }}>
                    {selectedMaterial.outlier_info.outliers.map((o: any) => `Hafta ${o.week}: ${o.value}`).join(' | ')}
                  </Typography>
                </Alert>
              )}

              <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                <CardContent sx={{ py: 1, px: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem' }}>
                      Model Başarısı (RMSE):
                    </Typography>
                    <Chip
                      label={getMapeStatus(selectedMaterial.model_rmse || 999).label}
                      sx={{
                        height: 20,
                        fontSize: '0.55rem',
                        fontWeight: 600,
                        bgcolor: getMapeStatus(selectedMaterial.model_rmse || 999).bgColor,
                        color: getMapeStatus(selectedMaterial.model_rmse || 999).color,
                        border: `1px solid ${getMapeStatus(selectedMaterial.model_rmse || 999).borderColor}`,
                      }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {getMapeStatus(selectedMaterial.model_rmse || 999).label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                      Değer: {selectedMaterial.model_rmse?.toFixed(1) || '?'}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1.5 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f0f7ff' }}>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Model</TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">RMSE</TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">1.Hafta</TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Son Hafta</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(selectedMaterial.model_comparison || {}).map(([modelName, data]: [string, any]) => (
                      <TableRow
                        key={modelName}
                        sx={{ bgcolor: modelName === selectedMaterial.selected_model ? alpha('#1f4e79', 0.08) : 'inherit' }}
                      >
                        <TableCell>
                          {modelLabels[modelName] || modelName}
                          {modelName === selectedMaterial.selected_model && (
                            <Chip label="✅ Seçili" size="small" color="success" sx={{ height: 16, fontSize: '0.5rem', ml: 0.5 }} />
                          )}
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.7rem' }}>{data.rmse?.toFixed(2) || '-'}</TableCell>
                        <TableCell align="center" sx={{ fontSize: '0.7rem' }}>{data.forecast?.[0]?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="center" sx={{ fontSize: '0.7rem' }}>{data.forecast?.[data.forecast.length - 1]?.toFixed(0) || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <ModelParams result={selectedMaterial} />
              <ForecastChart result={selectedMaterial} />

              <Box sx={{ mt: 2, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#0d47a1' }}>
                  <strong>📌 Seçim Nedeni:</strong> {selectedMaterial.selection_reason}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1.5 }}>
          <Button onClick={() => setShowComparison(false)} size="small" sx={{ fontSize: '0.7rem', textTransform: 'none' }}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>

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
                    const timeStr = itemDate.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
                    const status = item.data?.status || 'completed';
                    const statusConfig = {
                      completed: { label: '✅ Tamamlandı', color: 'success' },
                      processing: { label: '🔄 İşleniyor', color: 'warning' },
                      pending: { label: '⏳ Bekliyor', color: 'info' },
                      failed: { label: '❌ Başarısız', color: 'error' },
                    };
                    const statusInfo = statusConfig[status as keyof typeof statusConfig] || statusConfig.completed;
                    
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
                          {item.data?.report_name || 'Talep Tahmini Analizi'}
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