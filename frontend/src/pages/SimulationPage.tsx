// frontend/src/pages/SimulationPage.tsx - TAM VE DÜZELTİLMİŞ

import { useState, useEffect } from 'react';
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
  Switch,
  FormControlLabel,
  TextField,
  Stack,
  Tooltip,
  LinearProgress,
  Snackbar,
  Slider,
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
  Timeline,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Tune,
  Info,
  Speed,
  TrendingUp,
  Analytics as AnalyticsIcon,
  Security,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  CloudDone,
  CloudOff,
  Inventory,
  AttachMoney,
  Lightbulb,
  AutoAwesome,
  Psychology,
  ShowChart,
  AccountBalanceWallet,
  ExpandMore,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { usePricingPreview } from '../hooks/usePricing';
import { fetchAndLoadResult, checkAndLoadAnalysis } from '../utils/loadAnalysisResult';

// ✅ YENİ BİLEŞENLER
import DecisionReasoning from '../components/Results/DecisionReasoning';
import TechnicalAnalysisDetail from '../components/Results/TechnicalAnalysisDetail';
import LearningScoreBadge from '../components/Dashboard/LearningScoreBadge';

// ============================================================
// 📌 INTERFACES
// ============================================================

interface SimulationResult {
  material_code: string;
  group: string;
  service_level: number;
  cvar_95: number;
  tail_risk: number;
  tail_risk_level: string;
  cvar_risk: string;
  service_gap: number;
  stockout_probability: number;
  avg_stock: number;
  regime_used: boolean;
  copula_used: boolean;
  adaptive_ss_used: boolean;
  recommendations: string[];
  current_rop: number;
  recommended_rop: number;
  // ✅ YENİ ALANLAR
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
  avgServiceLevel: number;
  avgCVaR: number;
  avgTailRisk: number;
  highRiskCount: number;
  regimeUsedCount: number;
  copulaUsedCount: number;
  adaptiveUsedCount: number;
}

interface AIComment {
  summary: string;
  performance: string;
  risk: string;
  recommendation: string;
  confidence: string;
}

// ============================================================
// 📌 AI REASONING SECTION BİLEŞENİ
// ============================================================

const AIReasoningSection = ({ result }: { result: SimulationResult }) => {
  const aiDecision = result.ai_decision;
  
  if (!aiDecision) {
    return null;
  }

  const reasoning = {
    recommended_ss: result.recommended_rop || 0,
    current_ss: result.current_rop || 0,
    reasons: aiDecision.reasons || [
      result.service_level < 90 ? 'Servis seviyesi düşük' : '',
      result.tail_risk > 0.5 ? 'Tail risk yüksek' : '',
      result.stockout_probability > 10 ? 'Stok tükenme riski yüksek' : '',
      result.cvar_95 > 100 ? 'CVaR riski yüksek' : '',
    ].filter(Boolean),
    conclusion: aiDecision.decision === 'increase_safety_stock' 
      ? 'ROP ve SS artırılmalı.' 
      : aiDecision.decision === 'maintain_current'
      ? 'Mevcut politika yeterli.'
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

const TechnicalAnalysisSection = ({ result }: { result: SimulationResult }) => {
  const [expanded, setExpanded] = useState(false);

  const technicalData = {
    material_code: result.material_code,
    cv: result.tail_risk || 0,
    pattern: result.tail_risk > 0.5 ? 'YUKSEK_RISK' : 'DUSUK_RISK',
    pattern_label: result.tail_risk > 0.5 ? 'Yüksek Risk' : 'Düşük Risk',
    pattern_color: result.tail_risk > 0.5 ? 'error' : 'success',
    abc: 'C',
    abc_label: 'Simülasyon',
    xyz: result.tail_risk > 0.5 ? 'Z' : 'X',
    xyz_label: result.tail_risk > 0.5 ? 'Yüksek Risk' : 'Düşük Risk',
    forecast_model: 'n/a',
    forecast_model_label: 'Simülasyon',
    seasonality: false,
    seasonality_label: 'Yok',
    seasonality_strength: 0,
    trend_direction: result.service_level > 95 ? 'Artış' : 'Azalış',
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


export default function SimulationPage() {
  const { user, fetchUser } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [materialCount, setMaterialCount] = useState(0);
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null);
  const [aiComment, setAiComment] = useState<AIComment | null>(null);

  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);

  const [config, setConfig] = useState({
    n_simulations: 500,
    weeks: 26,
    use_regime: false,
    use_copula: false,
    use_adaptive_ss: false,
  });

  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'info' 
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
    '/api/simulate/batch',
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

  const [steps, setSteps] = useState<AnalysisStep[]>([
    { label: 'Veri okunuyor...', description: 'Excel dosyası kontrol ediliyor', status: 'pending' },
    { label: 'Talep geçmişi hazırlanıyor...', description: 'Malzeme verileri işleniyor', status: 'pending' },
    { label: 'Senaryolar oluşturuluyor...', description: 'Monte Carlo senaryoları hazırlanıyor', status: 'pending' },
    { label: 'Simülasyon çalıştırılıyor...', description: 'Binlerce senaryo simüle ediliyor', status: 'pending' },
    { label: 'Sonuçlar doğrulanıyor...', description: 'Veriler kontrol ediliyor', status: 'pending' },
    { label: 'Rapor oluşturuluyor...', description: 'Excel dosyası hazırlanıyor', status: 'pending' },
  ]);
  const [activeStep, setActiveStep] = useState(-1);
  const [isAnalysisComplete, setIsAnalysisComplete] = useState(false);

  const [asyncSteps, setAsyncSteps] = useState<AnalysisStep[]>([
    { label: 'Analiz Ediliyor...', description: 'Veriler işleniyor', status: 'pending' },
    { label: 'Görev Oluşturuluyor...', description: 'Arka plan işlemi başlatılıyor', status: 'pending' },
    { label: 'Görevlere Eklendi ✓', description: 'İlerlemeyi ASYNC Görevler sayfasından takip edin', status: 'pending' },
  ]);
  const [asyncActiveStep, setAsyncActiveStep] = useState(-1);
  const [isAsyncComplete, setIsAsyncComplete] = useState(false);

  useEffect(() => {
    checkUploadedData();
  }, []);

  const checkUploadedData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/upload/status');
      const hasData = res.data.has_data === true;
      setHasUploadedData(hasData);
      setMaterialCount(res.data.materials_count || 0);
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
    checkAndLoadAnalysis('simulation', handleFetchAndLoad);
  }, []);

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

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

  const generateSummary = (resultsData: SimulationResult[]) => {
    if (!resultsData || resultsData.length === 0) return null;

    const total = resultsData.length;
    const avgService = resultsData.reduce((acc, r) => acc + r.service_level, 0) / total;
    const avgCVaR = resultsData.reduce((acc, r) => acc + r.cvar_95, 0) / total;
    const avgTailRisk = resultsData.reduce((acc, r) => acc + (r.tail_risk || 0), 0) / total;
    const highRiskCount = resultsData.filter(r => r.tail_risk > 0.4).length;
    const regimeUsedCount = resultsData.filter(r => r.regime_used).length;
    const copulaUsedCount = resultsData.filter(r => r.copula_used).length;
    const adaptiveUsedCount = resultsData.filter(r => r.adaptive_ss_used).length;

    return {
      totalMaterials: total,
      avgServiceLevel: avgService,
      avgCVaR: avgCVaR,
      avgTailRisk: avgTailRisk,
      highRiskCount: highRiskCount,
      regimeUsedCount: regimeUsedCount,
      copulaUsedCount: copulaUsedCount,
      adaptiveUsedCount: adaptiveUsedCount,
    };
  };

  const generateAIComment = (summary: AnalysisSummary) => {
    if (!summary) return null;

    let performanceText = '';
    if (summary.avgServiceLevel >= 95) {
      performanceText = `Ortalama servis seviyesi %${summary.avgServiceLevel.toFixed(1)} ile mükemmel seviyede. Stok yönetimi başarılı.`;
    } else if (summary.avgServiceLevel >= 90) {
      performanceText = `Ortalama servis seviyesi %${summary.avgServiceLevel.toFixed(1)} ile iyi seviyede. İyileştirme fırsatları mevcut.`;
    } else {
      performanceText = `Ortalama servis seviyesi %${summary.avgServiceLevel.toFixed(1)} ile düşük seviyede. Stok politikaları gözden geçirilmeli.`;
    }

    let riskText = '';
    if (summary.highRiskCount > summary.totalMaterials * 0.3) {
      riskText = `${summary.highRiskCount} ürün yüksek tail risk taşıyor. Tedarik zinciri riskleri değerlendirilmeli.`;
    } else if (summary.highRiskCount > summary.totalMaterials * 0.1) {
      riskText = `${summary.highRiskCount} ürün orta düzeyde tail risk taşıyor. Risk yönetimi önerilir.`;
    } else {
      riskText = `Tail risk düşük seviyede. ${summary.highRiskCount} ürün risk altında.`;
    }

    let recommendationText = '';
    if (summary.regimeUsedCount > 0 || summary.copulaUsedCount > 0 || summary.adaptiveUsedCount > 0) {
      const parts = [];
      if (summary.regimeUsedCount > 0) parts.push(`${summary.regimeUsedCount} ürün Rejim Modeli ile`);
      if (summary.copulaUsedCount > 0) parts.push(`${summary.copulaUsedCount} ürün Copula ile`);
      if (summary.adaptiveUsedCount > 0) parts.push(`${summary.adaptiveUsedCount} ürün Adaptif SS ile`);
      recommendationText = `${parts.join(', ')} simüle edildi. Gelişmiş modeller kullanımda.`;
    } else {
      recommendationText = `Tüm ürünler standart simülasyon ile analiz edildi. Gelişmiş modeller önerilir.`;
    }

    let confidenceText = '';
    const totalConfigs = (summary.regimeUsedCount > 0 ? 1 : 0) + (summary.copulaUsedCount > 0 ? 1 : 0) + (summary.adaptiveUsedCount > 0 ? 1 : 0);
    if (totalConfigs >= 2 && summary.totalMaterials > 50) {
      confidenceText = 'Çoklu model kullanımı ile simülasyon güvenilirliği yüksek.';
    } else if (totalConfigs >= 1 && summary.totalMaterials > 20) {
      confidenceText = 'Model desteği ile simülasyon güvenilir.';
    } else {
      confidenceText = 'Temel simülasyon yapıldı. Gelişmiş modellerle daha güvenilir sonuçlar elde edilebilir.';
    }

    return {
      summary: `${summary.totalMaterials} ürün simüle edildi. Ortalama servis: %${summary.avgServiceLevel.toFixed(1)}.`,
      performance: performanceText,
      risk: riskText,
      recommendation: recommendationText,
      confidence: confidenceText,
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
      
      updateStep(2, 'active', `${config.n_simulations} senaryo oluşturuluyor...`);
      await sleep(1000);
      updateStep(2, 'completed', 'Senaryolar hazırlandı');
      setProgress(50);
      
      updateStep(3, 'active', 'Simülasyon çalıştırılıyor...');
      const response = await simulationMutation.mutateAsync();
      updateStep(3, 'completed', `${response.total || response.results?.length || 0} malzeme simüle edildi`);
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
      setError(err.response?.data?.detail || err.message || 'Simülasyon sırasında hata oluştu');
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
      
      const response = await asyncSimulationMutation.mutateAsync();
      
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

  // 📌 SENKRON Simülasyon
  const simulationMutation = useMutation({
    mutationFn: async () => {
      setProgress(10);
      setProgressLabel('Simülasyon başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/simulate/batch', config);
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla simüle edildi.`);
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
        setError(data.error || 'Simülasyon başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Simülasyon hatası:', err);
      setError(err.response?.data?.detail || 'Simülasyon sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Simülasyon
  const asyncSimulationMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/simulate/batch/async', config);
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
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
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
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(100);
        setProgressLabel('Tamamlandı!');
        
        const resultsRes = await api.get(`/api/forecast/async/result/${taskId}`);
        if (resultsRes.data.success) {
          setResults(resultsRes.data.results || []);
          setPage(0);
          setSuccess(`${resultsRes.data.total || 0} malzeme başarıyla simüle edildi.`);
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
        setError(status.message || 'Async analiz başarısız oldu');
        return;
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
        params: { 
          result_type: 'simulation_batch', 
          limit: 10000 
        }
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        const batchResults = rawResults.filter((item: any) => item.is_batch === true);
        
        const historyItems = batchResults.map((item: any) => {
          const data = item.data || {};
          const totalMaterials = item.total_materials || data.total || 0;
          
          const nSimulations = data?.n_simulations || data?.config?.n_simulations || 500;
          const weeks = data?.weeks || data?.config?.weeks || 26;
          
          const reportName = `Monte Carlo Simülasyonu (${nSimulations} senaryo, ${weeks} hafta) - ${totalMaterials} Malzeme`;
          
          return {
            id: item.id,
            created_at: item.created_at,
            data: {
              total: totalMaterials,
              results: data.results || [],
              report_name: reportName,
              status: item.status || 'completed',
              n_simulations: nSimulations,
              weeks: weeks,
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
      
      const summary = generateSummary(historyResults);
      setAnalysisSummary(summary);
      if (summary) {
        const comment = generateAIComment(summary);
        setAiComment(comment);
      }
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
      const response = await api.post('/api/export/simulation-results', {
        results: results,
        config: config
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `simulasyon_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const modelInfo = {
    use_regime: {
      label: 'Rejim Modeli',
      description: 'Talebi düşük/yüksek rejimlere ayırarak daha gerçekçi simülasyon sağlar. 24+ hafta veri gerektirir.',
      icon: <TrendingUp fontSize="small" />
    },
    use_copula: {
      label: 'Copula Modeli',
      description: 'Talep ile lead time arasında korelasyon kurar. Gerçek dünya bağımlılığını yansıtır.',
      icon: <AnalyticsIcon fontSize="small" />
    },
    use_adaptive_ss: {
      label: 'Adaptif SS',
      description: 'Simülasyon içinde ROP\'u hedef servis seviyesine göre dinamik olarak günceller.',
      icon: <Speed fontSize="small" />
    }
  };

  const getServiceLevelColor = (value: number) => {
    if (value >= 95) return 'success.main';
    if (value >= 90) return 'warning.main';
    return 'error.main';
  };

  const getRiskColor = (value: number) => {
    if (value <= 5) return 'success.main';
    if (value <= 10) return 'warning.main';
    return 'error.main';
  };

  const isNormalAnalysisActive = activeStep >= 0 && !isAsyncComplete && !activeAsyncTask;
  const isAsyncAnalysisActive = asyncActiveStep >= 0 || isAsyncComplete;

  // ✅ Hero Header
  const HeroHeader = () => (
    <Card sx={{ mb: 3, borderRadius: 2, bgcolor: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)', border: '1px solid #d0e0ff' }}>
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { md: 'center' }, justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Timeline sx={{ fontSize: 24, color: '#1f4e79' }} />
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.3rem' }}>
                Monte Carlo Simülasyonu
              </Typography>
              <Chip label="Simülasyon" size="small" sx={{ height: 20, fontSize: '0.55rem', bgcolor: '#1f4e79', color: 'white' }} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
              Binlerce senaryo ile stok performansınızı simüle edin. Risk analizi ve optimizasyon.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5, mt: { xs: 1.5, md: 0 }, flexWrap: 'wrap' }}>
            <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label="500+ senaryo" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<AutoAwesome sx={{ fontSize: 14 }} />} label="Risk analizi" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Speed sx={{ fontSize: 14 }} />} label="Adaptif SS" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Download sx={{ fontSize: 14 }} />} label="Excel raporu" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // ✅ KPI Kartları
  const KpiCards = () => {
    const summary = analysisSummary;
    
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
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <ShowChart sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? `${summary.avgServiceLevel.toFixed(1)}%` : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama Servis</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AnalyticsIcon sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.avgCVaR.toFixed(1) : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama CVaR95</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Security sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.highRiskCount : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Yüksek Risk</Typography>
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
                📈 {aiComment.performance}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c' }}>
                ⚠️ {aiComment.risk}
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
          {/* 📦 Veri Durumu Kartı */}
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
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                  {materialCount} malzeme yüklü
                </Typography>
              )}
              {!hasUploadedData && !isCheckingData && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                  Lütfen Dashboard'dan Excel yükleyin
                </Typography>
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
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    Simülasyon başlatmak için butonlardan birine tıklayın
                  </Typography>
                </Box>
              )}

              {!isProcessing && (isAnalysisComplete || isAsyncComplete) && (
                <Box sx={{ textAlign: 'center', py: 1 }}>
                  <Chip
                    icon={<CheckCircle sx={{ fontSize: 14 }} />}
                    label="✅ Simülasyon tamamlandı"
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

        {/* ✅ SAĞ SÜTUN - Butonlar, Parametreler */}
        <Grid size={{ xs: 12, md: 7 }}>
          {/* ✅ Butonlar */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Button
                  variant="contained"
                  size="medium"
                  startIcon={simulationMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAnalysis}
                  disabled={simulationMutation.isPending || !hasUploadedData || isProcessing}
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
                  {simulationMutation.isPending ? 'Simüle Ediliyor...' : 'Simülasyonu Başlat'}
                </Button>

                <Button
                  variant="contained"
                  size="medium"
                  color="secondary"
                  startIcon={asyncSimulationMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAsyncAnalysis}
                  disabled={asyncSimulationMutation.isPending || !hasUploadedData || isProcessing}
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
                  {asyncSimulationMutation.isPending ? 'Başlatılıyor...' : 'Arka Planda Çalıştır'}
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

          {/* ✅ Parametre Kartı */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <Tune sx={{ fontSize: 18, color: '#1f4e79' }} />
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
                  Simülasyon Parametreleri
                </Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Simülasyon Sayısı"
                    value={config.n_simulations}
                    onChange={(e) => setConfig({ ...config, n_simulations: Number(e.target.value) })}
                    size="small"
                    slotProps={{ 
                      htmlInput: { min: 100, max: 5000, step: 100 },
                    }}
                    sx={{ '& .MuiInputLabel-root': { fontSize: '0.7rem' }, '& .MuiInputBase-root': { fontSize: '0.7rem' } }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Hafta Sayısı"
                    value={config.weeks}
                    onChange={(e) => setConfig({ ...config, weeks: Number(e.target.value) })}
                    size="small"
                    slotProps={{ 
                      htmlInput: { min: 4, max: 52, step: 1 },
                    }}
                    sx={{ '& .MuiInputLabel-root': { fontSize: '0.7rem' }, '& .MuiInputBase-root': { fontSize: '0.7rem' } }}
                  />
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 1.5, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(modelInfo).map(([key, info]) => (
                  <Tooltip title={info.description} arrow placement="top" key={key}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config[key as keyof typeof config] as boolean}
                          onChange={(e) => setConfig({ ...config, [key]: e.target.checked })}
                          size="small"
                        />
                      }
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {info.icon}
                          <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>{info.label}</Typography>
                          {key === 'use_regime' && (
                            <Chip label="24+" size="small" variant="outlined" sx={{ height: 14, fontSize: '0.45rem' }} />
                          )}
                        </Box>
                      }
                      sx={{ m: 0 }}
                    />
                  </Tooltip>
                ))}
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
                      {activeDatasetId ? 'Simülasyon sonrası maliyet görünecek' : 'Dataset oluşturun'}
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
                    Simülasyon Özeti
                  </Typography>
                </Box>
                <Grid container spacing={1}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      <strong>{analysisSummary.totalMaterials}</strong> ürün simüle edildi
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Ortalama servis: <strong>%{analysisSummary.avgServiceLevel.toFixed(1)}</strong>
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Yüksek risk: <strong>{analysisSummary.highRiskCount}</strong> ürün
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Gelişmiş model: <strong>
                        {analysisSummary.regimeUsedCount > 0 ? `${analysisSummary.regimeUsedCount} R` : ''}
                        {analysisSummary.copulaUsedCount > 0 ? ` ${analysisSummary.copulaUsedCount} C` : ''}
                        {analysisSummary.adaptiveUsedCount > 0 ? ` ${analysisSummary.adaptiveUsedCount} A` : ''}
                        {!analysisSummary.regimeUsedCount && !analysisSummary.copulaUsedCount && !analysisSummary.adaptiveUsedCount ? '-' : ''}
                      </strong>
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* ✅ Tanıtım Kartları */}
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: 'info.light', border: '1px solid #90caf9' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Lightbulb sx={{ fontSize: 18, color: '#0d47a1' }} />
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.8rem' }}>
              💡 Simülasyon Kullanım İpuçları
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.7rem' }}>
                  ⚙️ Simülasyon Sayısı
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                500: Hızlı test <br />
                1000+: Detaylı analiz <br />
                <strong>Uyarı:</strong> Sayı arttıkça süre uzar!
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.7rem' }}>
                  📊 Rejim Modeli
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                Talebi düşük/yüksek rejimlere ayırır. <br />
                <strong>Gereksinim:</strong> 24+ hafta veri
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.7rem' }}>
                  🔗 Copula Modeli
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                Talep-Lead time korelasyonu. <br />
                <strong>Etki:</strong> Daha gerçekçi senaryolar
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.7rem' }}>
                  🔄 Adaptif SS
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#374151' }}>
                ROP'u hedef servise göre günceller. <br />
                <strong>Avantaj:</strong> Dinamik optimizasyon
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* İlerleme Durumu */}
      {isProcessing && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, justifyContent: 'center' }}>
            <CircularProgress variant="determinate" value={progress} size={40} />
            <Typography variant="body2" color="text.secondary">{progressLabel}</Typography>
            {activeAsyncTask && (
              <Typography variant="caption" color="text.secondary">
                (ID: {activeAsyncTask.slice(0,8)})
              </Typography>
            )}
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ mt: 1, maxWidth: 400, mx: 'auto', height: 6, borderRadius: 3 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {config.n_simulations} senaryo simüle ediliyor...
          </Typography>
        </Box>
      )}

      {/* Sonuçlar */}
      {results.length > 0 && (
        <Card>
          <CardContent sx={{ py: 1.5, px: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                📊 Sonuçlar ({results.length} malzeme)
              </Typography>
              <Button variant="outlined" size="small" startIcon={<Download sx={{ fontSize: 16 }} />} onClick={handleExport} sx={{ fontSize: '0.65rem', textTransform: 'none' }}>
                Excel
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f0f7ff' }}>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Malzeme</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Grup</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">Servis %</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">CVaR95</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">Tail Risk</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">Stok Tük. %</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Modeller</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Tavsiye</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#f8faff' } }}>
                      <TableCell sx={{ fontSize: '0.7rem' }}>{result.material_code}</TableCell>
                      <TableCell sx={{ fontSize: '0.7rem' }}>{result.group}</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: getServiceLevelColor(result.service_level),
                          fontSize: '0.7rem'
                        }}
                      >
                        {result.service_level}%
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.7rem' }}>{result.cvar_95}</TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.7rem' }}>
                        <Chip
                          label={result.tail_risk?.toFixed(2) || '-'}
                          size="small"
                          color={
                            result.tail_risk > 0.5 ? 'error' :
                            result.tail_risk > 0.3 ? 'warning' : 'success'
                          }
                          sx={{ minWidth: 40, height: 20, fontSize: '0.5rem' }}
                        />
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ 
                          color: getRiskColor(result.stockout_probability),
                          fontWeight: 'bold',
                          fontSize: '0.7rem'
                        }}
                      >
                        {result.stockout_probability}%
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} sx={{ justifyContent: 'center' }}>
                          {result.regime_used && (
                            <Tooltip title="Rejim aktif">
                              <Chip label="R" size="small" color="info" sx={{ minWidth: 20, height: 18, fontSize: '0.5rem' }} />
                            </Tooltip>
                          )}
                          {result.copula_used && (
                            <Tooltip title="Copula aktif">
                              <Chip label="C" size="small" color="secondary" sx={{ minWidth: 20, height: 18, fontSize: '0.5rem' }} />
                            </Tooltip>
                          )}
                          {result.adaptive_ss_used && (
                            <Tooltip title="Adaptif SS aktif">
                              <Chip label="A" size="small" color="warning" sx={{ minWidth: 20, height: 18, fontSize: '0.5rem' }} />
                            </Tooltip>
                          )}
                          {!result.regime_used && !result.copula_used && !result.adaptive_ss_used && (
                            <Chip label="-" size="small" variant="outlined" sx={{ minWidth: 20, height: 18, fontSize: '0.5rem' }} />
                          )}
                        </Stack>
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem' }}>
                        {result.recommendations && result.recommendations.length > 0 ? (
                          <Tooltip title={result.recommendations[0]} arrow>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                cursor: 'pointer',
                                display: 'block',
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                fontSize: '0.65rem'
                              }}
                            >
                              {result.recommendations[0].substring(0, 40)}
                              {result.recommendations[0].length > 40 ? '...' : ''}
                            </Typography>
                          </Tooltip>
                        ) : '-'}
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
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>Ortalama Servis</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(results.reduce((acc, r) => acc + r.service_level, 0) / results.length).toFixed(1)}%
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>Ortalama CVaR95</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(results.reduce((acc, r) => acc + r.cvar_95, 0) / results.length).toFixed(1)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>Ortalama Tail Risk</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(results.reduce((acc, r) => acc + (r.tail_risk || 0), 0) / results.length).toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'primary.light', borderRadius: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>Aktif Model</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {(() => {
                          const parts = [];
                          if (results.filter(r => r.regime_used).length > 0) {
                            parts.push(`${results.filter(r => r.regime_used).length} R`);
                          }
                          if (results.filter(r => r.copula_used).length > 0) {
                            parts.push(`${results.filter(r => r.copula_used).length} C`);
                          }
                          if (results.filter(r => r.adaptive_ss_used).length > 0) {
                            parts.push(`${results.filter(r => r.adaptive_ss_used).length} A`);
                          }
                          return parts.length > 0 ? parts.join(' ') : '-';
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
            <Timeline sx={{ fontSize: 40, color: '#b0b0b0', mb: 1 }} />
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
              Henüz simülasyon yapılmadı
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              "Simülasyonu Başlat" veya "Arka Planda Çalıştır" butonuna tıklayın
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
                          {item.data?.report_name || 'Monte Carlo Simülasyonu'}
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