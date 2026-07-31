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
  Tooltip,
  Snackbar,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  Stack,
  Avatar,
  alpha,
  // ✅ EKSİK IMPORT'LAR
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  LocalShipping,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
  Warning,
  CheckCircle,
  Error,
  Security,
  PlayArrow,
  CloudDone,
  CloudOff,
  Inventory,
  AttachMoney,
  Lightbulb,
  AutoAwesome,
  Psychology,
  ShowChart,
  Speed,
  Analytics as AnalyticsIcon,
  TrendingUp,
  TrendingDown,
  Pending,
  AccountBalanceWallet,
  // ✅ EKSİK IMPORT
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
// 📌 INTERFACES
// ============================================================

interface SupplierResult {
  supplier_id: string;
  name: string;
  risk_score: number;
  performance_score: number;
  ontime_rate: number;
  lt_mean: number;
  lt_std: number;
  factor: number;
  material_count: number;
  total_share: number;
  risk_level: string;
  performance_level: string;
  recommendation: string;
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
  totalSuppliers: number;
  avgRiskScore: number;
  avgPerformanceScore: number;
  avgOntimeRate: number;
  highRiskCount: number;
  lowRiskCount: number;
  topSupplier: string;
  topSupplierScore: number;
}

interface AIComment {
  summary: string;
  risk: string;
  performance: string;
  recommendation: string;
  confidence: string;
}

// ============================================================
// 📌 AI REASONING SECTION BİLEŞENİ
// ============================================================

const AIReasoningSection = ({ result }: { result: SupplierResult }) => {
  const aiDecision = result.ai_decision;
  
  if (!aiDecision) {
    return null;
  }

  const reasoning = {
    recommended_ss: 0,
    current_ss: 0,
    reasons: aiDecision.reasons || [
      result.risk_score > 0.7 ? 'Yüksek risk skoru' : '',
      result.performance_score < 0.4 ? 'Düşük performans' : '',
      result.ontime_rate < 80 ? 'Zamanında teslimat oranı düşük' : '',
      result.lt_mean > 21 ? 'Lead Time uzun' : '',
    ].filter(Boolean),
    conclusion: aiDecision.decision === 'review_supplier' 
      ? 'Tedarikçi gözden geçirilmeli.' 
      : aiDecision.decision === 'maintain_current'
      ? 'Mevcut tedarikçi performansı yeterli.'
      : 'Detaylı analiz önerilir.',
    confidence: aiDecision.confidence || 0.5,
    factors: {
      cv: 0,
      lead_time: result.lt_mean || 14,
      intermittent: false,
      seasonal: false,
      risk_score: result.risk_score || 0,
      pattern: result.performance_level || 'ORTA',
    }
  };

  return (
    <Box sx={{ mt: 1 }}>
      <DecisionReasoning
        materialCode={result.supplier_id}
        reasoning={reasoning}
      />
    </Box>
  );
};

// ============================================================
// 📌 TEKNİK ANALİZ BÖLÜMÜ - ACCORDION
// ============================================================

const TechnicalAnalysisSection = ({ result }: { result: SupplierResult }) => {
  const [expanded, setExpanded] = useState(false);

  const technicalData = {
    material_code: result.supplier_id,
    cv: result.risk_score || 0,
    pattern: result.performance_level || 'ORTA',
    pattern_label: result.performance_level || 'Orta',
    pattern_color: result.performance_level === 'İYİ' ? 'success' : result.performance_level === 'ORTA' ? 'warning' : 'error',
    abc: 'C',
    abc_label: 'Tedarikçi',
    xyz: result.risk_level === 'DÜŞÜK' ? 'X' : result.risk_level === 'ORTA' ? 'Y' : 'Z',
    xyz_label: result.risk_level === 'DÜŞÜK' ? 'Düşük Risk' : result.risk_level === 'ORTA' ? 'Orta Risk' : 'Yüksek Risk',
    forecast_model: 'n/a',
    forecast_model_label: 'Tedarikçi',
    seasonality: false,
    seasonality_label: 'Yok',
    seasonality_strength: 0,
    trend_direction: result.performance_level === 'İYİ' ? 'Artış' : 'Azalış',
    trend_percent: 0,
    lead_time_days: result.lt_mean || 14,
    zero_ratio: 0,
    risk_score: result.risk_score || 0,
    risk_level: result.risk_level || 'Düşük',
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


export default function SupplierPage() {
  const { user, fetchUser } = useAuth();
  const [hasSupplierData, setHasSupplierData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [suppliers, setSuppliers] = useState<SupplierResult[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
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
    '/api/supplier/batch',
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
    { label: 'Tedarikçi verileri hazırlanıyor...', description: 'Tedarikçi bilgileri işleniyor', status: 'pending' },
    { label: 'Performans analizi yapılıyor...', description: 'Teslimat ve kalite metrikleri hesaplanıyor', status: 'pending' },
    { label: 'Risk analizi yapılıyor...', description: 'Risk skorları ve seviyeleri belirleniyor', status: 'pending' },
    { label: 'Pay optimizasyonu yapılıyor...', description: 'Optimum tedarikçi payları hesaplanıyor', status: 'pending' },
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
    checkSupplierData();
  }, []);

  const checkSupplierData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/supplier/check');
      const hasData = res.data.has_suppliers === true;
      setHasSupplierData(hasData);
      setMaterialCount(res.data.material_count || 0);
      if (!hasData) {
        setError('Tedarikçi verisi bulunamadı. Lütfen Excel\'e "Tedarikciler" ve "Malzeme_Tedarikciler" sheet\'lerini ekleyin.');
      }
    } catch (error) {
      console.error('❌ Tedarikçi veri kontrolü hatası:', error);
      setHasSupplierData(false);
      setError('Veri kontrolü sırasında hata oluştu.');
    } finally {
      setIsCheckingData(false);
    }
  };


  const handleFetchAndLoad = (id: number) => {
    fetchAndLoadResult(id, setSuppliers, setPage, setSuccess, setError, setLoading);
  };

  useEffect(() => {
    checkAndLoadAnalysis('supplier', handleFetchAndLoad);
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

  const generateSummary = (suppliersData: SupplierResult[]) => {
    if (!suppliersData || suppliersData.length === 0) return null;

    const total = suppliersData.length;
    const avgRisk = suppliersData.reduce((acc, s) => acc + (s.risk_score || 0), 0) / total;
    const avgPerf = suppliersData.reduce((acc, s) => acc + (s.performance_score || 0), 0) / total;
    const avgOntime = suppliersData.reduce((acc, s) => acc + (s.ontime_rate || 0), 0) / total;
    const highRiskCount = suppliersData.filter(s => s.risk_level === 'YÜKSEK' || s.risk_score > 0.7).length;
    const lowRiskCount = suppliersData.filter(s => s.risk_level === 'DÜŞÜK' || s.risk_score < 0.3).length;

    const sorted = [...suppliersData].sort((a, b) => b.performance_score - a.performance_score);
    const topSupplier = sorted[0]?.name || '-';
    const topSupplierScore = sorted[0]?.performance_score || 0;

    return {
      totalSuppliers: total,
      avgRiskScore: avgRisk,
      avgPerformanceScore: avgPerf,
      avgOntimeRate: avgOntime,
      highRiskCount: highRiskCount,
      lowRiskCount: lowRiskCount,
      topSupplier: topSupplier,
      topSupplierScore: topSupplierScore,
    };
  };

  const generateAIComment = (summary: AnalysisSummary) => {
    if (!summary) return null;

    let riskText = '';
    if (summary.avgRiskScore > 0.6) {
      riskText = `Ortalama risk skoru ${summary.avgRiskScore.toFixed(2)} ile yüksek seviyede. ${summary.highRiskCount} tedarikçi yüksek risk taşıyor. Tedarik zinciri riskleri değerlendirilmeli.`;
    } else if (summary.avgRiskScore > 0.3) {
      riskText = `Ortalama risk skoru ${summary.avgRiskScore.toFixed(2)} ile orta seviyede. ${summary.highRiskCount} tedarikçi risk altında. Risk yönetimi önerilir.`;
    } else {
      riskText = `Ortalama risk skoru ${summary.avgRiskScore.toFixed(2)} ile düşük seviyede. ${summary.lowRiskCount} tedarikçi düşük riskli.`;
    }

    let performanceText = '';
    if (summary.avgPerformanceScore > 0.7) {
      performanceText = `Ortalama performans skoru ${summary.avgPerformanceScore.toFixed(2)} ile iyi seviyede. En iyi tedarikçi: "${summary.topSupplier}" (${(summary.topSupplierScore * 100).toFixed(0)}%).`;
    } else if (summary.avgPerformanceScore > 0.4) {
      performanceText = `Ortalama performans skoru ${summary.avgPerformanceScore.toFixed(2)} ile orta seviyede. İyileştirme fırsatları mevcut.`;
    } else {
      performanceText = `Ortalama performans skoru ${summary.avgPerformanceScore.toFixed(2)} ile düşük seviyede. Tedarikçi performansı iyileştirilmeli.`;
    }

    let recommendationText = '';
    if (summary.highRiskCount > summary.totalSuppliers * 0.3) {
      recommendationText = `${summary.highRiskCount} tedarikçi yüksek riskli. Alternatif tedarikçi geliştirme stratejisi önerilir.`;
    } else if (summary.avgOntimeRate < 85) {
      recommendationText = `Ortalama zamanında teslimat oranı %${summary.avgOntimeRate.toFixed(0)}. Teslimat performansı iyileştirilmeli.`;
    } else {
      recommendationText = `Tedarikçi performansı genel olarak iyi. ${summary.lowRiskCount} tedarikçi düşük riskli.`;
    }

    let confidenceText = '';
    if (summary.totalSuppliers > 10 && summary.avgOntimeRate > 80) {
      confidenceText = 'Geniş veri seti ve iyi teslimat oranı ile analiz güvenilir.';
    } else if (summary.totalSuppliers > 5) {
      confidenceText = 'Veri seti yeterli, analiz güvenilir.';
    } else {
      confidenceText = 'Tedarikçi sayısı sınırlı, sonuçlar dikkatle değerlendirilmeli.';
    }

    return {
      summary: `${summary.totalSuppliers} tedarikçi analiz edildi. Ortalama risk: ${summary.avgRiskScore.toFixed(2)}, ortalama performans: ${summary.avgPerformanceScore.toFixed(2)}.`,
      risk: riskText,
      performance: performanceText,
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
      
      updateStep(1, 'active', 'Tedarikçi verileri işleniyor...');
      await sleep(800);
      updateStep(1, 'completed', 'Tedarikçi verileri hazırlandı');
      setProgress(30);
      
      updateStep(2, 'active', 'Performans analizi yapılıyor...');
      await sleep(1000);
      updateStep(2, 'completed', 'Performans metrikleri hesaplandı');
      setProgress(50);
      
      updateStep(3, 'active', 'Risk analizi yapılıyor...');
      await sleep(800);
      updateStep(3, 'completed', 'Risk skorları belirlendi');
      setProgress(65);
      
      updateStep(4, 'active', 'Pay optimizasyonu yapılıyor...');
      const response = await supplierMutation.mutateAsync();
      updateStep(4, 'completed', `${response.total_suppliers || 0} tedarikçi optimize edildi`);
      setProgress(85);
      
      if (response.suppliers) {
        const summary = generateSummary(response.suppliers);
        setAnalysisSummary(summary);
        if (summary) {
          const comment = generateAIComment(summary);
          setAiComment(comment);
        }
      }
      
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
      
      const response = await asyncSupplierMutation.mutateAsync();
      
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

  // 📌 SENKRON Tedarikçi Analizi
  const supplierMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Tedarikçi analizi başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/supplier/batch', {});
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setSuppliers(data.suppliers || []);
        setRecommendations(data.recommendations || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total_suppliers || 0} tedarikçi başarıyla analiz edildi.`);
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
        setError(data.error || 'Tedarikçi analizi başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Tedarikçi analizi hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Tedarikçi Analizi
  const asyncSupplierMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/supplier/batch/async', {});
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
          setSuppliers(resultsRes.data.suppliers || []);
          setRecommendations(resultsRes.data.recommendations || []);
          setPage(0);
          setSuccess(`${resultsRes.data.total_suppliers || 0} tedarikçi başarıyla analiz edildi.`);
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
          result_type: 'supplier_batch', 
          limit: 10000 
        }
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        const batchResults = rawResults.filter((item: any) => item.is_batch === true);
        
        const historyItems = batchResults.map((item: any) => {
          const data = item.data || {};
          const totalSuppliers = item.total_materials || data.total_suppliers || 0;
          
          const suppliersData = data?.suppliers || [];
          let highRiskCount = 0;
          let lowRiskCount = 0;
          let topSupplier = '-';
          let topSupplierScore = 0;
          
          if (suppliersData.length > 0) {
            suppliersData.forEach((s: any) => {
              if (s.risk_level === 'YÜKSEK') highRiskCount++;
              if (s.risk_level === 'DÜŞÜK') lowRiskCount++;
            });
            
            const sorted = [...suppliersData].sort((a, b) => (b.performance_score || 0) - (a.performance_score || 0));
            if (sorted.length > 0) {
              topSupplier = sorted[0]?.name || '-';
              topSupplierScore = sorted[0]?.performance_score || 0;
            }
          }
          
          const reportName = `Tedarikçi Analizi (${totalSuppliers} Tedarikçi) - ${lowRiskCount} Düşük Risk, ${highRiskCount} Yüksek Risk - En İyi: ${topSupplier}`;
          
          return {
            id: item.id,
            created_at: item.created_at,
            data: {
              total: totalSuppliers,
              suppliers: suppliersData,
              recommendations: data?.recommendations || [],
              report_name: reportName,
              status: item.status || 'completed',
              high_risk_count: highRiskCount,
              low_risk_count: lowRiskCount,
              top_supplier: topSupplier,
              top_supplier_score: topSupplierScore,
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
    const historySuppliers = item.data?.suppliers || [];
    if (historySuppliers.length > 0) {
      setSuppliers(historySuppliers);
      setRecommendations(item.data?.recommendations || []);
      setPage(0);
      setHistoryDialogOpen(false);
      setSuccess(`${historySuppliers.length} tedarikçi geçmiş sonuçları yüklendi.`);
      setTimeout(() => setSuccess(null), 3000);
      
      const summary = generateSummary(historySuppliers);
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
    if (suppliers.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }
    try {
      const response = await api.post('/api/export/supplier-results', {
        suppliers: suppliers,
        recommendations: recommendations
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tedarikci_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const paginatedSuppliers = suppliers.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getRiskColor = (riskLevel: string) => {
    switch(riskLevel) {
      case 'DÜŞÜK': return 'success';
      case 'ORTA': return 'warning';
      case 'YÜKSEK': return 'error';
      default: return 'default';
    }
  };

  const getPerformanceColor = (perfLevel: string) => {
    switch(perfLevel) {
      case 'İYİ': return 'success';
      case 'ORTA': return 'warning';
      case 'KÖTÜ': return 'error';
      default: return 'default';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch(riskLevel) {
      case 'DÜŞÜK': return <CheckCircle fontSize="small" />;
      case 'ORTA': return <Warning fontSize="small" />;
      case 'YÜKSEK': return <Error fontSize="small" />;
      default: return <Info fontSize="small" />;
    }
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
              <LocalShipping sx={{ fontSize: 24, color: '#1f4e79' }} />
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.3rem' }}>
                Tedarikçi Analizi
              </Typography>
              <Chip label="Supplier" size="small" sx={{ height: 20, fontSize: '0.55rem', bgcolor: '#1f4e79', color: 'white' }} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
              Tedarikçi performansını, risklerini ve optimum pay dağılımını analiz eder.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5, mt: { xs: 1.5, md: 0 }, flexWrap: 'wrap' }}>
            <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label="Risk analizi" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<AutoAwesome sx={{ fontSize: 14 }} />} label="Performans" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Speed sx={{ fontSize: 14 }} />} label="Optimizasyon" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
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
              {suppliers.length || 0}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Tedarikçi</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Security sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.avgRiskScore.toFixed(2) : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Ortalama Risk</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <ShowChart sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? (summary.avgOntimeRate * 100).toFixed(0) + '%' : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Teslimat Oranı</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AttachMoney sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.totalSuppliers : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Toplam Tedarikçi</Typography>
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
                ⚠️ {aiComment.risk}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c' }}>
                📈 {aiComment.performance}
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
          severity={error.includes('Tedarikçi') ? 'warning' : 'error'} 
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
                ) : hasSupplierData ? (
                  <CloudDone sx={{ fontSize: 20, color: '#2e7d32' }} />
                ) : (
                  <CloudOff sx={{ fontSize: 20, color: '#d32f2f' }} />
                )}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  Veri Durumu
                </Typography>
                <Chip
                  label={isCheckingData ? 'Kontrol ediliyor...' : hasSupplierData ? '✅ Yüklü' : '❌ Yüklenmemiş'}
                  size="small"
                  color={hasSupplierData ? 'success' : 'error'}
                  sx={{ height: 20, fontSize: '0.55rem' }}
                />
              </Box>
              {hasSupplierData && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                  {materialCount} malzeme ile ilişkili tedarikçi
                </Typography>
              )}
              {!hasSupplierData && !isCheckingData && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem' }}>
                  Lütfen Excel'e tedarikçi verilerini ekleyin
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
                    Analiz başlatmak için butonlardan birine tıklayın
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

        {/* ✅ SAĞ SÜTUN - Butonlar ve Analiz Özeti */}
        <Grid size={{ xs: 12, md: 7 }}>
          {/* ✅ Butonlar */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Button
                  variant="contained"
                  size="medium"
                  startIcon={supplierMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAnalysis}
                  disabled={supplierMutation.isPending || !hasSupplierData || isProcessing}
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
                  {supplierMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
                </Button>

                <Button
                  variant="contained"
                  size="medium"
                  color="secondary"
                  startIcon={asyncSupplierMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAsyncAnalysis}
                  disabled={asyncSupplierMutation.isPending || !hasSupplierData || isProcessing}
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
                  {asyncSupplierMutation.isPending ? 'Başlatılıyor...' : 'Arka Planda Çalıştır'}
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

          {/* ✅ Analiz Özeti (varsa) */}
          {analysisSummary && (
            <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#e8f5e9', border: '1px solid #a5d6a7' }}>
              <CardContent sx={{ py: 1.5, px: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CheckCircle sx={{ fontSize: 18, color: '#2e7d32' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2e7d32', fontSize: '0.8rem' }}>
                    Tedarikçi Özeti
                  </Typography>
                </Box>
                <Grid container spacing={1}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      <strong>{analysisSummary.totalSuppliers}</strong> tedarikçi analiz edildi
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Ortalama risk: <strong>{analysisSummary.avgRiskScore.toFixed(2)}</strong>
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Yüksek risk: <strong>{analysisSummary.highRiskCount}</strong> tedarikçi
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      En iyi tedarikçi: <strong>{analysisSummary.topSupplier}</strong>
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* ✅ Tavsiyeler */}
          {recommendations.length > 0 && (
            <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#e3f2fd', border: '1px solid #90caf9' }}>
              <CardContent sx={{ py: 1.5, px: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Lightbulb sx={{ fontSize: 18, color: '#0d47a1' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.8rem' }}>
                    💡 Tavsiyeler
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  {recommendations.map((rec, idx) => (
                    <Typography key={idx} variant="body2" sx={{ fontSize: '0.7rem', color: '#374151', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#0d47a1', display: 'inline-block' }} />
                      {rec}
                    </Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* ✅ Bilgilendirme Kartı */}
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: 'info.light', border: '1px solid #90caf9' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0d47a1', fontSize: '0.8rem' }}>
              📊 Tedarikçi Analizi Metrikleri
            </Typography>
          </Box>
          <Grid container spacing={1.5}>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.65rem', color: '#0d47a1' }}>
                🎯 Risk Skoru
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                0-1 arası, 1 en riskli
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.65rem', color: '#0d47a1' }}>
                📈 Performans Skoru
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                0-1 arası, 1 en iyi
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.65rem', color: '#0d47a1' }}>
                ⏱ Zamanında Teslimat
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                Yüzde olarak teslimat başarısı
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.65rem', color: '#0d47a1' }}>
                📦 Lead Time
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                Ortalama teslimat süresi (gün)
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
        </Box>
      )}

      {/* Sonuçlar */}
      {suppliers.length > 0 && (
        <Card>
          <CardContent sx={{ py: 1.5, px: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                📊 Tedarikçiler ({suppliers.length})
              </Typography>
              <Button variant="outlined" size="small" startIcon={<Download sx={{ fontSize: 16 }} />} onClick={handleExport} sx={{ fontSize: '0.65rem', textTransform: 'none' }}>
                Excel
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f0f7ff' }}>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Tedarikçi</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Risk</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Performans</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Zamanında %</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">LT (gün)</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Pay %</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Tavsiye</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedSuppliers.map((supplier) => (
                    <TableRow key={supplier.supplier_id} hover sx={{ '&:hover': { bgcolor: '#f8faff' } }}>
                      <TableCell sx={{ fontSize: '0.7rem' }}>
                        <Typography variant="body2" sx={{ fontWeight: 'medium', fontSize: '0.7rem' }}>
                          {supplier.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                          {supplier.supplier_id}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem' }}>
                        <Tooltip title={`Risk Skoru: ${supplier.risk_score.toFixed(2)}`} arrow>
                          <Chip
                            icon={getRiskIcon(supplier.risk_level)}
                            label={supplier.risk_level}
                            size="small"
                            color={getRiskColor(supplier.risk_level)}
                            sx={{ height: 20, fontSize: '0.55rem' }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem' }}>
                        <Tooltip title={`Performans Skoru: ${supplier.performance_score.toFixed(2)}`} arrow>
                          <Chip
                            label={supplier.performance_level}
                            size="small"
                            color={getPerformanceColor(supplier.performance_level)}
                            sx={{ height: 20, fontSize: '0.55rem' }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem' }}>
                        {supplier.ontime_rate}%
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem' }}>
                        {supplier.lt_mean} ± {supplier.lt_std}
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem' }}>
                        {(supplier.total_share * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem' }}>
                        <Tooltip title={supplier.recommendation} arrow>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              cursor: 'pointer',
                              display: 'block',
                              maxWidth: 250,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              fontSize: '0.65rem'
                            }}
                          >
                            {supplier.recommendation}
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
                count={suppliers.length}
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
      )}

      {/* Boş Durum */}
      {!isProcessing && suppliers.length === 0 && !error && hasSupplierData && !isCheckingData && (
        <Card sx={{ borderRadius: 2, border: '1px dashed #e0e0e0', bgcolor: '#fafcff' }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <LocalShipping sx={{ fontSize: 40, color: '#b0b0b0', mb: 1 }} />
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
              Henüz analiz yapılmadı
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              "Analiz Et" veya "Arka Planda Çalıştır" butonuna tıklayın
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
                      📦 Tedarikçi Sayısı
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
                          {item.data?.report_name || 'Tedarikçi Analizi'}
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