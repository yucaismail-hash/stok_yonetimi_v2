// frontend/src/pages/SafetyStockPage.tsx
// Stokonomi Design System v1.0 - Emniyet Stoğu Sayfası
// ✅ Tüm UI iyileştirmeleri uygulandı - Backend mantığı değiştirilmedi

import { useState, useEffect, useCallback } from 'react';
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
  Snackbar,
  Tooltip,
  Slider,
  LinearProgress,
  Stack,
  Avatar,
  alpha,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Skeleton,
} from '@mui/material';
import {
  Security,
  Send,
  Download,
  History,
  Close,
  Visibility,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  Speed,
  Analytics,
  BarChart,
  Inventory,
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Lightbulb,
  Psychology,
  AutoAwesome,
  Timeline,
  ExpandMore,
  Category,
  Assessment,
  Warning,
  AccountBalanceWallet,
  UploadFile,
  Refresh,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { usePricingPreview } from '../hooks/usePricing';
import { useLearningScore } from '../hooks/useLearningScore';

// ✅ Design System Component'leri
import {
  PageLayout,
  Hero,
  KpiCard,
  AIAssistantCard,
  ProcessFlowCard,
  SectionHeader,
  StandardTable,
  AIRecommendationBadge,
  type ProcessStep,
  type TableColumn,
  type AIRecommendationType,
} from '../components/common';

// ✅ Bileşenler
import DecisionReasoning from '../components/Results/DecisionReasoning';
import TechnicalAnalysisDetail from '../components/Results/TechnicalAnalysisDetail';
import LearningScoreBadge from '../components/Dashboard/LearningScoreBadge';

// ============================================================
// 📌 INTERFACES
// ============================================================

interface SafetyStockResult {
  material_code: string;
  group: string;
  lead_time_days: number;
  pattern: string;
  pattern_label: string;
  pattern_color: string;
  cv: number;
  zero_ratio: number;
  trend_direction?: string;
  trend_percent?: number;
  classic_ss: number;
  croston_ss: number;
  syntetos_boylan_ss: number;
  bootstrapping_ss: number;
  ml_ss: number;
  hybrid_ss: number;
  recommended_method: string;
  recommended_method_label: string;
  recommended_value: number;
  recommended_rop?: number;
  abc?: string;
  abc_label?: string;
  abc_color?: string;
  xyz?: string;
  xyz_label?: string;
  xyz_color?: string;
  has_seasonality?: boolean;
  seasonality_strength?: number;
  seasonality_label?: string;
  is_intermittent?: boolean;
  intermittent_level?: string;
  forecast_model?: string;
  forecast_model_label?: string;
  risk_score?: number;
  risk_level?: string;
  ai_comment?: string;
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
  ai_summary?: any;
  data: any;
}

interface AnalysisSummary {
  totalMaterials: number;
  mostUsedMethod: string;
  mostUsedMethodPercent: number;
  avgServiceLevel: number;
  totalRecommendedSS: number;
  patternDistribution: Record<string, number>;
  abcDistribution?: Record<string, number>;
  xyzDistribution?: Record<string, number>;
  avgRiskScore?: number;
  highRiskCount?: number;
  intermittentCount?: number;
  seasonalCount?: number;
  increaseCount?: number;
  decreaseCount?: number;
  maintainCount?: number;
}

// ============================================================
// 📌 METHOD TANIMLARI
// ============================================================

const methodLabelsFull: Record<string, string> = {
  classic_ss: 'Klasik',
  croston_ss: 'Croston',
  syntetos_boylan_ss: 'SB Croston',
  bootstrapping_ss: 'Bootstrap',
  ml_ss: 'ML',
  hybrid_ss: 'Hibrit',
};

const methodColors: Record<string, string> = {
  classic_ss: '#1976d2',
  croston_ss: '#2e7d32',
  syntetos_boylan_ss: '#ed6c02',
  bootstrapping_ss: '#9c27b0',
  ml_ss: '#d32f2f',
  hybrid_ss: '#1f4e79',
};

// ============================================================
// 📌 YAŞAM DÖNGÜSÜ ADIMLARI
// ============================================================

const LIFECYCLE_STEPS: ProcessStep[] = [
  { label: 'Dataset doğrulanıyor', description: 'Veri kaynağı kontrol ediliyor', status: 'pending' },
  { label: 'Son analiz yükleniyor', description: 'Geçmiş analiz sonuçları okunuyor', status: 'pending' },
  { label: 'Learning Memory okunuyor', description: 'Şirket hafızası yükleniyor', status: 'pending' },
  { label: 'KPI hazırlanıyor', description: 'Performans metrikleri hesaplanıyor', status: 'pending' },
  { label: 'AI hazırlanıyor', description: 'Yapay zeka önerileri hazırlanıyor', status: 'pending' },
  { label: 'Sayfa hazır', description: 'Tüm veriler yüklendi', status: 'pending' },
];

const ANALYSIS_STEPS: ProcessStep[] = [
  { label: 'Veri okunuyor', description: 'Excel dosyası kontrol ediliyor', status: 'pending' },
  { label: 'Pattern Analizi', description: 'Talep desenleri belirleniyor', status: 'pending' },
  { label: 'ABC XYZ', description: 'Maliyet ve talep sınıflandırması', status: 'pending' },
  { label: '6 Model Hesaplanıyor', description: 'Emniyet stoğu hesaplamaları', status: 'pending' },
  { label: 'AI Analizi', description: 'Risk skoru ve öneriler oluşturuluyor', status: 'pending' },
  { label: 'Learning Engine', description: 'Şirket hafızası güncelleniyor', status: 'pending' },
  { label: 'Excel hazırlanıyor', description: 'Rapor dosyası oluşturuluyor', status: 'pending' },
  { label: 'Tamamlandı', description: 'Analiz başarıyla tamamlandı', status: 'pending' },
];

// ============================================================
// 📌 YARDIMCI BİLEŞENLER
// ============================================================

const AIReasoningSection = ({ result }: { result: SafetyStockResult }) => {
  const aiDecision = result.ai_decision;
  if (!aiDecision) return null;

  const reasoning = {
    recommended_ss: result.hybrid_ss || result.recommended_value || 0,
    current_ss: result.classic_ss || 0,
    reasons: aiDecision.reasons || [
      (result.cv || 0) > 0.7 ? 'CV yüksek' : '',
      (result.lead_time_days || 0) > 21 ? 'Lead Time uzun' : '',
      result.is_intermittent ? 'Düzensiz talep' : '',
      result.has_seasonality ? 'Mevsimsel talep' : '',
      (result.risk_score || 0) > 0.5 ? 'Risk skoru yüksek' : '',
    ].filter(Boolean),
    conclusion: aiDecision.decision === 'increase_safety_stock' 
      ? 'Syntetos-Boylan önerildi.' 
      : aiDecision.decision === 'maintain_current'
      ? 'Mevcut politika yeterli.'
      : 'Detaylı analiz önerilir.',
    confidence: aiDecision.confidence || 0.5,
    factors: {
      cv: result.cv || 0,
      lead_time: result.lead_time_days || 14,
      intermittent: result.is_intermittent || false,
      seasonal: result.has_seasonality || false,
      risk_score: result.risk_score || 0,
      pattern: result.pattern_label || 'DEGISKEN',
    }
  };

  return (
    <Box sx={{ mt: 1 }}>
      <DecisionReasoning materialCode={result.material_code} reasoning={reasoning} />
    </Box>
  );
};

const TechnicalAnalysisSection = ({ result }: { result: SafetyStockResult }) => {
  const [expanded, setExpanded] = useState(false);

  const technicalData = {
    material_code: result.material_code,
    cv: result.cv || 0,
    pattern: result.pattern || 'DEGISKEN',
    pattern_label: result.pattern_label || 'Değişken',
    pattern_color: result.pattern_color || 'default',
    abc: result.abc || 'C',
    abc_label: result.abc_label || 'Düşük Maliyetli',
    xyz: result.xyz || 'Z',
    xyz_label: result.xyz_label || 'Düzensiz Talep',
    forecast_model: result.forecast_model || 'auto',
    forecast_model_label: result.forecast_model_label || 'Otomatik',
    seasonality: result.has_seasonality || false,
    seasonality_label: result.seasonality_label || 'Yok',
    seasonality_strength: result.seasonality_strength || 0,
    trend_direction: result.trend_direction || 'Yok',
    trend_percent: result.trend_percent || 0,
    lead_time_days: result.lead_time_days || 14,
    zero_ratio: result.zero_ratio || 0,
    risk_score: result.risk_score || 0,
    risk_level: result.risk_level || 'Düşük',
  };

  return (
    <Accordion 
      expanded={expanded} 
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 1, '&:before': { display: 'none' }, border: '1px solid #e8f0fe', borderRadius: 1 }}
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
// 📌 SAĞ PANEL
// ============================================================

const RightPanel = ({
  datasetName,
  productCount,
  learningLevel,
  learningScore,
  aiReady,
  lifecycleSteps,
  lifecycleActiveStep,
  isLifecycleComplete,
  analysisSteps,
  analysisActiveStep,
  isAnalysisComplete,
  isProcessing,
  progress,
  progressLabel,
}: {
  datasetName: string;
  productCount: number;
  learningLevel: string;
  learningScore: number;
  aiReady: boolean;
  lifecycleSteps: ProcessStep[];
  lifecycleActiveStep: number;
  isLifecycleComplete: boolean;
  analysisSteps: ProcessStep[];
  analysisActiveStep: number;
  isAnalysisComplete: boolean;
  isProcessing: boolean;
  progress: number;
  progressLabel: string;
}) => {
  const currentSteps = isProcessing ? analysisSteps : lifecycleSteps;
  const currentActiveStep = isProcessing ? analysisActiveStep : lifecycleActiveStep;
  const isComplete = isProcessing ? isAnalysisComplete : isLifecycleComplete;
  const title = isProcessing ? 'Analiz Süreci' : 'Sayfa Yaşam Döngüsü';

  return (
    <Paper sx={{ p: 1, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#fafcff', height: '100%' }}>
      <ProcessFlowCard
        steps={currentSteps}
        activeStep={currentActiveStep}
        isComplete={isComplete}
        title={title}
        compact
        progress={progress}
        progressLabel={progressLabel}
      />
    </Paper>
  );
};

// ============================================================
// 📌 ANA SAYFA
// ============================================================

export default function SafetyStockPage() {
  const { user, fetchUser } = useAuth();
  
  // State'ler
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [results, setResults] = useState<SafetyStockResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [materialCount, setMaterialCount] = useState(0);
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null);
  const [selectedReasoning, setSelectedReasoning] = useState<SafetyStockResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);
  const { data: learningScoreData } = useLearningScore();
  const [serviceLevel, setServiceLevel] = useState<number>(0.95);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const learningComponents = learningScoreData?.components || {};

  // Lifecycle
  const [lifecycleSteps, setLifecycleSteps] = useState<ProcessStep[]>(LIFECYCLE_STEPS);
  const [lifecycleActiveStep, setLifecycleActiveStep] = useState(-1);
  const [isLifecycleComplete, setIsLifecycleComplete] = useState(false);

  // Analysis
  const [analysisSteps, setAnalysisSteps] = useState<ProcessStep[]>(ANALYSIS_STEPS);
  const [analysisActiveStep, setAnalysisActiveStep] = useState(-1);
  const [isAnalysisComplete, setIsAnalysisComplete] = useState(false);

  // Async için ayrı state
  const [asyncSteps, setAsyncSteps] = useState<ProcessStep[]>([
    { label: 'Analiz başlatılıyor...', description: 'Veriler işleniyor', status: 'pending' },
    { label: 'Görev oluşturuluyor...', description: 'Arka plan işlemi başlatılıyor', status: 'pending' },
    { label: 'Görevlere eklendi ✓', description: 'İlerlemeyi ASYNC Görevler sayfasından takip edin', status: 'pending' },
  ]);
  const [asyncActiveStep, setAsyncActiveStep] = useState(-1);
  const [isAsyncComplete, setIsAsyncComplete] = useState(false);

  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });

  const [activeDatasetId, setActiveDatasetId] = useState<number | null>(() => {
    const saved = localStorage.getItem('activeDatasetId');
    return saved ? parseInt(saved) : null;
  });

  const { data: pricingPreview, isLoading: pricingLoading } = usePricingPreview(
    '/api/safety-stock/batch',
    activeDatasetId || undefined
  );

  // ============================================================
  // 📌 EXPORT
  // ============================================================

  const handleExport = async () => {
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }

    setLoading(true);
    try {
      const exportData = {
        results: results,
        learning_rules: [],
        executive_summary: analysisSummary ? {
          totalProducts: analysisSummary.totalMaterials,
          totalSS: analysisSummary.totalRecommendedSS,
          highRiskCount: analysisSummary.highRiskCount,
          avgRisk: analysisSummary.avgRiskScore,
          mostUsedMethod: analysisSummary.mostUsedMethod,
          avgServiceLevel: analysisSummary.avgServiceLevel,
          increaseCount: analysisSummary.increaseCount || 0,
          decreaseCount: analysisSummary.decreaseCount || 0,
          maintainCount: analysisSummary.maintainCount || 0,
        } : null
      };

      const response = await api.post(
        '/api/export/safety-stock-results',
        exportData,
        { 
          responseType: 'blob',
          timeout: 60000,
        }
      );

      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `safety_stock_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess('Excel dosyası başarıyla indirildi.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('❌ Excel export hatası:', err);
      setError(`Excel dosyası oluşturulamadı: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // 📌 GENERATE SUMMARY
  // ============================================================

  const generateSummary = useCallback((resultsData: SafetyStockResult[]) => {
    if (!resultsData || resultsData.length === 0) return null;

    const methodCount: Record<string, number> = {};
    const patternDist: Record<string, number> = {};
    const abcDist: Record<string, number> = {};
    const xyzDist: Record<string, number> = {};
    
    let totalSS = 0;
    let highRiskCount = 0;
    let intermittentCount = 0;
    let seasonalCount = 0;
    let riskSum = 0;
    let increaseCount = 0;
    let decreaseCount = 0;
    let maintainCount = 0;

    resultsData.forEach(r => {
      const method = r.recommended_method || 'hybrid_ss';
      methodCount[method] = (methodCount[method] || 0) + 1;
      
      const pattern = r.pattern || 'DEGISKEN';
      patternDist[pattern] = (patternDist[pattern] || 0) + 1;
      
      const abc = r.abc || 'C';
      abcDist[abc] = (abcDist[abc] || 0) + 1;
      
      const xyz = r.xyz || 'Z';
      xyzDist[xyz] = (xyzDist[xyz] || 0) + 1;
      
      if (r.hybrid_ss) totalSS += r.hybrid_ss;
      
      const riskScore = r.risk_score || 0;
      riskSum += riskScore;
      if (riskScore > 0.5) highRiskCount++;
      
      if (r.is_intermittent) intermittentCount++;
      if (r.has_seasonality) seasonalCount++;

      const decision = r.ai_decision?.decision || '';
      if (decision === 'increase_safety_stock') increaseCount++;
      else if (decision === 'decrease_safety_stock') decreaseCount++;
      else if (decision === 'maintain_current') maintainCount++;
    });

    const sortedMethods = Object.entries(methodCount).sort((a, b) => b[1] - a[1]);
    const mostUsed = sortedMethods[0] || ['hybrid_ss', 0];
    const mostUsedPercent = resultsData.length > 0 ? (mostUsed[1] / resultsData.length) * 100 : 0;

    return {
      totalMaterials: resultsData.length,
      mostUsedMethod: mostUsed[0],
      mostUsedMethodPercent: mostUsedPercent,
      avgServiceLevel: serviceLevel * 100,
      totalRecommendedSS: Math.round(totalSS),
      patternDistribution: patternDist,
      abcDistribution: abcDist,
      xyzDistribution: xyzDist,
      avgRiskScore: riskSum / resultsData.length,
      highRiskCount: highRiskCount,
      intermittentCount: intermittentCount,
      seasonalCount: seasonalCount,
      increaseCount: increaseCount,
      decreaseCount: decreaseCount,
      maintainCount: maintainCount,
    };
  }, [serviceLevel]);

  // ============================================================
  // 📌 LIFECYCLE
  // ============================================================

  const updateLifecycleStep = useCallback((index: number, status: ProcessStep['status']) => {
    setLifecycleSteps(prev => prev.map((step, i) => {
      if (i === index) {
        return {
          ...step,
          status,
          timestamp: status === 'completed' || status === 'active' ? new Date().toLocaleTimeString() : undefined,
        };
      }
      return step;
    }));
    setLifecycleActiveStep(index);
  }, []);

  const runLifecycle = useCallback(async () => {
    const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    updateLifecycleStep(0, 'active');
    await sleep(200);
    updateLifecycleStep(0, 'completed');
    setProgress(15);

    updateLifecycleStep(1, 'active');
    await sleep(300);
    updateLifecycleStep(1, 'completed');
    setProgress(30);

    updateLifecycleStep(2, 'active');
    await sleep(200);
    updateLifecycleStep(2, 'completed');
    setProgress(50);

    updateLifecycleStep(3, 'active');
    await sleep(200);
    updateLifecycleStep(3, 'completed');
    setProgress(70);

    updateLifecycleStep(4, 'active');
    await sleep(200);
    updateLifecycleStep(4, 'completed');
    setProgress(85);

    updateLifecycleStep(5, 'active');
    await sleep(200);
    updateLifecycleStep(5, 'completed');
    setProgress(100);
    setIsLifecycleComplete(true);
    setProgressLabel('Hazır');
  }, [updateLifecycleStep]);

  const completeLifecycle = useCallback(() => {
    setLifecycleSteps(prev => prev.map((step, i) => ({
      ...step,
      status: i === 5 ? 'completed' : step.status,
      timestamp: i === 5 ? new Date().toLocaleTimeString() : step.timestamp,
    })));
    setIsLifecycleComplete(true);
    setProgress(100);
    setProgressLabel('Hazır');
  }, []);

  // ============================================================
  // 📌 CHECK UPLOADED DATA
  // ============================================================

  const checkUploadedData = useCallback(async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/upload/status');
      const hasData = res.data.has_data === true;
      setHasUploadedData(hasData);
      setMaterialCount(res.data.materials_count || 0);
      if (!hasData) {
        setError('Henüz Excel dosyası yüklenmemiş.');
      }
    } catch (error) {
      console.error('❌ Veri kontrolü hatası:', error);
      setHasUploadedData(false);
    } finally {
      setIsCheckingData(false);
    }
  }, []);

  // ============================================================
  // 📌 LOAD RESULTS
  // ============================================================

  const loadResults = useCallback(async () => {
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'safety_stock_batch', limit: 1 }
      });
      
      if (res.data.success && res.data.results && res.data.results.length > 0) {
        const latest = res.data.results[0];
        
        let aiSummaryData = null;
        if (latest.ai_summary) {
          aiSummaryData = latest.ai_summary;
        } else if (latest.data?.ai_summary) {
          aiSummaryData = latest.data.ai_summary;
        } else if (latest.result?.ai_summary) {
          aiSummaryData = latest.result.ai_summary;
        } else if (latest._ai_summary) {
          aiSummaryData = latest._ai_summary;
        } else if (latest.summary && typeof latest.summary === 'object') {
          aiSummaryData = latest.summary;
        }
        
        if (aiSummaryData) {
          setAiSummary(aiSummaryData);
        } else {
          setAiSummary(null);
        }
        
        const data = latest.data || {};
        const resultsData = data.results || [];
        
        if (resultsData.length > 0) {
          setResults(resultsData);
          setPage(0);
          setShowResults(true);
          const summary = generateSummary(resultsData);
          setAnalysisSummary(summary);
          setSuccess(`${resultsData.length} malzeme yüklendi.`);
          return true;
        }
      }
      setShowResults(false);
      return false;
    } catch (error) {
      console.error('❌ Veri yükleme hatası:', error);
      setShowResults(false);
      return false;
    }
  }, [generateSummary]);

  // ============================================================
  // 📌 EFFECTS
  // ============================================================

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
    const init = async () => {
      setIsDataLoading(true);
      await runLifecycle();
      await checkUploadedData();
      
      const loadAnalysisId = sessionStorage.getItem('loadAnalysisId');
      const loadAnalysisType = sessionStorage.getItem('loadAnalysisType');
      
      if (loadAnalysisId && loadAnalysisType === 'safety_stock_batch') {
        try {
          const resultRes = await api.get(`/api/upload/results/${loadAnalysisId}`);
          if (resultRes.data.success && resultRes.data.result) {
            const result = resultRes.data.result;
            const data = result.data || {};
            const resultsData = data.results || [];
            
            if (resultsData.length > 0) {
              setResults(resultsData);
              setPage(0);
              setShowResults(true);
              const summary = generateSummary(resultsData);
              setAnalysisSummary(summary);
              if (result.ai_summary) {
                setAiSummary(result.ai_summary);
              }
              setSuccess(`${resultsData.length} malzeme yüklendi.`);
            }
          }
        } catch (error) {
          console.error('❌ ID ile yükleme hatası:', error);
        }
        
        sessionStorage.removeItem('loadAnalysisId');
        sessionStorage.removeItem('loadAnalysisType');
        sessionStorage.removeItem('loadDatasetId');
      }
      
      completeLifecycle();
      setIsDataLoading(false);
    };
    init();
  }, [runLifecycle, checkUploadedData, completeLifecycle, generateSummary]);

  // ============================================================
  // 📌 ANALİZ BAŞLAT
  // ============================================================

  const startAnalysis = async () => {
    setAnalysisSteps(prev => prev.map(step => ({ ...step, status: 'pending', timestamp: undefined })));
    setAnalysisActiveStep(-1);
    setIsAnalysisComplete(false);
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    setProgressLabel('Analiz başlıyor...');
    setShowResults(false);
    setAiSummary(null);
    
    try {
      const updateStep = (index: number, status: ProcessStep['status']) => {
        setAnalysisSteps(prev => prev.map((step, i) => {
          if (i === index) {
            return {
              ...step,
              status,
              timestamp: status === 'completed' || status === 'active' ? new Date().toLocaleTimeString() : undefined,
            };
          }
          return step;
        }));
        setAnalysisActiveStep(index);
      };

      const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

      updateStep(0, 'active');
      await sleep(300);
      updateStep(0, 'completed');
      setProgress(10);

      updateStep(1, 'active');
      await sleep(400);
      updateStep(1, 'completed');
      setProgress(25);

      updateStep(2, 'active');
      await sleep(300);
      updateStep(2, 'completed');
      setProgress(40);

      updateStep(3, 'active');
      const response = await ssMutation.mutateAsync();
      updateStep(3, 'completed');
      setProgress(65);
      
      if (response.results) {
        setResults(response.results);
        setPage(0);
        setShowResults(true);
        const summary = generateSummary(response.results);
        setAnalysisSummary(summary);
        
        if (response.ai_summary) {
          setAiSummary(response.ai_summary);
        } else if (response.result_id) {
          try {
            const resultRes = await api.get(`/api/upload/results/${response.result_id}`);
            if (resultRes.data.result?.ai_summary) {
              setAiSummary(resultRes.data.result.ai_summary);
            }
          } catch (err) {
            console.log('⚠️ AI Summary alınamadı:', err);
          }
        }
      }

      updateStep(4, 'active');
      await sleep(300);
      updateStep(4, 'completed');
      setProgress(80);

      updateStep(5, 'active');
      await sleep(400);
      updateStep(5, 'completed');
      setProgress(92);

      updateStep(6, 'active');
      await sleep(300);
      updateStep(6, 'completed');
      setProgress(98);

      updateStep(7, 'active');
      await sleep(200);
      updateStep(7, 'completed');
      
      setIsAnalysisComplete(true);
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      
    } catch (err: any) {
      console.error('❌ Analiz hatası:', err);
      setError(err.response?.data?.detail || err.message || 'Analiz sırasında hata oluştu');
    } finally {
      setIsProcessing(false);
    }
  };

  // ============================================================
  // 📌 ASYNC ANALİZ BAŞLAT
  // ============================================================

  const startAsyncAnalysis = async () => {
    if (!hasUploadedData) {
      setError('Önce veri yüklemelisiniz!');
      return;
    }

    if (isProcessing) {
      return;
    }

    setAsyncSteps([
      { label: 'Analiz başlatılıyor...', description: 'Veriler işleniyor', status: 'active' },
      { label: 'Görev oluşturuluyor...', description: 'Arka plan işlemi başlatılıyor', status: 'pending' },
      { label: 'Görevlere eklendi ✓', description: 'İlerlemeyi ASYNC Görevler sayfasından takip edin', status: 'pending' },
    ]);
    setAsyncActiveStep(0);
    
    setIsProcessing(true);
    setProgress(5);
    setProgressLabel('Async analiz başlatılıyor...');
    setError(null);
    setAiSummary(null);
    
    try {
      const response = await api.post('/api/safety-stock/batch/async', {
        service_level: serviceLevel,
      });
      
      setAsyncActiveStep(1);
      setAsyncSteps(prev => prev.map((step, i) => {
        if (i === 0) return { ...step, status: 'completed', timestamp: new Date().toLocaleTimeString() };
        if (i === 1) return { ...step, status: 'active', timestamp: new Date().toLocaleTimeString() };
        return step;
      }));
      
      setActiveAsyncTask(response.data.task_id);
      setProgress(10);
      setProgressLabel('İşlem kuyruğa alındı.');
      
      setSnackbar({
        open: true,
        message: `✅ Rapor talebiniz başarıyla oluşturuldu. İşlem numarası: #${response.data.task_id.slice(0, 8)}`,
        severity: 'success',
      });
      
      const intervalId = setInterval(async () => {
        try {
          const statusRes = await api.get(`/api/tasks/async/${response.data.task_id}`);
          const task = statusRes.data.task || {};
          
          setProgress(task.progress || 50);
          setProgressLabel(task.message || 'İşleniyor...');
          
          if (task.status === 'completed') {
            clearInterval(intervalId);
            setIsProcessing(false);
            setActiveAsyncTask(null);
            setProgress(100);
            setProgressLabel('Tamamlandı!');
            setIsAsyncComplete(true);
            
            setAsyncSteps(prev => prev.map((step, i) => {
              if (i === 2) return { ...step, status: 'completed', timestamp: new Date().toLocaleTimeString() };
              return step;
            }));
            setAsyncActiveStep(2);
            
            setSuccess(`✅ Analiz tamamlandı! Sonuçları görmek için "Geçmiş" butonuna tıklayın.`);
            
            await fetchUser();
            return;
          }
          
          if (task.status === 'failed' || task.status === 'error') {
            clearInterval(intervalId);
            setIsProcessing(false);
            setActiveAsyncTask(null);
            setProgress(0);
            setProgressLabel('Hata!');
            setError(task.message || 'Async analiz başarısız oldu');
            
            setAsyncSteps(prev => prev.map((step, i) => {
              if (i === 2) return { ...step, status: 'error', timestamp: new Date().toLocaleTimeString() };
              return step;
            }));
          }
        } catch (error) {
          console.error('Async durum kontrol hatası:', error);
        }
      }, 3000);
      
      setTimeout(() => {
        clearInterval(intervalId);
        if (isProcessing) {
          setIsProcessing(false);
          setActiveAsyncTask(null);
          setError('Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.');
        }
      }, 300000);
      
    } catch (err: any) {
      console.error('❌ Async analiz hatası:', err);
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
    }
  };

  // ============================================================
  // 📌 MUTATIONS
  // ============================================================

  const ssMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/safety-stock/batch', { service_level: serviceLevel });
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla analiz edildi.`);
        await fetchUser();
      }
    },
    onError: (err: any) => {
      console.error('❌ Safety Stock hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
    },
  });

  // ============================================================
  // 📌 GEÇMİŞ
  // ============================================================

  const handleHistoryClick = async () => {
    setLoading(true);
    setHistoryDialogOpen(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'safety_stock_batch', limit: 100 }
      });
      
      if (res.data.success && res.data.results && res.data.results.length > 0) {
        const items = res.data.results.map((item: any) => ({
          id: item.id,
          created_at: item.created_at,
          ai_summary: item.ai_summary,
          data: {
            ...item.data,
            report_name: `Emniyet Stoğu - ${new Date(item.created_at).toLocaleDateString('tr-TR')}`,
            total: item.total_materials || item.data?.total || 0,
            status: item.status || 'completed',
          }
        }));
        setHistoryData(items);
      } else {
        setHistoryData([]);
      }
    } catch (err) {
      console.error('❌ Geçmiş yükleme hatası:', err);
      setHistoryData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadHistory = (item: HistoryItem) => {
    const data = item.data || {};
    const resultsData = data.results || [];
    
    if (resultsData.length > 0) {
      setResults(resultsData);
      setPage(0);
      setShowResults(true);
      const summary = generateSummary(resultsData);
      setAnalysisSummary(summary);
      if (item.ai_summary) {
        setAiSummary(item.ai_summary);
      }
      setHistoryDialogOpen(false);
      setSuccess(`${resultsData.length} malzeme geçmiş sonuçları yüklendi.`);
    }
  };

  // ============================================================
  // 📌 TABLO KOLONLARI (Güncellendi)
  // ============================================================

  const columns: TableColumn[] = [
    { 
      id: 'material_code', 
      label: 'Malzeme', 
      width: 110, 
      sticky: true, 
      render: (value) => (
        <Tooltip title={value} arrow>
          <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.65rem' }}>{value}</Typography>
        </Tooltip>
      )
    },
    { id: 'group', label: 'Grup', width: 80, sticky: true },
    { 
      id: 'abc', 
      label: 'ABC', 
      width: 45, 
      sticky: true, 
      render: (value) => (
        <Chip 
          label={value || '-'} 
          size="small" 
          color={value === 'A' ? 'error' : value === 'B' ? 'warning' : 'success'} 
          sx={{ height: 18, fontSize: '0.45rem', fontWeight: 600 }} 
        />
      )
    },
    { 
      id: 'xyz', 
      label: 'XYZ', 
      width: 45, 
      sticky: true, 
      render: (value) => (
        <Chip 
          label={value || '-'} 
          size="small" 
          color={value === 'X' ? 'success' : value === 'Y' ? 'warning' : 'error'} 
          sx={{ height: 18, fontSize: '0.45rem', fontWeight: 600 }} 
        />
      )
    },
    {
      id: 'ai_decision', 
      label: 'AI Kararı', 
      width: 85, 
      highlight: true, 
      render: (_, row) => {  // ✅ value yerine _ kullan, row'dan al
        const decision = row.ai_decision?.decision || '';
        const typeMap: Record<string, AIRecommendationType> = {
          'increase_safety_stock': 'increase',
          'decrease_safety_stock': 'decrease',
          'maintain_current': 'maintain',
          'urgent_action': 'urgent',
        };
        return (
          <AIRecommendationBadge 
            type={typeMap[decision] || 'normal'}  // ✅ decision string'i kullan
            confidence={row.ai_decision?.confidence || 0.5} 
            compact 
          />
        );
      }
    },
    { 
      id: 'recommended_method_label', 
      label: '⭐ AI Seçimi', 
      width: 75, 
      highlight: true, 
      render: (value, row) => (
        <Chip 
          label={value || '-'} 
          size="small" 
          sx={{ 
            bgcolor: alpha(methodColors[row.recommended_method] || '#6b7280', 0.1), 
            color: methodColors[row.recommended_method] || '#6b7280', 
            fontWeight: 600, 
            height: 18, 
            fontSize: '0.45rem', 
            border: `1px solid ${alpha(methodColors[row.recommended_method] || '#6b7280', 0.3)}` 
          }} 
        />
      )
    },
    { 
      id: 'recommended_value', 
      label: 'Önerilen SS', 
      width: 75, 
      highlight: true, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'risk_score', 
      label: 'Risk', 
      width: 70, 
      highlight: true, 
      align: 'center', 
      render: (value) => {
        const val = value ?? 0;
        let icon = '🟢 ↓';
        let color: 'success' | 'warning' | 'error' = 'success';
        if (val > 0.5) { icon = '🔴 ↑'; color = 'error'; }
        else if (val > 0.3) { icon = '🟠 !'; color = 'warning'; }
        return (
          <Chip
            label={`${icon} ${val.toFixed(2)}`}
            size="small"
            color={color}
            sx={{ height: 18, fontSize: '0.5rem', fontWeight: 500, minWidth: 60 }}
          />
        );
      }
    },
    { 
      id: 'classic_ss', 
      label: 'Klasik', 
      width: 50, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'croston_ss', 
      label: 'Croston', 
      width: 55, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'syntetos_boylan_ss', 
      label: 'SB', 
      width: 42, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'bootstrapping_ss', 
      label: 'Bootstrap', 
      width: 60, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'ml_ss', 
      label: 'ML', 
      width: 42, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'hybrid_ss', 
      label: 'Hibrit', 
      width: 50, 
      align: 'right', 
      render: (value) => value?.toFixed(0) || '-' 
    },
    { 
      id: 'actions', 
      label: 'Detay', 
      width: 90, 
      align: 'center', 
      render: (_, row) => (
        <Button
          size="small"
          variant="outlined"
          onClick={() => setSelectedReasoning(row)}
          startIcon={<Visibility sx={{ fontSize: 14 }} />}
          sx={{
            fontSize: '0.5rem',
            textTransform: 'none',
            minWidth: 'auto',
            px: 1,
            borderColor: '#1f4e79',
            color: '#1f4e79',
            '&:hover': { bgcolor: '#f0f7ff' },
          }}
        >
          İncele
        </Button>
      )
    }
  ];

  // ============================================================
  // 📌 RENDER
  // ============================================================

  const summary = analysisSummary;
  const totalProducts = results.length || materialCount || 0;
  const totalSS = summary?.totalRecommendedSS || 0;
  const criticalCount = summary?.highRiskCount || 0;
  const avgService = summary?.avgServiceLevel || 0;
  const estimatedSavings = totalSS > 0 ? Math.round(totalSS * 0.15) : 0;

  const aiAssistantData = aiSummary ? {
    summary: aiSummary.manager_summary || aiSummary.summary || '',
    overall_risk: aiSummary.overall_risk || '',
    confidence: aiSummary.confidence_score || aiSummary.confidence || 0,
    recommendations: aiSummary.recommended_actions || aiSummary.recommendations || [],
    topMethod: summary?.mostUsedMethod ? methodLabelsFull[summary.mostUsedMethod] || summary.mostUsedMethod : '-',
    kpis: {
      total_items: results.length || summary?.totalMaterials || 0,
      high_risk_count: summary?.highRiskCount || 0,
      increase_count: summary?.increaseCount || 0,
      decrease_count: summary?.decreaseCount || 0,
      maintain_count: summary?.maintainCount || 0,
    }
  } : null;

  const kpiData = [
    { label: 'Analiz Edilen Ürün', value: totalProducts, icon: <Inventory sx={{ fontSize: 16 }} />, color: '#1f4e79' },
    { label: 'Önerilen Toplam SS', value: totalSS.toLocaleString(), icon: <BarChart sx={{ fontSize: 16 }} />, color: '#2e7d32' },
    { label: 'Kritik Ürün Sayısı', value: criticalCount, icon: <Warning sx={{ fontSize: 16 }} />, color: criticalCount > 0 ? '#d32f2f' : '#1f4e79' },
    { label: 'Tahmini Servis', value: `${avgService.toFixed(0)}%`, icon: <Speed sx={{ fontSize: 16 }} />, color: avgService > 95 ? '#2e7d32' : avgService > 90 ? '#ed6c02' : '#d32f2f' },
    { label: 'Tahmini Tasarruf', value: `${estimatedSavings.toLocaleString()} TL`, icon: <AttachMoney sx={{ fontSize: 16 }} />, color: '#2e7d32' },
  ];

  // Loading
  if (isDataLoading) {
    return (
      <PageLayout hero={<Hero title="Emniyet Stoğu" loading />}>
        <Box sx={{ py: 4 }}>
          <Grid container spacing={1}>
            {[1, 2, 3, 4, 5].map((i) => (
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={i}>
                <Skeleton variant="rectangular" height={52} sx={{ borderRadius: 2 }} />
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 2 }}><Skeleton variant="rectangular" height={80} sx={{ borderRadius: 2 }} /></Box>
          <Box sx={{ mt: 2 }}><Skeleton variant="rectangular" height={150} sx={{ borderRadius: 2 }} /></Box>
        </Box>
      </PageLayout>
    );
  }

  // Empty
  if (!hasUploadedData && !isCheckingData) {
    return (
      <PageLayout hero={<Hero title="Emniyet Stoğu" datasetName="Veri Yüklenmemiş" productCount={0} aiReady={false} icon={<Security />} />}>
        <Card sx={{ borderRadius: 2, border: '1px dashed #d0d0d0', bgcolor: '#fafcff', py: 4 }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <UploadFile sx={{ fontSize: 48, color: '#b0b0b0', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#374151', mb: 1 }}>Henüz Veri Yüklenmemiş</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto', mb: 2 }}>
              Emniyet stoğu analizi için önce bir Excel dosyası yüklemelisiniz.
            </Typography>
            <Button variant="contained" startIcon={<UploadFile />} onClick={() => window.location.href = '/dashboard'} sx={{ bgcolor: '#1f4e79', '&:hover': { bgcolor: '#1a3d5c' }, textTransform: 'none' }}>Dashboard'a Git</Button>
          </CardContent>
        </Card>
      </PageLayout>
    );
  }

  // Normal Render
  return (
    <PageLayout
      hero={
        <Hero
          title="Emniyet Stoğu (Safety Stock)"
          subtitle="6 farklı metod + ABC/XYZ + AI Destekli"
          datasetName={activeDatasetId ? `Dataset #${activeDatasetId}` : 'Aktif Dataset'}
          productCount={materialCount}
          lastAnalysisDate={showResults && results.length > 0 ? new Date().toLocaleDateString('tr-TR') : undefined}
          aiReady={showResults && results.length > 0}
          aiStatus={showResults && results.length > 0 ? 'hazir' : 'bekleniyor'}
          learningLevel={learningScoreData?.level || 'Başlangıç'}
          learningScore={learningScoreData?.score || 0}
          learningComponents={learningComponents}
          icon={<Security />}
        />
      }
    >
      {/* KPI Kartları */}
      <Box sx={{ mb: 1 }}>
        <Grid container spacing={0.75}>
          {kpiData.map((kpi, index) => (
            <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={index}>
              <KpiCard {...kpi} compact />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Toolbar */}
      <Paper sx={{ p: 0.75, borderRadius: 2, border: '1px solid #e8f0fe', mb: 1 }}>
        <Stack 
          direction="row" 
          spacing={0.5} 
          sx={{ 
            flexWrap: 'wrap', 
            alignItems: 'center', 
            gap: 0.5 
          }}
        >
          <Button
            size="small"
            variant="contained"
            startIcon={ssMutation.isPending ? <CircularProgress size={14} /> : <Send sx={{ fontSize: 14 }} />}
            onClick={startAnalysis}
            disabled={ssMutation.isPending || !hasUploadedData || isProcessing}
            sx={{ fontSize: '0.6rem', textTransform: 'none', py: 0.3, px: 1.5, borderRadius: 1.5, height: 28 }}
          >
            {ssMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>

          <Button
            size="small"
            variant="contained"
            color="secondary"
            startIcon={<Send sx={{ fontSize: 14 }} />}
            onClick={startAsyncAnalysis}
            disabled={!hasUploadedData || isProcessing}
            sx={{ fontSize: '0.6rem', textTransform: 'none', py: 0.3, px: 1.5, borderRadius: 1.5, height: 28 }}
          >
            Arka Planda
          </Button>

          <Button
            size="small"
            variant="outlined"
            startIcon={<History sx={{ fontSize: 14 }} />}
            onClick={handleHistoryClick}
            sx={{ fontSize: '0.6rem', textTransform: 'none', py: 0.3, px: 1.5, borderRadius: 1.5, height: 28, borderColor: '#d0d0d0' }}
          >
            Geçmiş
          </Button>

          <Button
            size="small"
            variant="outlined"
            startIcon={loading ? <CircularProgress size={14} /> : <Download sx={{ fontSize: 14 }} />}
            onClick={handleExport}
            disabled={!showResults || results.length === 0 || loading}
            sx={{ fontSize: '0.6rem', textTransform: 'none', py: 0.3, px: 1.5, borderRadius: 1.5, height: 28, borderColor: '#d0d0d0', minWidth: 'auto' }}
          >
            {loading ? 'İndiriliyor...' : 'Excel'}
          </Button>

          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 0.75, flexWrap: 'wrap' }}>
            {pricingPreview && pricingPreview.estimated_credit_cost > 0 && (
              <Chip
                icon={<AccountBalanceWallet sx={{ fontSize: 12 }} />}
                label={`${pricingPreview.estimated_credit_cost} Kredi`}
                size="small"
                color={pricingPreview.is_sufficient ? 'success' : 'error'}
                sx={{ height: 22, fontSize: '0.45rem' }}
              />
            )}

            {(success || error) && (
              <Box
                sx={{
                  width: '1px',
                  height: '20px',
                  bgcolor: '#d0d0d0',
                  flexShrink: 0,
                }}
              />
            )}

            {success && (
              <Chip
                icon={<CheckCircle sx={{ fontSize: 14 }} />}
                label={success}
                size="small"
                sx={{
                  height: 26,
                  fontSize: '0.55rem',
                  fontWeight: 500,
                  bgcolor: '#e8f5e9',
                  color: '#1e4620',
                  border: '1px solid #a5d6a7',
                  borderRadius: 1.5,
                  maxWidth: 350,
                  '& .MuiChip-label': {
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    px: 1.5,
                  },
                  '& .MuiChip-icon': {
                    color: '#2e7d32',
                    fontSize: 16,
                  },
                }}
                onDelete={() => setSuccess(null)}
              />
            )}

            {error && (
              <Chip
                icon={<Close sx={{ fontSize: 14 }} />}
                label={error}
                size="small"
                sx={{
                  height: 26,
                  fontSize: '0.55rem',
                  fontWeight: 500,
                  bgcolor: '#ffebee',
                  color: '#4a1414',
                  border: '1px solid #ef9a9a',
                  borderRadius: 1.5,
                  maxWidth: 350,
                  '& .MuiChip-label': {
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    px: 1.5,
                  },
                  '& .MuiChip-icon': {
                    color: '#c62828',
                    fontSize: 16,
                  },
                }}
                onDelete={() => setError(null)}
              />
            )}
          </Box>
        </Stack>
      </Paper>

      {/* ✅ AI Summary + Right Panel Grid */}
      <Grid container spacing={1} sx={{ mb: 1 }}>
        {/* Sol: AI Summary + kritik kartlar */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Stack spacing={1}>
            <AIAssistantCard 
              data={aiAssistantData} 
              loading={isDataLoading} 
              compact 
            />
            
            {/* Kritik Kartlar */}
            <Grid container spacing={1}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Paper sx={{ p: 1, borderRadius: 2, border: '1px solid #ffebee', bgcolor: '#fff5f5' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#d32f2f', fontSize: '0.6rem', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Warning sx={{ fontSize: 12 }} /> Kritik Riskler
                  </Typography>
                  <Box sx={{ mt: 0.25 }}>
                    {summary && (summary.highRiskCount ?? 0) > 0 ? (
                      <>
                        <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                          {(summary.highRiskCount ?? 0)} ürün yüksek riskli
                        </Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>
                          Ortalama risk: {(summary.avgRiskScore ?? 0).toFixed(2)}
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>
                        {summary ? 'Kritik risk yok' : 'Analiz bekleniyor'}
                      </Typography>
                    )}
                  </Box>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Paper sx={{ p: 1, borderRadius: 2, border: '1px solid #e8f5e9', bgcolor: '#f5fff7' }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#2e7d32', fontSize: '0.6rem', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Lightbulb sx={{ fontSize: 12 }} /> AI Önerileri
                  </Typography>
                  <Box sx={{ mt: 0.25 }}>
                    {summary && (summary.increaseCount ?? 0) > 0 ? (
                      <>
                        <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151' }}>
                          {(summary.increaseCount ?? 0)} ürün artırılmalı
                        </Typography>
                        <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>
                          {(summary.decreaseCount ?? 0)} ürün azaltılabilir
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>
                        {summary ? 'AI önerisi yok' : 'Analiz bekleniyor'}
                      </Typography>
                    )}
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </Stack>
        </Grid>

        {/* Sağ: Yaşam Döngüsü */}
        <Grid size={{ xs: 12, md: 4 }}>
          <RightPanel
            datasetName={activeDatasetId ? `Dataset #${activeDatasetId}` : 'Aktif Dataset'}
            productCount={materialCount}
            learningLevel={learningScoreData?.level || 'Başlangıç'}
            learningScore={learningScoreData?.score || 0}
            aiReady={showResults && results.length > 0}
            lifecycleSteps={lifecycleSteps}
            lifecycleActiveStep={lifecycleActiveStep}
            isLifecycleComplete={isLifecycleComplete}
            analysisSteps={analysisSteps}
            analysisActiveStep={analysisActiveStep}
            isAnalysisComplete={isAnalysisComplete}
            isProcessing={isProcessing}
            progress={progress}
            progressLabel={progressLabel}
          />
        </Grid>
      </Grid>

      {/* Sonuç Tablosu */}
      {showResults && results.length > 0 ? (
        <Box>
          <SectionHeader
            title="📊 Sonuçlar"
            subtitle={`${results.length} malzeme analiz edildi`}
            badge={`${results.length} ürün`}
            badgeColor="primary"
          />
          <StandardTable
            columns={columns}
            rows={results}
            rowKey="material_code"
            page={page}
            rowsPerPage={rowsPerPage}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
            totalCount={results.length}
            highlightAIColumns
          />
        </Box>
      ) : (
        !isProcessing && hasUploadedData && (
          <Card sx={{ borderRadius: 2, border: '1px dashed #e0e0e0', bgcolor: '#fafcff' }}>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Security sx={{ fontSize: 36, color: '#b0b0b0', mb: 1 }} />
              <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.8rem', fontWeight: 500 }}>
                {isProcessing ? 'Analiz devam ediyor...' : 'Henüz analiz yapılmadı'}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                {isProcessing ? 'Lütfen bekleyin...' : '"Analiz Et" butonuna tıklayarak başlayın'}
              </Typography>
            </CardContent>
          </Card>
        )
      )}

      {/* Dialog'lar */}
      <Dialog open={!!selectedReasoning} onClose={() => setSelectedReasoning(null)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.85rem' }}>🤖 AI Karar Açıklaması</Typography>
            <IconButton onClick={() => setSelectedReasoning(null)} size="small"><Close fontSize="small" /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ py: 1.5 }}>
          {selectedReasoning && (
            <Box>
              <AIReasoningSection result={selectedReasoning} />
              <Box sx={{ mt: 1 }}><TechnicalAnalysisSection result={selectedReasoning} /></Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1 }}>
          <Button onClick={() => setSelectedReasoning(null)} size="small" sx={{ fontSize: '0.65rem', textTransform: 'none' }}>Kapat</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.85rem' }}>📜 Geçmiş Analizler</Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)} size="small"><Close fontSize="small" /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ py: 1.5 }}>
          {loading ? (
            <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress size={28} /></Box>
          ) : historyData.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography color="text.secondary" sx={{ fontSize: '0.8rem' }}>Henüz geçmiş analiz bulunmuyor.</Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f8faff' }}>
                    <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600, color: '#1f4e79' }}>📅 Tarih</TableCell>
                    <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600, color: '#1f4e79' }}>📄 Rapor</TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.65rem', fontWeight: 600, color: '#1f4e79' }}>📦 Ürün</TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.65rem', fontWeight: 600, color: '#1f4e79' }}>⏳ Durum</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.65rem', fontWeight: 600, color: '#1f4e79' }}>🔍 İşlem</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {historyData.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell sx={{ fontSize: '0.65rem' }}>{new Date(item.created_at).toLocaleDateString('tr-TR')}</TableCell>
                      <TableCell sx={{ fontSize: '0.65rem' }}>{item.data?.report_name || 'Emniyet Stoğu'}</TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.65rem' }}>{item.data?.total || 0}</TableCell>
                      <TableCell align="center">
                        <Chip label={item.data?.status === 'completed' ? '✅' : '🔄'} size="small" color={item.data?.status === 'completed' ? 'success' : 'warning'} sx={{ height: 18, fontSize: '0.4rem', minWidth: 30 }} />
                      </TableCell>
                      <TableCell align="right">
                        <Button size="small" variant="outlined" onClick={() => handleLoadHistory(item)} startIcon={<Visibility sx={{ fontSize: 12 }} />} sx={{ fontSize: '0.5rem', textTransform: 'none' }}>Yükle</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1 }}>
          <Button onClick={() => setHistoryDialogOpen(false)} size="small" sx={{ fontSize: '0.65rem', textTransform: 'none' }}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </PageLayout>
  );
}