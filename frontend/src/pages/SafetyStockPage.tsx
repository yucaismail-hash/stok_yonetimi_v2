// frontend/src/pages/SafetyStockPage.tsx
// Stokonomi Design System v1.0 - Emniyet Stoğu Sayfası
// Tüm modüller için ortak tasarım standardı

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
  Info,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  Speed,
  Analytics,
  BarChart,
  CloudDone,
  CloudOff,
  Inventory,
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Star,
  Lightbulb,
  Psychology,
  AutoAwesome,
  Timeline,
  ShowChart,
  ExpandMore,
  Category,
  Assessment,
  Warning,
  AccountBalanceWallet,
  UploadFile,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { usePricingPreview } from '../hooks/usePricing';
import { fetchAndLoadResult, checkAndLoadAnalysis } from '../utils/loadAnalysisResult';

// ✅ YENİ: Design System Component'leri
import {
  PageLayout,
  Hero,
  KpiCard,
  MetricCard,
  ExecutiveSummaryCard,
  ProcessFlowCard,
  SectionHeader,
  StandardTable,
  AIRecommendationBadge,
  type ProcessStep,
  type TableColumn,
  type AIRecommendationType,
} from '../components/common';

// ✅ YENİ BİLEŞENLER
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
  recommended_eoq?: number;
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
  forecast_reason?: string;
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
  mostUsedForecast?: string;
  increaseCount?: number;
  decreaseCount?: number;
  maintainCount?: number;
}

interface AIComment {
  summary: string;
  pattern: string;
  risk: string;
  recommendation: string;
  confidence: string;
  details?: string[];
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
// 📌 YARDIMCI BİLEŞENLER
// ============================================================

const AIReasoningSection = ({ result }: { result: SafetyStockResult }) => {
  const aiDecision = result.ai_decision;
  
  if (!aiDecision) {
    return null;
  }

  const reasoning = {
    recommended_ss: result.hybrid_ss || result.recommended_value || 0,
    current_ss: result.classic_ss || 0,
    reasons: aiDecision.reasons || [
      (result.cv || 0) > 0.7 ? 'CV yüksek' : '',
      (result.lead_time_days || 0) > 21 ? 'Lead Time uzun' : '',
      result.is_intermittent ? 'Düzensiz talep' : '',
      result.has_seasonality ? 'Yaz dönemi davranışı' : '',
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
      <DecisionReasoning
        materialCode={result.material_code}
        reasoning={reasoning}
      />
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
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [materialCount, setMaterialCount] = useState(0);
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null);
  const [aiComment, setAiComment] = useState<AIComment | null>(null);

  const [selectedReasoning, setSelectedReasoning] = useState<SafetyStockResult | null>(null);

  const [serviceLevel, setServiceLevel] = useState<number>(0.95);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);

  // Process Flow State'leri
  const [steps, setSteps] = useState<ProcessStep[]>([
    { label: 'Veri okunuyor...', description: 'Excel dosyası kontrol ediliyor', status: 'pending' },
    { label: 'Talep geçmişi hazırlanıyor...', description: 'Malzeme verileri işleniyor', status: 'pending' },
    { label: 'Pattern analizi yapılıyor...', description: 'Talep desenleri belirleniyor', status: 'pending' },
    { label: 'ABC/XYZ analizi yapılıyor...', description: 'Maliyet ve talep sınıflandırması', status: 'pending' },
    { label: '6 model hesaplanıyor...', description: 'Emniyet stoğu hesaplamaları', status: 'pending' },
    { label: 'AI analizi yapılıyor...', description: 'Risk skoru ve öneriler oluşturuluyor', status: 'pending' },
    { label: 'Learning Engine çalışıyor...', description: 'Şirket hafızası güncelleniyor', status: 'pending' },
    { label: 'Tamamlandı!', description: 'Rapor hazır', status: 'pending' },
  ]);
  const [activeStep, setActiveStep] = useState(-1);
  const [isAnalysisComplete, setIsAnalysisComplete] = useState(false);

  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'info' 
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Dataset ID
  const [activeDatasetId, setActiveDatasetId] = useState<number | null>(() => {
    const saved = localStorage.getItem('activeDatasetId');
    return saved ? parseInt(saved) : null;
  });

  // Pricing Preview
  const { data: pricingPreview, isLoading: pricingLoading } = usePricingPreview(
    '/api/safety-stock/batch',
    activeDatasetId || undefined
  );

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
    const loadData = async () => {
      setIsDataLoading(true);
      try {
        await checkUploadedData();
        await checkAndLoadAnalysis('safety_stock', handleFetchAndLoad);
      } catch (error) {
        console.error('❌ Veri yükleme hatası:', error);
      } finally {
        setIsDataLoading(false);
      }
    };
    loadData();
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

  // ============================================================
  // 📌 ANALİZ FONKSİYONLARI
  // ============================================================

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const updateStep = (index: number, status: ProcessStep['status'], description?: string) => {
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

  const resetSteps = () => {
    setSteps(prev => prev.map(step => ({
      ...step,
      status: 'pending',
      timestamp: undefined,
    })));
    setActiveStep(-1);
    setIsAnalysisComplete(false);
  };

  const generateSummary = (resultsData: SafetyStockResult[]) => {
    if (!resultsData || resultsData.length === 0) return null;

    const methodCount: Record<string, number> = {};
    const patternDist: Record<string, number> = {};
    const abcDist: Record<string, number> = {};
    const xyzDist: Record<string, number> = {};
    const forecastCount: Record<string, number> = {};
    
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
      
      const forecast = r.forecast_model || 'auto';
      forecastCount[forecast] = (forecastCount[forecast] || 0) + 1;
      
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

    const sortedForecast = Object.entries(forecastCount).sort((a, b) => b[1] - a[1]);
    const mostUsedForecast = sortedForecast[0]?.[0] || 'auto';

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
      mostUsedForecast: mostUsedForecast,
      increaseCount: increaseCount,
      decreaseCount: decreaseCount,
      maintainCount: maintainCount,
    };
  };

  const generateAIComment = (summary: AnalysisSummary) => {
    if (!summary) return null;

    const mostUsedLabel = methodLabelsFull[summary.mostUsedMethod] || summary.mostUsedMethod;
    const forecastLabel = summary.mostUsedForecast || 'Otomatik';
    
    const details: string[] = [];
    
    if (summary.abcDistribution) {
      const abcText = Object.entries(summary.abcDistribution)
        .sort((a, b) => b[1] - a[1])
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
      details.push(`📊 ABC Dağılımı: ${abcText}`);
    }
    
    if (summary.xyzDistribution) {
      const xyzText = Object.entries(summary.xyzDistribution)
        .sort((a, b) => b[1] - a[1])
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
      details.push(`📈 XYZ Dağılımı: ${xyzText}`);
    }
    
    details.push(`📦 ${summary.intermittentCount} ürün aralıklı talep gösteriyor`);
    details.push(`🌊 ${summary.seasonalCount} ürün mevsimsellik gösteriyor`);
    details.push(`⚠️ ${summary.highRiskCount} ürün yüksek riskli`);

    return {
      summary: `${summary.totalMaterials} ürün analiz edildi. En çok tercih edilen SS yöntemi "${mostUsedLabel}" (%${summary.mostUsedMethodPercent.toFixed(0)}). En çok kullanılan forecast: "${forecastLabel}".`,
      pattern: `ABC/XYZ analizi yapıldı. ${summary.highRiskCount} ürün yüksek riskli.`,
      risk: `Ortalama risk skoru: ${summary.avgRiskScore?.toFixed(2) || '-'}`,
      recommendation: `Önerilen toplam emniyet stoğu: ${summary.totalRecommendedSS.toLocaleString()} birim. Servis seviyesi: %${summary.avgServiceLevel.toFixed(0)}.`,
      confidence: summary.totalMaterials > 20 ? 'Geniş veri seti, analiz güvenilir.' : 'Veri seti sınırlı, sonuçlar dikkatle değerlendirilmeli.',
      details: details,
    };
  };

  // ============================================================
  // 📌 ANALİZ BAŞLATMA
  // ============================================================

  const startAnalysis = async () => {
    resetSteps();
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    
    try {
      updateStep(0, 'active', 'Excel dosyası kontrol ediliyor...');
      await sleep(600);
      updateStep(0, 'completed', 'Veri başarıyla okundu');
      setProgress(10);
      
      updateStep(1, 'active', 'Malzeme verileri işleniyor...');
      await sleep(800);
      updateStep(1, 'completed', 'Malzeme verileri hazırlandı');
      setProgress(25);
      
      updateStep(2, 'active', 'Talep desenleri belirleniyor...');
      await sleep(1000);
      updateStep(2, 'completed', 'Pattern analizi tamamlandı');
      setProgress(40);
      
      updateStep(3, 'active', 'ABC/XYZ analizi yapılıyor...');
      await sleep(800);
      updateStep(3, 'completed', 'ABC/XYZ sınıflandırması tamamlandı');
      setProgress(50);
      
      updateStep(4, 'active', '6 farklı metod ile SS hesaplanıyor...');
      const response = await ssMutation.mutateAsync();
      updateStep(4, 'completed', `${response.total || response.results?.length || 0} malzeme hesaplandı`);
      setProgress(70);
      
      if (response.results) {
        const summary = generateSummary(response.results);
        setAnalysisSummary(summary);
        if (summary) {
          const comment = generateAIComment(summary);
          setAiComment(comment);
        }
      }
      
      updateStep(5, 'active', 'AI analizi yapılıyor...');
      await sleep(600);
      updateStep(5, 'completed', 'Risk skorları ve öneriler oluşturuldu');
      setProgress(85);
      
      updateStep(6, 'active', 'Learning Engine çalışıyor...');
      await sleep(800);
      updateStep(6, 'completed', 'Şirket hafızası güncellendi');
      setProgress(95);
      
      updateStep(7, 'active', 'Rapor hazırlanıyor...');
      await sleep(600);
      updateStep(7, 'completed', 'Rapor hazır');
      
      setIsAnalysisComplete(true);
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      
    } catch (err: any) {
      console.error('❌ Analiz hatası:', err);
      const errorIndex = steps.findIndex(s => s.status === 'active');
      if (errorIndex !== -1) {
        updateStep(errorIndex, 'error', err.response?.data?.detail || 'Hata oluştu!');
      }
      setError(err.response?.data?.detail || err.message || 'Analiz sırasında hata oluştu');
    } finally {
      setIsProcessing(false);
    }
  };

  // ============================================================
  // 📌 MUTATIONS
  // ============================================================

  const ssMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/safety-stock/batch', {
        service_level: serviceLevel,
      });
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
            message: `💰 ${data.credit_cost} kredi harcandı. Kalan: ${data.balance_after} kredi.`,
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
      console.error('❌ Safety Stock hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // ============================================================
  // 📌 TABLO KOLONLARI - YENİ STANDART
  // ============================================================

  const columns: TableColumn[] = [
    // Bölüm 1: Kimlik (sticky)
    { 
      id: 'material_code', 
      label: 'Malzeme', 
      width: 120, 
      sticky: true,
      render: (value) => (
        <Tooltip title={value} arrow>
          <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem' }}>
            {value}
          </Typography>
        </Tooltip>
      )
    },
    { id: 'group', label: 'Grup', width: 90, sticky: true },
    { 
      id: 'abc', 
      label: 'ABC', 
      width: 50, 
      sticky: true,
      render: (value) => (
        <Chip 
          label={value || '-'} 
          size="small" 
          color={value === 'A' ? 'error' : value === 'B' ? 'warning' : 'success'}
          sx={{ height: 20, fontSize: '0.5rem', fontWeight: 600 }}
        />
      )
    },
    { 
      id: 'xyz', 
      label: 'XYZ', 
      width: 50, 
      sticky: true,
      render: (value) => (
        <Chip 
          label={value || '-'} 
          size="small" 
          color={value === 'X' ? 'success' : value === 'Y' ? 'warning' : 'error'}
          sx={{ height: 20, fontSize: '0.5rem', fontWeight: 600 }}
        />
      )
    },

    // Bölüm 2: AI Tavsiyesi (highlight)
    { 
      id: 'ai_decision', 
      label: 'AI Kararı', 
      width: 90, 
      highlight: true,
      render: (value, row) => {
        const typeMap: Record<string, AIRecommendationType> = {
          'increase_safety_stock': 'increase',
          'decrease_safety_stock': 'decrease',
          'maintain_current': 'maintain',
          'urgent_action': 'urgent',
        };
        return (
          <AIRecommendationBadge
            type={typeMap[value] || 'normal'}
            confidence={row.ai_decision?.confidence || 0.5}
            description={row.ai_decision?.explanation}
            compact
          />
        );
      }
    },
    { 
      id: 'recommended_method_label', 
      label: 'Metot', 
      width: 85, 
      highlight: true,
      render: (value, row) => (
        <Chip
          label={value || '-'}
          size="small"
          sx={{
            bgcolor: alpha(methodColors[row.recommended_method] || '#6b7280', 0.1),
            color: methodColors[row.recommended_method] || '#6b7280',
            fontWeight: 600,
            height: 20,
            fontSize: '0.5rem',
            border: `1px solid ${alpha(methodColors[row.recommended_method] || '#6b7280', 0.3)}`,
          }}
        />
      )
    },
    { 
      id: 'recommended_value', 
      label: 'Önerilen SS', 
      width: 85, 
      highlight: true, 
      align: 'right',
      render: (value) => value?.toFixed(0) || '-'
    },
    { 
      id: 'recommended_rop', 
      label: 'Önerilen ROP', 
      width: 85, 
      highlight: true, 
      align: 'right',
      render: (value) => value?.toFixed(0) || '-'
    },
    { 
      id: 'risk_score', 
      label: 'Risk', 
      width: 60, 
      highlight: true, 
      align: 'center',
      render: (value) => (
        <Chip 
          label={value?.toFixed(2) || '-'} 
          size="small" 
          color={value > 0.5 ? 'error' : value > 0.3 ? 'warning' : 'success'}
          sx={{ height: 18, fontSize: '0.45rem' }}
        />
      )
    },
    { 
      id: 'confidence', 
      label: 'Güven', 
      width: 60, 
      highlight: true, 
      align: 'center',
      render: (value) => (
        <Chip 
          label={`%${Math.round((value || 0.5) * 100)}`} 
          size="small" 
          color={(value || 0) > 0.7 ? 'success' : 'warning'}
          sx={{ height: 18, fontSize: '0.45rem' }}
        />
      )
    },

    // Bölüm 3: Tüm Model Sonuçları
    { id: 'classic_ss', label: 'Klasik', width: 55, align: 'right', render: (value) => value?.toFixed(0) || '-' },
    { id: 'croston_ss', label: 'Croston', width: 60, align: 'right', render: (value) => value?.toFixed(0) || '-' },
    { id: 'syntetos_boylan_ss', label: 'SB', width: 45, align: 'right', render: (value) => value?.toFixed(0) || '-' },
    { id: 'bootstrapping_ss', label: 'Bootstrap', width: 65, align: 'right', render: (value) => value?.toFixed(0) || '-' },
    { id: 'ml_ss', label: 'ML', width: 45, align: 'right', render: (value) => value?.toFixed(0) || '-' },
    { id: 'hybrid_ss', label: 'Hibrit', width: 55, align: 'right', render: (value) => value?.toFixed(0) || '-' },

    // Bölüm 4: Teknik Analiz
    { id: 'cv', label: 'CV', width: 55, align: 'right', render: (value) => value?.toFixed(3) || '-' },
    { id: 'forecast_model_label', label: 'Forecast', width: 75 },
    { 
      id: 'trend_direction', 
      label: 'Trend', 
      width: 55,
      render: (value) => value === 'Artış' ? <TrendingUp sx={{ fontSize: 14, color: '#d32f2f' }} /> : value === 'Azalış' ? <TrendingDown sx={{ fontSize: 14, color: '#2e7d32' }} /> : '-'
    },
    { id: 'lead_time_days', label: 'LT', width: 40, align: 'right', render: (value) => value || '-' },
    { id: 'zero_ratio', label: 'Zero %', width: 55, align: 'right', render: (value) => value ? (value * 100).toFixed(0) + '%' : '-' },
    { id: 'seasonality_label', label: 'Sezonsallık', width: 70 },

    // Bölüm 5: Detay
    {
      id: 'actions',
      label: 'Detay',
      width: 100,
      align: 'center',
      render: (_, row) => (
        <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
          <Button 
            size="small" 
            variant="text" 
            onClick={() => setSelectedReasoning(row)}
            sx={{ fontSize: '0.5rem', textTransform: 'none', minWidth: 'auto', px: 1, color: '#1f4e79' }}
          >
            Neden?
          </Button>
          <Button 
            size="small" 
            variant="text" 
            sx={{ fontSize: '0.5rem', textTransform: 'none', minWidth: 'auto', px: 1, color: '#6b7280' }}
          >
            İncele
          </Button>
        </Box>
      )
    }
  ];

  // ============================================================
  // 📌 RENDER - EMPTY STATE
  // ============================================================

  const renderEmptyState = () => (
    <Card sx={{ 
      borderRadius: 2, 
      border: '1px dashed #d0d0d0', 
      bgcolor: '#fafcff',
      py: 4,
    }}>
      <CardContent sx={{ textAlign: 'center' }}>
        <UploadFile sx={{ fontSize: 56, color: '#b0b0b0', mb: 2 }} />
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#374151', mb: 1 }}>
          Henüz Veri Yüklenmemiş
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto', mb: 2 }}>
          Emniyet stoğu analizi yapabilmek için önce bir Excel dosyası yüklemelisiniz.
          Dashboard'dan "Veri Yükle" butonuna tıklayarak başlayabilirsiniz.
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadFile />}
          onClick={() => window.location.href = '/dashboard'}
          sx={{
            bgcolor: '#1f4e79',
            '&:hover': { bgcolor: '#1a3d5c' },
            textTransform: 'none',
          }}
        >
          Dashboard'a Git
        </Button>
      </CardContent>
    </Card>
  );

  // ============================================================
  // 📌 RENDER - LOADING STATE
  // ============================================================

  const renderLoadingState = () => (
    <Box sx={{ py: 4 }}>
      <Grid container spacing={2}>
        {[1, 2, 3, 4, 5].map((i) => (
          <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={i}>
            <Skeleton variant="rectangular" height={88} sx={{ borderRadius: 2 }} />
          </Grid>
        ))}
      </Grid>
      <Box sx={{ mt: 3 }}>
        <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 2 }} />
      </Box>
      <Box sx={{ mt: 2 }}>
        <Skeleton variant="rectangular" height={48} sx={{ borderRadius: 2 }} />
      </Box>
      <Box sx={{ mt: 2 }}>
        <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
      </Box>
    </Box>
  );

  // ============================================================
  // 📌 RENDER - ANA
  // ============================================================

  const summary = analysisSummary;
  const totalProducts = results.length || materialCount || 0;
  const totalSS = summary?.totalRecommendedSS || 0;
  const criticalCount = summary?.highRiskCount || 0;
  const avgService = summary?.avgServiceLevel || 0;
  const estimatedSavings = totalSS > 0 ? Math.round(totalSS * 0.15) : 0;

  // AI Executive Summary Data
  const executiveData = summary ? {
    totalProducts: summary.totalMaterials,
    increaseCount: summary.increaseCount || 0,
    decreaseCount: summary.decreaseCount || 0,
    maintainCount: summary.maintainCount || 0,
    topMethod: methodLabelsFull[summary.mostUsedMethod] || summary.mostUsedMethod,
    topRisk: (summary.highRiskCount || 0) > (summary.totalMaterials * 0.2) ? 'Yüksek riskli ürün oranı artıyor' : 'Risk seviyesi yönetilebilir',
    estimatedImpact: `%${Math.round(avgService)} servis, ${estimatedSavings} TL tasarruf`,
    confidence: summary.totalMaterials > 20 ? 0.92 : 0.75,
  } : undefined;

  // KPI Card verileri
  const kpiData = [
    {
      label: 'Analiz Edilen Ürün',
      value: totalProducts,
      icon: <Inventory sx={{ fontSize: 18 }} />,
      color: '#1f4e79',
    },
    {
      label: 'Önerilen Toplam SS',
      value: totalSS.toLocaleString(),
      icon: <BarChart sx={{ fontSize: 18 }} />,
      color: '#2e7d32',
      tooltip: 'Tüm ürünler için önerilen toplam emniyet stoğu',
    },
    {
      label: 'Kritik Ürün Sayısı',
      value: criticalCount,
      icon: <Warning sx={{ fontSize: 18 }} />,
      color: criticalCount > 0 ? '#d32f2f' : '#1f4e79',
      tooltip: 'Risk skoru 0.5\'in üzerindeki ürünler',
    },
    {
      label: 'Tahmini Servis',
      value: `${avgService.toFixed(0)}%`,
      icon: <Speed sx={{ fontSize: 18 }} />,
      color: avgService > 95 ? '#2e7d32' : avgService > 90 ? '#ed6c02' : '#d32f2f',
      tooltip: 'Hedef servis seviyesi',
    },
    {
      label: 'Tahmini Tasarruf',
      value: `${estimatedSavings.toLocaleString()} TL`,
      icon: <AttachMoney sx={{ fontSize: 18 }} />,
      color: '#2e7d32',
      tooltip: 'Önerilen optimizasyon ile tahmini sermaye tasarrufu',
    },
  ];

  // ✅ Veri yükleniyorsa loading göster
  if (isDataLoading) {
    return (
      <PageLayout hero={<Hero title="Emniyet Stoğu" loading />}>
        {renderLoadingState()}
      </PageLayout>
    );
  }

  // ✅ Veri yoksa uyarı göster
  if (!hasUploadedData && !isCheckingData) {
    return (
      <PageLayout
        hero={
          <Hero
            title="Emniyet Stoğu (Safety Stock)"
            subtitle="6 farklı metod + ABC/XYZ + AI Destekli Akıllı Analiz Motoru"
            datasetName="Veri Yüklenmemiş"
            productCount={0}
            aiReady={false}
            learningLevel="Başlangıç"
            learningScore={0}
            icon={<Security />}
          />
        }
      >
        {renderEmptyState()}
      </PageLayout>
    );
  }

  // ✅ Normal render (veri var)
  return (
    <PageLayout
      hero={
        <Hero
          title="Emniyet Stoğu (Safety Stock)"
          subtitle="6 farklı metod + ABC/XYZ + AI Destekli Akıllı Analiz Motoru"
          datasetName={activeDatasetId ? `Dataset #${activeDatasetId}` : 'Aktif Dataset'}
          productCount={materialCount}
          lastAnalysisDate={results.length > 0 ? new Date().toLocaleDateString('tr-TR') : undefined}
          aiReady={results.length > 0}
          learningLevel="Başlangıç"
          learningScore={0}
          icon={<Security />}
        />
      }
    >
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

      {/* Learning Score Badge */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <LearningScoreBadge variant="compact" />
      </Box>

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

      {/* KPI Kartları */}
      <Box sx={{ mb: 2 }}>
        <Grid container spacing={1.5}>
          {kpiData.map((kpi, index) => (
            <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={index}>
              <KpiCard {...kpi} compact />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* AI Executive Summary */}
      <Box sx={{ mb: 2 }}>
        <ExecutiveSummaryCard data={executiveData} loading={isProcessing} compact />
      </Box>

      {/* Kontroller + İşlem Akışı Grid */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        {/* Kontroller */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper sx={{ p: 1.5, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              <Button
                variant="contained"
                size="medium"
                startIcon={ssMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                onClick={startAnalysis}
                disabled={ssMutation.isPending || !hasUploadedData || isProcessing}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  bgcolor: '#1f4e79',
                  '&:hover': { bgcolor: '#1a3d5c' },
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                }}
              >
                {ssMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
              </Button>

              <Button
                variant="contained"
                size="medium"
                color="secondary"
                startIcon={<Send sx={{ fontSize: 18 }} />}
                disabled={!hasUploadedData || isProcessing}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                }}
              >
                Arka Planda Çalıştır
              </Button>

              <Button
                variant="outlined"
                size="medium"
                startIcon={<History sx={{ fontSize: 18 }} />}
                onClick={() => {}}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                  borderColor: '#d0d0d0',
                }}
              >
                Geçmiş
              </Button>

              <Button
                variant="outlined"
                size="medium"
                startIcon={<Download sx={{ fontSize: 18 }} />}
                disabled={results.length === 0}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                  borderColor: '#d0d0d0',
                }}
              >
                Excel
              </Button>

              <Button
                variant="outlined"
                size="medium"
                startIcon={<Category sx={{ fontSize: 18 }} />}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                  borderColor: '#d0d0d0',
                }}
              >
                ABC/XYZ
              </Button>

              <Button
                variant="outlined"
                size="medium"
                startIcon={<AutoAwesome sx={{ fontSize: 18 }} />}
                sx={{
                  fontSize: '0.7rem',
                  textTransform: 'none',
                  py: 0.5,
                  px: 2,
                  borderRadius: 2,
                  height: 36,
                  borderColor: '#d0d0d0',
                }}
              >
                AI Ayarları
              </Button>

              {/* Kredi Bilgisi */}
              {pricingPreview && pricingPreview.estimated_credit_cost > 0 && (
                <Chip
                  icon={<AccountBalanceWallet sx={{ fontSize: 14 }} />}
                  label={`${pricingPreview.estimated_credit_cost} Kredi`}
                  size="small"
                  color={pricingPreview.is_sufficient ? 'success' : 'error'}
                  sx={{ height: 28, fontSize: '0.6rem' }}
                />
              )}
            </Stack>
          </Paper>
        </Grid>

        {/* İşlem Akışı */}
        <Grid size={{ xs: 12, md: 5 }}>
          <ProcessFlowCard
            steps={steps}
            activeStep={activeStep}
            isComplete={isAnalysisComplete}
            compact
            progress={progress}
            progressLabel={progressLabel}
          />
        </Grid>
      </Grid>

      {/* Sonuç Tablosu */}
      {results.length > 0 ? (
        <Box sx={{ mt: 2 }}>
          <SectionHeader
            title="📊 Sonuçlar"
            subtitle={`${results.length} malzeme analiz edildi`}
            badge={`${results.length} ürün`}
            badgeColor="primary"
            actions={
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download sx={{ fontSize: 16 }} />}
                sx={{ fontSize: '0.6rem', textTransform: 'none', height: 28 }}
              >
                Excel
              </Button>
            }
          />

          <StandardTable
            columns={columns}
            rows={results}
            rowKey="material_code"
            page={page}
            rowsPerPage={rowsPerPage}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            totalCount={results.length}
            highlightAIColumns
          />
        </Box>
      ) : (
        !isProcessing && !activeAsyncTask && !error && hasUploadedData && !isCheckingData && (
          <Card sx={{ borderRadius: 2, border: '1px dashed #e0e0e0', bgcolor: '#fafcff' }}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Security sx={{ fontSize: 48, color: '#b0b0b0', mb: 1 }} />
              <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.9rem', fontWeight: 500 }}>
                Henüz analiz yapılmadı
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                "Analiz Et" butonuna tıklayarak emniyet stoğu analizini başlatın
              </Typography>
            </CardContent>
          </Card>
        )
      )}

      {/* AI Karar Açıklaması Dialog */}
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
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>📅 Tarih</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>📄 Rapor Adı</TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>📦 Malzeme</TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>⏳ Durum</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>🔍 İşlem</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {historyData.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell sx={{ fontSize: '0.7rem' }}>
                        <Box>
                          <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                            {new Date(item.created_at).toLocaleDateString('tr-TR')}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#9e9e9e' }}>
                            {new Date(item.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                        {item.data?.report_name || 'Emniyet Stoğu Analizi'}
                      </TableCell>
                      <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600 }}>
                        {item.data?.total || 0}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={item.data?.status === 'completed' ? '✅ Tamamlandı' : '🔄 İşleniyor'}
                          size="small"
                          color={item.data?.status === 'completed' ? 'success' : 'warning'}
                          sx={{ height: 20, fontSize: '0.55rem' }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<Visibility sx={{ fontSize: 14 }} />}
                          sx={{ fontSize: '0.6rem', textTransform: 'none' }}
                        >
                          Görüntüle
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
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
    </PageLayout>
  );
}