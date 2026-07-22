// frontend/src/pages/SafetyStockPage.tsx - TAM DOSYA (GÜNCELLENMİŞ)
// 🆕 Cost query'ler kaldırıldı, credit_cost/balance_after eklendi

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
  Stepper,
  Step,
  StepLabel,
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
  Check,
  Close as CloseIcon,
  AccountBalanceWallet,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { usePricingPreview } from '../hooks/usePricing';
import { fetchAndLoadResult, checkAndLoadAnalysis } from '../utils/loadAnalysisResult';
interface SafetyStockResult {
  material_code: string;
  group: string;
  lead_time_days: number;
  pattern: string;
  pattern_label: string;
  pattern_color: string;
  cv: number;
  zero_ratio: number;
  trend: number;
  classic_ss: number;
  croston_ss: number;
  syntetos_boylan_ss: number;
  bootstrapping_ss: number;
  ml_ss: number;
  hybrid_ss: number;
  recommended_method: string;
  recommended_method_label: string;
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
}

interface AIComment {
  summary: string;
  pattern: string;
  risk: string;
  recommendation: string;
  confidence: string;
  details?: string[];
}

const methodLabelsFull: Record<string, string> = {
  classic_ss: 'Klasik SS',
  croston_ss: 'Croston',
  syntetos_boylan_ss: 'Syntetos-Boylan',
  bootstrapping_ss: 'Bootstrapping',
  ml_ss: 'ML Tabanlı',
  hybrid_ss: 'Hibrit',
};

// ✅ AI Executive Summary Bileşeni
const AIExecutiveSummary = ({
  summary,
  aiComment,
  loading,
}: {
  summary: AnalysisSummary | null;
  aiComment: AIComment | null;
  loading: boolean;
}) => {
  if (loading) {
    return (
      <Card sx={{ bgcolor: '#f8faff', border: '1px solid #e8f0fe', height: '100%' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Skeleton variant="circular" width={32} height={32} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="40%" height={20} />
              <Skeleton variant="text" width="60%" height={14} />
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!summary || !aiComment) {
    return (
      <Card sx={{ bgcolor: '#f8faff', border: '1px solid #e8f0fe', height: '100%' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Lightbulb sx={{ fontSize: 18, color: '#6b7280' }} />
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
              AI Analiz Özeti
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
              — Henüz veri yok
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{
      bgcolor: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)',
      border: '1px solid #d0e0ff',
      borderRadius: 2,
      height: '100%',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: '#1f4e79' }} />

      <CardContent sx={{ py: 1.5, px: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar sx={{ bgcolor: '#1f4e79', width: 32, height: 32 }}>
            <Psychology sx={{ fontSize: 16, color: 'white' }} />
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.8rem' }}>
                🤖 AI Analiz Özeti
              </Typography>
              {summary.totalMaterials > 0 && (
                <Chip
                  label={`${summary.totalMaterials} ürün`}
                  size="small"
                  sx={{ height: 18, fontSize: '0.5rem', bgcolor: 'white' }}
                />
              )}
            </Box>
            <Typography variant="body2" sx={{ color: '#1f4e79', fontSize: '0.75rem', mt: 0.25 }}>
              {aiComment.summary}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 1 }} />

        <Grid container spacing={1}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>📊 Analiz</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: '#1f4e79' }}>
                {summary.totalMaterials}
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>⚠️ Yüksek Risk</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: '#d32f2f' }}>
                {summary.highRiskCount || 0}
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>📈 Aralıklı Talep</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: '#ed6c02' }}>
                {summary.intermittentCount || 0}
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280' }}>🌊 Mevsimsellik</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: '#1976d2' }}>
                {summary.seasonalCount || 0}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {aiComment.details && aiComment.details.length > 0 && (
          <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
            {aiComment.details.slice(0, 2).map((detail, idx) => (
              <Typography key={idx} variant="caption" sx={{ fontSize: '0.6rem', color: '#374151', display: 'block' }}>
                {detail}
              </Typography>
            ))}
            {aiComment.details.length > 2 && (
              <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#9e9e9e' }}>
                +{aiComment.details.length - 2} daha...
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

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

// ✅ Method Tooltip Bileşeni
const MethodTooltip = ({ method }: { method: any }) => {
  return (
    <Box sx={{ p: 1.5, maxWidth: 280 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem', mb: 0.5 }}>
        {method.tooltip.title}
      </Typography>
      <Divider sx={{ mb: 1 }} />
      
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.75 }}>
        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#1f4e79', fontWeight: 600, minWidth: 14 }}>📌</Typography>
        <Box>
          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e', display: 'block', fontWeight: 500 }}>
            Ne zaman kullanılır?
          </Typography>
          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#374151' }}>
            {method.tooltip.when}
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
            {method.tooltip.example}
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
            {method.tooltip.advantage}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default function SafetyStockPage() {
  const { user, fetchUser } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
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

  const [serviceLevel, setServiceLevel] = useState<number>(0.95);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);

  const [steps, setSteps] = useState<AnalysisStep[]>([
    { label: 'Veri okunuyor...', description: 'Excel dosyası kontrol ediliyor', status: 'pending' },
    { label: 'Talep geçmişi hazırlanıyor...', description: 'Malzeme verileri işleniyor', status: 'pending' },
    { label: 'Pattern analizi yapılıyor...', description: 'Talep desenleri belirleniyor', status: 'pending' },
    { label: 'ABC/XYZ analizi yapılıyor...', description: 'Maliyet ve talep sınıflandırması', status: 'pending' },
    { label: 'Emniyet stoğu hesaplanıyor...', description: '6 farklı metod ile SS hesaplanıyor', status: 'pending' },
    { label: 'AI analizi yapılıyor...', description: 'Risk skoru ve öneriler oluşturuluyor', status: 'pending' },
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
    '/api/safety-stock/batch',
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

  const methodDetails = [
    {
      key: 'classic_ss',
      label: 'Klasik SS',
      icon: <BarChart fontSize="small" />,
      short: 'Düzenli satış yapan ürünler',
      tooltip: {
        title: 'Klasik Emniyet Stoğu',
        when: 'Düzenli ve istikrarlı talep yapısına sahip ürünler.',
        example: 'Günlük tüketim ürünleri, temel gıda maddeleri.',
        advantage: 'Basit hesaplama, hızlı sonuç, sektörde yaygın kabul görmüş.',
      },
    },
    {
      key: 'croston_ss',
      label: 'Croston',
      icon: <Analytics fontSize="small" />,
      short: 'Seyrek satılan ürünler',
      tooltip: {
        title: 'Croston Yöntemi',
        when: 'Aralıklı ve seyrek talep gösteren ürünler.',
        example: 'Yedek parçalar, bakım ekipmanları, özel sipariş ürünleri.',
        advantage: 'Talep olmayan dönemleri hesaba katarak daha doğru sonuç verir.',
      },
    },
    {
      key: 'syntetos_boylan_ss',
      label: 'Syntetos-Boylan',
      icon: <Analytics fontSize="small" />,
      short: 'Aralıklı talep gören ürünler',
      tooltip: {
        title: 'Syntetos-Boylan Yöntemi',
        when: 'Aralıklı talep gören ürünler (Croston\'un gelişmiş hali).',
        example: 'Nadir satılan ürünler, mevsimlik ürünler, özel koleksiyon ürünleri.',
        advantage: 'Croston\'un sistematik hatasını düzeltir, daha güvenilir sonuç.',
      },
    },
    {
      key: 'bootstrapping_ss',
      label: 'Bootstrapping',
      icon: <Speed fontSize="small" />,
      short: 'Dalgalı talep yapısı',
      tooltip: {
        title: 'Bootstrapping Yöntemi',
        when: 'Aşırı değişken ve düzensiz talep gösteren ürünler.',
        example: 'Promosyonlu ürünler, trend ürünler, yeni lansmanlar.',
        advantage: 'Binlerce senaryo oluşturarak en gerçekçi ve güvenilir sonucu verir.',
      },
    },
    {
      key: 'ml_ss',
      label: 'ML Tabanlı',
      icon: <Analytics fontSize="small" />,
      short: 'Karmaşık talep analizi',
      tooltip: {
        title: 'Makine Öğrenmesi Yöntemi',
        when: 'Karmaşık ve çok değişkenli talep yapısına sahip ürünler.',
        example: 'E-ticaret ürünleri, çok sayıda SKU\'su olan işletmeler.',
        advantage: 'Geçmiş verilerden öğrenir, kullanıldıkça daha doğru hale gelir.',
      },
    },
    {
      key: 'hybrid_ss',
      label: 'Hibrit',
      icon: <Star fontSize="small" />,
      short: '⭐ Varsayılan Öneri',
      tooltip: {
        title: 'Hibrit (Akıllı Seçim)',
        when: 'Tüm talep türleri için uygun, en çok önerilen yöntem.',
        example: 'Tüm ürün grupları için ideal başlangıç noktası.',
        advantage: '6 yöntemin tamamını değerlendirir, talep yapısına en uygun olanı seçer.',
      },
      isRecommended: true,
    },
  ];

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
    checkAndLoadAnalysis('safety_stock', handleFetchAndLoad);
  }, []);

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

  const startAnalysis = async () => {
    clearAllSteps();
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
      setProgress(55);
      
      updateStep(4, 'active', '6 farklı metod ile SS hesaplanıyor...');
      const response = await ssMutation.mutateAsync();
      updateStep(4, 'completed', `${response.total || response.results?.length || 0} malzeme hesaplandı`);
      setProgress(75);
      
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
      setProgress(90);
      
      updateStep(6, 'active', 'Excel dosyası hazırlanıyor...');
      await sleep(600);
      updateStep(6, 'completed', 'Rapor hazır');
      
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
      const response = await asyncSsMutation.mutateAsync();
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

  // 📌 SENKRON Safety Stock
  const ssMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/safety-stock/batch', {
        service_level: serviceLevel,
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
        
        // ✅ Yeni: credit_cost ve balance_after'i göster
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
      console.error('❌ Safety Stock hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Safety Stock
  const asyncSsMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/safety-stock/batch/async', {
        service_level: serviceLevel,
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
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'safety_stock_batch', limit: 10000 }
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        const batchResults = rawResults.filter((item: any) => item.is_batch === true);
        
        const historyItems = batchResults.map((item: any) => {
          const data = item.data || {};
          const totalMaterials = item.total_materials || data.total || 0;
          const serviceLevelVal = data?.service_level || 0.95;
          const method = data?.recommended_method || data?.method || 'hybrid_ss';
          
          const methodLabelsLocal: Record<string, string> = {
            'classic_ss': 'Klasik',
            'croston_ss': 'Croston',
            'syntetos_boylan_ss': 'Syntetos-Boylan',
            'bootstrapping_ss': 'Bootstrapping',
            'ml_ss': 'ML',
            'hybrid_ss': 'Hibrit',
          };
          const methodLabel = methodLabelsLocal[method] || method;
          const reportName = `Emniyet Stoğu (%${(serviceLevelVal * 100).toFixed(0)}) - ${methodLabel} - ${totalMaterials} Malzeme`;
          
          return {
            id: item.id,
            created_at: item.created_at,
            data: {
              total: totalMaterials,
              results: data.results || [],
              report_name: reportName,
              status: item.status || 'completed',
              service_level: serviceLevelVal,
              method: method,
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
      const response = await api.post('/api/export/safety-stock-results', {
        results: results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `safety_stock_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const getBestMethod = (result: SafetyStockResult) => {
    const methods = ['classic_ss', 'croston_ss', 'syntetos_boylan_ss', 'bootstrapping_ss', 'ml_ss', 'hybrid_ss'];
    const values = methods.map(m => result[m as keyof SafetyStockResult] as number);
    const min = Math.min(...values);
    return methods[values.indexOf(min)];
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

  const getSSColor = (value: number, maxValue: number) => {
    if (value === 0 || !value) return 'text.secondary';
    const ratio = value / maxValue;
    if (ratio < 0.3) return '#2e7d32';
    if (ratio < 0.6) return '#ed6c02';
    return '#d32f2f';
  };

  const handleSliderChange = (_event: Event, value: number | number[]) => {
    const newValue = Array.isArray(value) ? value[0] : value;
    setServiceLevel(newValue);
  };

  const isNormalAnalysisActive = activeStep >= 0 && !isAsyncComplete && !activeAsyncTask;
  const isAsyncAnalysisActive = asyncActiveStep >= 0 || isAsyncComplete;

  const HeroHeader = () => (
    <Card sx={{ mb: 3, borderRadius: 2, bgcolor: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)', border: '1px solid #d0e0ff' }}>
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { md: 'center' }, justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Security sx={{ fontSize: 24, color: '#1f4e79' }} />
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.3rem' }}>
                Emniyet Stoğu (Safety Stock)
              </Typography>
              <Chip label="SS Analizi" size="small" sx={{ height: 20, fontSize: '0.55rem', bgcolor: '#1f4e79', color: 'white' }} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
              6 farklı metod + ABC/XYZ + AI Destekli Akıllı Analiz Motoru
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5, mt: { xs: 1.5, md: 0 }, flexWrap: 'wrap' }}>
            <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label="6 metod" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Category sx={{ fontSize: 14 }} />} label="ABC/XYZ" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Psychology sx={{ fontSize: 14 }} />} label="AI Öneri" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
            <Chip icon={<Download sx={{ fontSize: 14 }} />} label="Excel raporu" size="small" variant="outlined" sx={{ height: 24, fontSize: '0.6rem' }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const KpiCards = () => {
    const summary = analysisSummary;
    const totalPatterns = summary?.patternDistribution ? Object.keys(summary.patternDistribution).length : 0;
    const methodLabel = summary ? (methodLabelsFull[summary.mostUsedMethod] || summary.mostUsedMethod) : '-';
    
    return (
      <Grid container spacing={1.5} sx={{ mb: 2 }}>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Inventory sx={{ fontSize: 18, color: '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: '#1f4e79' }}>
              {results.length || materialCount || 0}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Malzeme</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Category sx={{ fontSize: 18, color: '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: '#1f4e79' }}>
              {totalPatterns || '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Pattern</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AutoAwesome sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? methodLabel : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>En Çok Kullanılan</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <AttachMoney sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.totalRecommendedSS.toLocaleString() : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Önerilen Toplam SS</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: summary ? '#e8f5e9' : '#fafcff', border: '1px solid #e8f0fe', borderRadius: 2 }}>
            <Warning sx={{ fontSize: 18, color: summary ? '#2e7d32' : '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem', color: summary ? '#2e7d32' : '#1f4e79' }}>
              {summary ? summary.highRiskCount : '-'}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280' }}>Yüksek Risk</Typography>
          </Paper>
        </Grid>
      </Grid>
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

      {/* ✅ AI Executive Summary */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, md: 12 }}>
          <AIExecutiveSummary
            summary={analysisSummary}
            aiComment={aiComment}
            loading={isProcessing || false}
          />
        </Grid>
      </Grid>

      {/* ✅ ANA GRID - 2 SÜTUN */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        {/* SOL SÜTUN - İşlem Akışı ve Veri Durumu */}
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

        {/* SAĞ SÜTUN - Butonlar, Servis Seviyesi ve Analiz Özeti */}
        <Grid size={{ xs: 12, md: 7 }}>
          {/* Butonlar */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Button
                  variant="contained"
                  size="medium"
                  startIcon={ssMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAnalysis}
                  disabled={ssMutation.isPending || !hasUploadedData || isProcessing}
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
                  {ssMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
                </Button>

                <Button
                  variant="contained"
                  size="medium"
                  color="secondary"
                  startIcon={asyncSsMutation.isPending ? <CircularProgress size={18} /> : <Send sx={{ fontSize: 18 }} />}
                  onClick={startAsyncAnalysis}
                  disabled={asyncSsMutation.isPending || !hasUploadedData || isProcessing}
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
                  {asyncSsMutation.isPending ? 'Başlatılıyor...' : 'Arka Planda Çalıştır'}
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

          {/* Servis Seviyesi */}
          <Card sx={{ mb: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem', letterSpacing: '0.3px' }}>
                  Servis Seviyesi
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem' }}>
                  {(serviceLevel * 100).toFixed(0)}%
                </Typography>
              </Box>

              <Box sx={{ px: 1 }}>
                <Slider
                  value={serviceLevel}
                  onChange={handleSliderChange}
                  min={0.80}
                  max={0.99}
                  step={0.01}
                  marks={[
                    { value: 0.85, label: '85%' },
                    { value: 0.90, label: '90%' },
                    { value: 0.95, label: '95%' },
                    { value: 0.99, label: '99%' },
                  ]}
                  valueLabelDisplay="auto"
                  size="small"
                  sx={{
                    color: '#1f4e79',
                    '& .MuiSlider-markLabel': { fontSize: '0.5rem', color: '#9e9e9e' },
                    '& .MuiSlider-thumb': { width: 16, height: 16, zIndex: 10 },
                    '& .MuiSlider-track': { height: 4 },
                    '& .MuiSlider-rail': { height: 4 },
                  }}
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1.5, px: 1, borderTop: '1px solid #f0f0f0', pt: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#d32f2f' }} />
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#d32f2f', fontWeight: 500 }}>
                    Düşük stok
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#ed6c02' }} />
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#ed6c02', fontWeight: 500 }}>
                    Dengeli
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#2e7d32' }} />
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#2e7d32', fontWeight: 500 }}>
                    Çok güvenli
                  </Typography>
                </Box>
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
                      En çok kullanılan yöntem: <strong>{methodLabelsFull[analysisSummary.mostUsedMethod] || analysisSummary.mostUsedMethod}</strong>
                      <Chip 
                        label={`%${analysisSummary.mostUsedMethodPercent.toFixed(0)}`} 
                        size="small" 
                        color="success" 
                        sx={{ height: 18, fontSize: '0.5rem', ml: 0.5 }}
                      />
                    </Typography>
                    {analysisSummary.abcDistribution && (
                      <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#1f4e79' }}>
                        ABC: A:{analysisSummary.abcDistribution.A || 0}, B:{analysisSummary.abcDistribution.B || 0}, C:{analysisSummary.abcDistribution.C || 0}
                      </Typography>
                    )}
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Servis seviyesi: <strong>%{analysisSummary.avgServiceLevel.toFixed(0)}</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#1f4e79' }}>
                      Önerilen toplam SS: <strong>{analysisSummary.totalRecommendedSS.toLocaleString()}</strong> birim
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.7rem', color: '#1f4e79' }}>
                      ⚠️ Yüksek risk: <strong>{analysisSummary.highRiskCount}</strong> ürün
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* ✅ 6 FARKLI SS METODU */}
      <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#fafcff', border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Card sx={{ mb: 2, borderRadius: 2, bgcolor: '#f0f7ff', border: '1px solid #d0e0ff' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Lightbulb sx={{ fontSize: 20, color: '#1f4e79', mt: 0.25 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem' }}>
                    🧠 Stokonomi Akıllı Analiz Motoru
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#374151', mt: 0.5 }}>
                    Stokonomi, her malzeme için <strong>6 SS yöntemi</strong> + <strong>ABC/XYZ analizi</strong> + <strong>Sezonsallık</strong> + <strong>Trend</strong> + <strong>Intermittent Talep</strong> kontrollerini yapar. 
                    Tüm verileri değerlendirerek <strong>en uygun SS metodunu otomatik önerir</strong> ve <strong>AI destekli yorum</strong> sunar.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Grid container spacing={1.5}>
            {methodDetails.map((method) => (
              <Grid size={{ xs: 6, sm: 4, md: 2 }} key={method.key}>
                <Tooltip
                  title={<MethodTooltip method={method} />}
                  arrow
                  placement="bottom"
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
                        zIndex: 9999,
                      },
                    },
                    popper: {
                      sx: { zIndex: 9999 },
                    },
                  }}
                >
                  <Paper
                    sx={{
                      p: 1,
                      textAlign: 'center',
                      bgcolor: method.isRecommended ? alpha('#1f4e79', 0.06) : 'white',
                      border: method.isRecommended ? '2px solid #1f4e79' : '1px solid #e8f0fe',
                      borderRadius: 2,
                      cursor: 'default',
                      transition: 'all 0.2s',
                      position: 'relative',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                        borderColor: method.isRecommended ? '#1f4e79' : '#b0b0b0',
                      },
                    }}
                  >
                    {method.isRecommended && (
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
                      {method.icon}
                      <Typography variant="caption" sx={{ fontWeight: method.isRecommended ? 700 : 500, fontSize: '0.65rem' }}>
                        {method.label}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ fontSize: '0.55rem', color: method.isRecommended ? '#1f4e79' : '#6b7280', display: 'block', mt: 0.25, fontWeight: method.isRecommended ? 500 : 400 }}>
                      {method.short}
                    </Typography>
                    {method.isRecommended && (
                      <Box sx={{ mt: 0.5, height: 2, bgcolor: '#1f4e79', borderRadius: 1, width: '60%', mx: 'auto' }} />
                    )}
                  </Paper>
                </Tooltip>
              </Grid>
            ))}
          </Grid>

          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Chip icon={<Category sx={{ fontSize: 14 }} />} label="ABC/XYZ Sınıflandırması" size="small" color="primary" variant="outlined" />
            <Chip icon={<Timeline sx={{ fontSize: 14 }} />} label="Sezonsallık + Trend Analizi" size="small" color="secondary" variant="outlined" />
            <Chip icon={<Warning sx={{ fontSize: 14 }} />} label="Intermittent Talep Kontrolü" size="small" color="warning" variant="outlined" />
            <Chip icon={<Psychology sx={{ fontSize: 14 }} />} label="AI Destekli Yorum" size="small" color="info" variant="outlined" />
            <Chip icon={<Assessment sx={{ fontSize: 14 }} />} label="Risk Skoru" size="small" color="error" variant="outlined" />
          </Box>

          <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center' }}>
            <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', textAlign: 'center' }}>
              💡 Analiz sırasında altı yöntemin tamamı + ABC/XYZ + sezonsallık + trend hesaplanır. 
              En uygun yöntem otomatik seçilir ve AI yorumu ile desteklenir.
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Sonuçlar Tablosu */}
      {results.length > 0 ? (
        <Card sx={{ borderRadius: 2 }}>
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
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>ABC</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>XYZ</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }}>Pattern</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">CV</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="right">Hibrit</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Önerilen</TableCell>
                    <TableCell sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79' }} align="center">Risk</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => {
                    const best = getBestMethod(result);
                    
                    return (
                      <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#f8faff' } }}>
                        <TableCell sx={{ fontSize: '0.7rem' }}>{result.material_code}</TableCell>
                        <TableCell>
                          <Chip 
                            label={result.abc || '-'} 
                            size="small" 
                            color={(result.abc_color as any) || 'default'}
                            sx={{ height: 18, fontSize: '0.55rem', fontWeight: 'bold' }}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={result.xyz || '-'} 
                            size="small" 
                            color={(result.xyz_color as any) || 'default'}
                            sx={{ height: 18, fontSize: '0.55rem', fontWeight: 'bold' }}
                          />
                        </TableCell>
                        <TableCell>
                          <Tooltip title={`CV: ${result.cv}, Zero Ratio: ${result.zero_ratio}`} arrow>
                            <Chip
                              label={`${result.pattern_label}`}
                              size="small"
                              color={getPatternColor(result.pattern_color)}
                              variant="outlined"
                              sx={{ height: 20, fontSize: '0.55rem' }}
                            />
                          </Tooltip>
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.7rem' }}>{result.cv.toFixed(3)}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', color: '#1f4e79', fontSize: '0.7rem' }}>
                          {result.hybrid_ss?.toFixed(0) || '-'}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={result.recommended_method_label || methodLabelsFull[best] || best}
                            size="small"
                            color={result.recommended_method === best ? 'success' : 'default'}
                            sx={{ height: 20, fontSize: '0.55rem' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={result.risk_level || 'Düşük'}
                            size="small"
                            color={result.risk_level === 'Yüksek' ? 'error' : result.risk_level === 'Orta' ? 'warning' : 'success'}
                            sx={{ height: 18, fontSize: '0.5rem' }}
                          />
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
              <Security sx={{ fontSize: 40, color: '#b0b0b0', mb: 1 }} />
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

      {/* Geçmiş Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
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
                            <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>{dateStr}</Typography>
                            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#9e9e9e' }}>{timeStr}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ fontSize: '0.7rem', fontWeight: 500 }}>{item.data?.report_name || 'Emniyet Stoğu Analizi'}</TableCell>
                        <TableCell align="center" sx={{ fontSize: '0.7rem', fontWeight: 600 }}>{item.data?.total || 0}</TableCell>
                        <TableCell align="center">
                          <Chip label={statusInfo.label} size="small" color={statusInfo.color as any} sx={{ height: 20, fontSize: '0.55rem' }} />
                        </TableCell>
                        <TableCell align="right">
                          <Button size="small" variant="outlined" onClick={() => handleViewHistory(item)} startIcon={<Visibility sx={{ fontSize: 14 }} />} sx={{ fontSize: '0.6rem', textTransform: 'none' }}>
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