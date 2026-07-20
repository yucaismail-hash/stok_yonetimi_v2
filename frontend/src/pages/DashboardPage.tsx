// frontend/src/pages/DashboardPage.tsx - TAM GÜNCEL DOSYA (AI Özeti Yenile Butonu KALDIRILDI)

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Stack,
  Skeleton,
  Snackbar,
} from '@mui/material';
import {
  Assessment,
  CheckCircle,
  Info,
  Inventory,
  Visibility,
  CloudUpload,
  InsertDriveFile,
  Clear,
  UploadFile,
  Payments,
  Close,
  CancelOutlined,
  ErrorOutlined,
  Download,
  PlayArrow,
  Schedule,
  AccountBalanceWallet,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { styled } from '@mui/material/styles';
import PolarCheckout from '../components/PolarCheckout';
import {
  Shield,
  TrendingUp as TrendingUpLucide,
  Dice5,
  School,
  Truck,
  Download as DownloadLucide,
  Lightbulb as LightbulbLucide,
} from 'lucide-react';

// ✅ Activity Interface
interface Activity {
  id: number;
  type: string;
  message: string;
  time: string;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
  raw?: any;
}

// ✅ Task Interface
interface Task {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  total_materials: number;
  completed_materials: number;
  result_type: string;
  report_name: string;
}

// ✅ AI Önerisi Interface
interface AIRecommendationData {
  has_recommendation: boolean;
  summary: string;
  details?: string[];
  last_analysis_date?: string | null;
  confidence: number;
  action?: string;
  action_path?: string;
}

// ✅ Credit Package Interface
interface CreditPackage {
  id: number;
  polar_product_id: string;
  name: string;
  credits: number;
  price_tl: number;
  is_active: boolean;
}

// 📁 Styled Upload Area
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const UploadArea = styled(Paper)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.spacing(2),
  padding: theme.spacing(2),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s',
  backgroundColor: '#f8faff',
  minHeight: 100,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  '&:hover': {
    backgroundColor: '#f0f7ff',
    borderColor: '#1f4e79',
  },
  '&.dragging': {
    backgroundColor: '#e3f2fd',
    borderColor: '#1f4e79',
    transform: 'scale(1.02)',
  },
}));

// 📊 Hızlı İstatistik Kartı
interface QuickStatProps {
  value: number;
  label: string;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

const QuickStat = ({ value, label, icon, color, loading }: QuickStatProps) => (
  <Paper
    sx={{
      px: 1.5,
      py: 1,
      display: 'flex',
      alignItems: 'center',
      gap: 1.5,
      backgroundColor: '#fafcff',
      border: '1px solid #e8f0fe',
      borderRadius: 2,
    }}
  >
    <Avatar sx={{ bgcolor: color, width: 28, height: 28 }}>{icon}</Avatar>
    <Box>
      {loading ? (
        <Skeleton variant="text" width={40} height={24} />
      ) : (
        <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
          {value.toLocaleString('tr-TR')}
        </Typography>
      )}
      <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem', display: 'block', lineHeight: 1 }}>
        {label}
      </Typography>
    </Box>
  </Paper>
);

// 📋 Hızlı Analiz Kartı
interface QuickAnalysisCardProps {
  title: string;
  icon: React.ReactNode;
  color: string;
  cost: number;
  onClick: () => void;
  isAsync?: boolean;
  loading?: boolean;
}

const QuickAnalysisCard = ({ title, icon, color, cost, onClick, isAsync, loading }: QuickAnalysisCardProps) => (
  <Card
    sx={{
      cursor: loading ? 'default' : 'pointer',
      transition: 'all 0.2s',
      '&:hover': {
        transform: loading ? 'none' : 'translateY(-2px)',
        boxShadow: loading ? 0 : 2,
      },
      border: '1px solid #e8f0fe',
      borderRadius: 2,
      opacity: loading ? 0.7 : 1,
    }}
    onClick={loading ? undefined : onClick}
  >
    <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 1.5, px: 2 }}>
      <Avatar sx={{ bgcolor: color, width: 32, height: 32 }}>{icon}</Avatar>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.8rem' }}>
          {loading ? <Skeleton variant="text" width={60} /> : title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
          {loading ? (
            <Skeleton variant="text" width={40} height={14} />
          ) : (
            <>
              <Chip label={`${cost} Kredi`} size="small" sx={{ height: 16, fontSize: '0.5rem' }} />
              {isAsync && <Chip label="ASYNC" size="small" color="secondary" sx={{ height: 16, fontSize: '0.45rem' }} />}
            </>
          )}
        </Box>
      </Box>
      {!loading && <PlayArrow sx={{ color: '#9e9e9e', fontSize: 16 }} />}
    </CardContent>
  </Card>
);

// 🤖 AI Executive Summary - KOMPAKT
const AIExecutiveSummary = ({
  recommendation,
  loading
}: {
  recommendation: AIRecommendationData | null;
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

  if (!recommendation || !recommendation.has_recommendation) {
    return (
      <Card sx={{ bgcolor: '#f8faff', border: '1px solid #e8f0fe', height: '100%' }}>
        <CardContent sx={{ py: 1.5, px: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LightbulbLucide size={18} color="#6b7280" />
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
              AI Yönetici Özeti
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
            <LightbulbLucide size={16} color="white" />
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.8rem' }}>
                🤖 AI Özet
              </Typography>
              {recommendation.last_analysis_date && (
                <Chip
                  label={recommendation.last_analysis_date}
                  size="small"
                  sx={{ height: 18, fontSize: '0.5rem', bgcolor: 'white' }}
                />
              )}
            </Box>
            <Typography variant="body2" sx={{ color: '#1f4e79', fontSize: '0.75rem', mt: 0.25 }}>
              {recommendation.summary}
            </Typography>
            {recommendation.action && (
              <Button
                variant="text"
                size="small"
                onClick={() => window.location.href = recommendation.action_path || '/tasks'}
                sx={{ mt: 0.5, p: 0, fontSize: '0.65rem', color: '#1f4e79', fontWeight: 600, textTransform: 'none' }}
              >
                {recommendation.action} →
              </Button>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

// 💳 Kredi Satın Alma Dialog
const CreditPurchaseDialog = ({
  open,
  onClose,
  onPurchase,
  currentBalance,
  isLoading = false,
  paymentStatus = 'idle',
  paymentMessage = null,
  onReset,
}: {
  open: boolean;
  onClose: () => void;
  onPurchase: (pkg: CreditPackage) => void;
  currentBalance: number;
  isLoading?: boolean;
  paymentStatus?: 'idle' | 'processing' | 'success' | 'canceled' | 'error';
  paymentMessage?: string | null;
  onReset?: () => void;
}) => {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<CreditPackage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && paymentStatus === 'idle') {
      fetchPackages();
    }
  }, [open, paymentStatus]);

  const fetchPackages = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/polar/packages');
      if (res.data && Array.isArray(res.data)) {
        setPackages(res.data);
        if (res.data.length > 0) {
          setSelectedPackage(res.data[0]);
        }
      }
    } catch (error) {
      console.error('❌ Paket hatası:', error);
      setError('Paketler yüklenirken bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = () => {
    if (!selectedPackage) return;
    onPurchase(selectedPackage);
  };

  const handleClose = () => {
    setError(null);
    if (onReset) onReset();
    onClose();
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 3, fontWeight: 'bold', color: 'primary.main' }}>
            🚀 Ödeme Başlatılıyor...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Lütfen bekleyin, güvenli ödeme sayfası açılıyor.
          </Typography>
        </Box>
      );
    }

    if (paymentStatus === 'success') {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main' }}>
            🎉 Ödeme Başarılı!
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            {paymentMessage || 'Kredileriniz hesabınıza başarıyla eklendi.'}
          </Typography>
          <Chip
            label={`💰 Yeni Bakiye: ${currentBalance} Kredi`}
            color="success"
            sx={{ mt: 2, fontWeight: 'bold' }}
          />
        </Box>
      );
    }

    if (paymentStatus === 'canceled') {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CancelOutlined sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
            ⏹️ Ödeme İptal Edildi
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            {paymentMessage || 'Ödeme işleminiz iptal edildi. Herhangi bir ücret alınmamıştır.'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Tekrar denemek için "Tekrar Dene" butonunu kullanabilirsiniz.
          </Typography>
        </Box>
      );
    }

    if (paymentStatus === 'error') {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <ErrorOutlined sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'error.main' }}>
            ❌ Ödeme Alınamadı
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            {paymentMessage || 'Ödeme işlemi sırasında bir hata oluştu.'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Lütfen tekrar deneyin veya farklı bir ödeme yöntemi kullanın.
          </Typography>
        </Box>
      );
    }

    return (
      <>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Aşağıdaki paketlerden birini seçerek kredi satın alabilirsiniz.
          Ödeme işlemi güvenli ödeme platformu Polar üzerinden gerçekleştirilir.
        </Typography>

        <Grid container spacing={2}>
          {packages.map((pkg) => (
            <Grid size={{ xs: 12, sm: 4 }} key={pkg.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: selectedPackage?.id === pkg.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                  transition: 'all 0.3s ease',
                  borderRadius: 3,
                  position: 'relative',
                  overflow: 'hidden',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 8,
                  },
                  ...(selectedPackage?.id === pkg.id && {
                    boxShadow: '0 8px 25px rgba(25, 118, 210, 0.25)',
                  }),
                }}
                onClick={() => setSelectedPackage(pkg)}
              >
                {selectedPackage?.id === pkg.id && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      right: 0,
                      bgcolor: 'success.main',
                      color: 'white',
                      px: 2,
                      py: 0.5,
                      borderRadius: '0 0 0 12px',
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                    }}
                  >
                    SEÇİLDİ
                  </Box>
                )}
                <CardContent sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {pkg.credits}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Kredi
                  </Typography>

                  <Divider sx={{ my: 1.5 }} />

                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1a237e' }}>
                    ₺{pkg.price_tl.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {pkg.name}
                  </Typography>

                  {selectedPackage?.id === pkg.id && (
                    <CheckCircle sx={{ color: 'success.main', mt: 1 }} />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {selectedPackage && (
          <Paper
            sx={{
              mt: 3,
              p: 2.5,
              bgcolor: '#e3f2fd',
              borderRadius: 3,
              border: '1px solid #90caf9',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
              }}
            >
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                  📋 Seçilen Paket: {selectedPackage.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedPackage.credits} Kredi
                </Typography>
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                ₺{selectedPackage.price_tl.toFixed(2)}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              🔒 Güvenli ödeme Polar tarafından sağlanmaktadır.
            </Typography>
          </Paper>
        )}
      </>
    );
  };

  const renderActions = () => {
    if (isLoading) {
      return (
        <>
          <Button disabled>İptal</Button>
          <Button disabled variant="contained">
            <CircularProgress size={20} sx={{ mr: 1 }} />
            İşlem Devam Ediyor...
          </Button>
        </>
      );
    }

    if (paymentStatus === 'success' || paymentStatus === 'canceled') {
      return (
        <>
          <Button variant="contained" color="primary" onClick={handleClose}>
            {paymentStatus === 'success' ? "Dashboard'a Dön" : 'Tekrar Dene'}
          </Button>
        </>
      );
    }

    if (paymentStatus === 'error') {
      return (
        <>
          <Button onClick={handleClose}>Vazgeç</Button>
          <Button variant="contained" color="warning" onClick={onReset}>
            Tekrar Dene
          </Button>
        </>
      );
    }

    return (
      <>
        <Button
          onClick={handleClose}
          sx={{
            color: '#666',
            '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' },
          }}
        >
          İptal
        </Button>
        <Button
          variant="contained"
          onClick={handlePurchase}
          disabled={!selectedPackage || loading}
          startIcon={<Payments />}
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #0d47a1 0%, #1a237e 100%)',
            },
            '&:disabled': {
              background: '#ccc',
            },
          }}
        >
          Satın Al
        </Button>
      </>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={paymentStatus === 'idle' ? handleClose : undefined}
      maxWidth="sm"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
            overflow: 'hidden',
            minHeight: 400,
          },
        },
      }}
    >
      <Box
        sx={{
          p: 3,
          background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
          color: 'white',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
              {paymentStatus === 'success'
                ? '✅ Ödeme Başarılı'
                : paymentStatus === 'canceled'
                  ? '⏹️ Ödeme İptal'
                  : paymentStatus === 'error'
                    ? '❌ Ödeme Hatası'
                    : '💳 Kredi Satın Al'}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              {paymentStatus === 'success'
                ? 'Kredileriniz hesabınıza eklendi.'
                : paymentStatus === 'canceled'
                  ? 'İşleminiz iptal edildi.'
                  : paymentStatus === 'error'
                    ? 'Bir hata oluştu, tekrar deneyin.'
                    : 'İhtiyacın olan krediyi seç, hemen kullanmaya başla'}
            </Typography>
          </Box>
          {paymentStatus === 'idle' && (
            <IconButton onClick={handleClose} size="small" sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          )}
        </Box>
        {paymentStatus === 'idle' && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={`💰 Mevcut: ${currentBalance} Kredi`}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                fontWeight: 'bold',
              }}
            />
          </Box>
        )}
      </Box>

      <DialogContent sx={{ p: 3, bgcolor: '#f8f9fa' }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading && paymentStatus === 'idle' ? (
          <Box sx={{ textAlign: 'center', py: 4 }}> 
            <CircularProgress />
          </Box>
        ) : (
          renderContent()
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, bgcolor: '#f8f9fa', borderTop: '1px solid #e0e0e0' }}>
        {renderActions()}
      </DialogActions>
    </Dialog>
  );
};

// 📌 Ana Dashboard Component
export default function DashboardPage() {
  const { user, fetchUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [creditDialogOpen, setCreditDialogOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [lastUploadedFile, setLastUploadedFile] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<CreditPackage | null>(null);
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'canceled' | 'error'>('idle');
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [costs, setCosts] = useState<Record<string, number>>({});
  const [costsLoading, setCostsLoading] = useState(true);
  const [aiRecommendation, setAiRecommendation] = useState<AIRecommendationData | null>(null);
  const [aiLoading, setAiLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [userStats, setUserStats] = useState({
    tokenBalance: 0,
    totalMaterials: 0,
    totalAnalyses: 0,
    pendingTasks: 0,
    completedTasks: 0,
  });

  // ✅ AI durumu için polling
  const [hasPendingAnalysis, setHasPendingAnalysis] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  // ✅ Tüm verileri yükle
  const loadAllData = useCallback(async () => {
    if (dataLoaded) return;
    setLoading(true);
    try {
      await Promise.all([
        fetchCosts(),
        fetchAIExecutiveSummary(),
        fetchTasks(),
        fetchActivities(),
        fetchStats(),
      ]);
      setDataLoaded(true);
    } catch (error) {
      console.error('❌ Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  }, [dataLoaded]);

  useEffect(() => {
    if (user && !dataLoaded) {
      loadAllData();
    }
  }, [user, dataLoaded]);

  // ✅ Maliyetleri getir
  const fetchCosts = async () => {
    setCostsLoading(true);
    try {
      const endpoints = [
        '/api/forecast/batch',
        '/api/safety-stock',
        '/api/simulate',
        '/api/backtest',
        '/api/supplier/optimize-shares'
      ];
      const costMap: Record<string, number> = {};
      for (const endpoint of endpoints) {
        try {
          const res = await api.get('/api/cost', {
            params: { endpoint, method: 'POST' }
          });
          const key = endpoint.replace('/api/', '').split('/')[0];
          costMap[key] = res.data.cost || 5;
        } catch (e) {
          costMap[endpoint] = 5;
        }
      }
      setCosts(costMap);
    } catch (error) {
      console.error('❌ Maliyet hatası:', error);
    } finally {
      setCostsLoading(false);
    }
  };

  // ✅ AI Executive Summary - Dashboard'dan al
  const fetchAIExecutiveSummary = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await api.get('/api/dashboard/ai-summary');
      console.log('🔍 AI Dashboard Özeti:', res.data);
      
      if (res.data.has_data && res.data.summary) {
        const summary = res.data.summary;
        
        // Dashboard'dan gelen özeti kullan
        let summaryText = summary.manager_summary || summary.summary || 'Analizleriniz başarıyla tamamlandı.';
        
        // Eğer özet çok uzunsa kısalt
        if (summaryText.length > 200) {
          summaryText = summaryText.substring(0, 197) + '...';
        }
        
        // Detayları hazırla
        const details = summary.recommended_actions || [];
        if (summary.critical_materials && summary.critical_materials.length > 0) {
          details.push(`⚠️ Kritik ürünler: ${summary.critical_materials.join(', ')}`);
        }
        
        // İstatistikleri ekle
        if (summary.statistics) {
          const stats = summary.statistics;
          if (stats.total_analyses) {
            details.push(`📊 ${stats.total_analyses} analiz tamamlandı`);
          }
          if (stats.total_materials) {
            details.push(`📦 ${stats.total_materials} ürün analiz edildi`);
          }
        }
        
        setAiRecommendation({
          has_recommendation: true,
          summary: summaryText,
          details: details.length > 0 ? details : undefined,
          last_analysis_date: res.data.last_analysis_date ? new Date(res.data.last_analysis_date).toLocaleDateString('tr-TR') : 'Bugün',
          confidence: 0.85,
          action: "Detaylı Raporları Gör",
          action_path: "/tasks"
        });
      } else {
        setAiRecommendation({
          has_recommendation: false,
          summary: "Henüz AI özeti oluşturulmamış. Analiz yaptıkça burada özetler görünecek.",
          last_analysis_date: null,
          confidence: 0,
        });
      }
    } catch (error) {
      console.error('❌ AI özet hatası:', error);
      setAiRecommendation({
        has_recommendation: false,
        summary: "AI özeti alınamadı. Lütfen daha sonra tekrar deneyin.",
        last_analysis_date: null,
        confidence: 0,
      });
    } finally {
      setAiLoading(false);
    }
  }, []);

  // ✅ AI durumu kontrolü (polling)
  const checkAIStatus = useCallback(async () => {
    try {
      const res = await api.get('/api/dashboard/ai-summary/status');
      if (res.data.is_completed) {
        // Tamamlandı, özeti yenile
        setHasPendingAnalysis(false);
        await fetchAIExecutiveSummary();
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      } else if (res.data.ai_status === 'failed') {
        setHasPendingAnalysis(false);
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      }
    } catch (error) {
      console.error('❌ AI durum kontrol hatası:', error);
    }
  }, [fetchAIExecutiveSummary, pollingInterval]);

  // ✅ AI durumunu kontrol et (polling)
  useEffect(() => {
    let intervalId: number | null = null;
    if (hasPendingAnalysis) {
      intervalId = setInterval(checkAIStatus, 5000);
      setPollingInterval(intervalId);
      setTimeout(() => {
        if (intervalId) {
          clearInterval(intervalId);
          setPollingInterval(null);
          setHasPendingAnalysis(false);
        }
      }, 120000); // 2 dakika timeout
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        setPollingInterval(null);
      }
    };
  }, [hasPendingAnalysis]);

  // ✅ Görevleri getir
  const fetchTasks = async () => {
    setTasksLoading(true);
    try {
      const res = await api.get('/api/tasks/async');
      if (res.data.success) {
        setTasks(res.data.tasks || []);
      }
    } catch (error) {
      console.error('❌ Görev hatası:', error);
      setTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  // ✅ İstatistikleri getir
  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const balance = user?.token_balance || 0;
      const uploadRes = await api.get('/api/upload/status');
      const totalMaterials = uploadRes.data.materials_count || 0;
      const lastFile = uploadRes.data.last_filename || null;
      setLastUploadedFile(lastFile);
      const historyRes = await api.get('/api/upload/results', {
        params: { limit: 100 },
      });
      const totalAnalyses = historyRes.data.total || 0;
      const tasksRes = await api.get('/api/tasks/async');
      const tasks = tasksRes.data.tasks || [];
      const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;
      const pendingTasks = tasks.filter((t: any) => t.status === 'pending' || t.status === 'processing').length;

      setUserStats({
        tokenBalance: balance,
        totalMaterials,
        totalAnalyses,
        completedTasks,
        pendingTasks,
      });
    } catch (error) {
      console.error('❌ Dashboard istatistik hatası:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  // ✅ Aktiviteleri getir
  const fetchActivities = async () => {
    try {
      const res = await api.get('/api/upload/results', {
        params: { limit: 100 },
      });

      const results = res.data.results || [];
      const activityList: Activity[] = results.map((item: any, index: number) => {
        const typeMap: Record<string, string> = {
          'forecast_batch': 'Talep Tahmini',
          'forecast_batch_async': 'Talep Tahmini',
          'safety_stock_batch': 'Emniyet Stoğu',
          'safety_stock_batch_async': 'Emniyet Stoğu',
          'simulation_batch': 'Monte Carlo Simülasyonu',
          'simulation_batch_async': 'Monte Carlo Simülasyonu',
          'backtest_batch': 'Backtest',
          'backtest_batch_async': 'Backtest',
          'supplier_batch': 'Tedarikçi Analizi',
          'supplier_batch_async': 'Tedarikçi Analizi',
        };
        const type = typeMap[item.result_type] || item.result_type || 'Analiz';

        let totalMaterials = 0;
        if (item.result_data?.total) {
          totalMaterials = item.result_data.total;
        } else if (item.result_data?.results && Array.isArray(item.result_data.results)) {
          totalMaterials = item.result_data.results.length;
        } else if (item.results && Array.isArray(item.results)) {
          totalMaterials = item.results.length;
        } else if (item.total) {
          totalMaterials = item.total;
        }

        const materialText = totalMaterials > 0 ? `${totalMaterials} malzeme` : '';
        let message = `${type} tamamlandı`;
        if (materialText) {
          message = `${type} - ${materialText}`;
        }

        return {
          id: index,
          type: item.result_type || 'analysis',
          message: message,
          time: new Date(item.created_at).toLocaleString('tr-TR'),
          status: 'success' as const,
          details: item.result_type || 'Analiz',
          raw: item,
        };
      });

      activityList.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

      setAllActivities(activityList);
      setActivities(activityList.slice(0, 5));

    } catch (error) {
      console.error('❌ Aktivite hatası:', error);
      setAllActivities([]);
      setActivities([]);
    }
  };

  // ✅ Verileri yenile
  const refreshData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchStats(),
        fetchTasks(),
        fetchAIExecutiveSummary(),
        fetchActivities(),
      ]);
    } catch (error) {
      console.error('❌ Veri yenileme hatası:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ Upload başarılı olduğunda verileri yenile
  useEffect(() => {
    if (uploadSuccess) {
      refreshData();
    }
  }, [uploadSuccess]);

  // ✅ Ödeme başarılı olduğunda verileri yenile
  useEffect(() => {
    if (paymentStatus === 'success') {
      refreshData();
    }
  }, [paymentStatus]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(false);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Lütfen bir dosya seçin.');
      return;
    }

    setUploading(true);
    setUploadProgress(10);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadProgress(30);
      const response = await api.post('/api/upload?mode=quick', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(30 + percent * 0.6);
          }
        },
      });

      setUploadProgress(100);

      if (response.data.success) {
        setUploadSuccess(true);
        setLastUploadedFile(selectedFile.name);
        // AI özeti yenilemek için hasPendingAnalysis true yap
        setHasPendingAnalysis(true);
        await fetchUser();
        setTimeout(() => setUploadSuccess(false), 5000);
      } else {
        setUploadError(response.data.error || 'Dosya yüklenirken hata oluştu.');
      }
    } catch (err: any) {
      console.error('❌ Upload hatası:', err);
      setUploadError(err.response?.data?.detail || 'Dosya yüklenirken hata oluştu.');
    } finally {
      setUploading(false);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      handleFileSelect(event.target.files[0]);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // ✅ Excel Şablonu İndir
  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/api/upload/template', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'stokonomi_sablon.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMessage('✅ Şablon başarıyla indirildi!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('❌ Şablon indirme hatası:', err);
      setUploadError('Şablon indirilemedi.');
    }
  };

  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  // ✅ Analizler için maliyetleri al
  const getCost = (key: string) => {
    const costMap: Record<string, string> = {
      'safety-stock': 'safety-stock',
      'forecast': 'forecast',
      'simulation': 'simulate',
      'backtest': 'backtest',
      'supplier': 'supplier/optimize-shares',
    };
    const endpoint = costMap[key] || key;
    return costs[endpoint] || costs[key] || 5;
  };

  const quickAnalyses = [
    { key: 'safety-stock', title: 'Emniyet Stoğu', icon: <Shield size={18} />, color: '#2e7d32', path: '/safety-stock', isAsync: true },
    { key: 'forecast', title: 'Talep Tahmini', icon: <TrendingUpLucide size={18} />, color: '#1976d2', path: '/forecast', isAsync: true },
    { key: 'simulation', title: 'Simülasyon', icon: <Dice5 size={18} />, color: '#9c27b0', path: '/simulation', isAsync: true },
    { key: 'backtest', title: 'Backtest', icon: <School size={18} />, color: '#ed6c02', path: '/backtest', isAsync: true },
    { key: 'supplier', title: 'Tedarikçi', icon: <Truck size={18} />, color: '#d32f2f', path: '/supplier', isAsync: true },
  ];

  const pendingTasks = tasks.filter(t => t.status === 'pending' || t.status === 'processing');
  const completedTasksList = tasks.filter(t => t.status === 'completed');

  // ✅ Checkout işlemleri
  const handlePurchase = async (pkg: CreditPackage) => {
    setSelectedProduct(pkg);
    setIsCreatingCheckout(true);
    setPaymentStatus('processing');
    setPaymentMessage('Ödeme başlatılıyor, lütfen bekleyin...');

    try {
      const res = await api.post('/api/polar/checkout', {
        product_id: pkg.polar_product_id,
      });

      if (res.data && res.data.checkout_url) {
        const checkoutUrl = new URL(res.data.checkout_url);
        checkoutUrl.searchParams.set('embed_origin', window.location.origin);
        setCheckoutUrl(checkoutUrl.toString());
        setCheckoutOpen(true);
        setIsCreatingCheckout(false);
      } else {
        setPaymentStatus('error');
        setPaymentMessage('Ödeme linki oluşturulamadı.');
        setIsCreatingCheckout(false);
      }
    } catch (err: any) {
      console.error('❌ Checkout hatası:', err);
      setPaymentStatus('error');
      setPaymentMessage(err.response?.data?.detail || 'Ödeme başlatılamadı.');
      setIsCreatingCheckout(false);
    }
  };

  const handleCheckoutSuccess = () => {
    fetchUser();
    setCheckoutOpen(false);
    setCreditDialogOpen(false);
    setPaymentStatus('success');
    setPaymentMessage('Kredileriniz hesabınıza başarıyla eklendi!');
    setSuccessMessage('✅ Krediler başarıyla eklendi!');
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const handleCheckoutCancel = () => {
    setCheckoutOpen(false);
    setCreditDialogOpen(false);
    setPaymentStatus('canceled');
    setPaymentMessage('Ödeme işleminiz iptal edildi.');
  };

  const handlePaymentReset = () => {
    setPaymentStatus('idle');
    setPaymentMessage(null);
    setCheckoutOpen(false);
    setCheckoutUrl('');
    setSelectedProduct(null);
  };

  // ✅ URL'deki checkout_id'yi yakala
  useEffect(() => {
    const checkPaymentStatus = async () => {
      const params = new URLSearchParams(window.location.search);
      const checkoutId = params.get('checkout_id');

      if (checkoutId) {
        try {
          const res = await api.get(`/api/polar/transaction/${checkoutId}`);
          if (res.data) {
            setPaymentStatus('success');
            setPaymentMessage(`${res.data.credits} kredi hesabınıza eklendi!`);
            setCreditDialogOpen(true);
            setSuccessMessage(`✅ ${res.data.credits} kredi eklendi!`);
            setTimeout(() => setSuccessMessage(null), 5000);
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } catch (error: any) {
          if (error.response?.status === 404) {
            setPaymentStatus('canceled');
            setPaymentMessage('Ödeme işleminiz iptal edildi.');
            setCreditDialogOpen(true);
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        }
      }
    };
    checkPaymentStatus();
  }, []);

  // ✅ Sayfalandırılmış aktiviteler
  const paginatedActivities = allActivities.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      <CreditPurchaseDialog
        open={creditDialogOpen}
        onClose={() => {
          setCreditDialogOpen(false);
          setPaymentStatus('idle');
          setPaymentMessage(null);
        }}
        onPurchase={handlePurchase}
        currentBalance={user?.token_balance || 0}
        isLoading={isCreatingCheckout}
        paymentStatus={paymentStatus}
        paymentMessage={paymentMessage}
        onReset={handlePaymentReset}
      />

      <PolarCheckout
        open={checkoutOpen}
        onClose={() => setCheckoutOpen(false)}
        onSuccess={handleCheckoutSuccess}
        onCancel={handleCheckoutCancel}
        checkoutUrl={checkoutUrl}
        productName={selectedProduct?.name || 'Kredi Paketi'}
      />

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* ✅ 1. HERO ALANI - İKİ SÜTUN: YÜKLEME + AI ÖZET */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {/* Sol: Excel Yükleme */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CloudUpload sx={{ fontSize: 18, color: '#1f4e79' }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  Excel Yükle
                </Typography>
                <Chip label=".xlsx .xls" size="small" sx={{ height: 18, fontSize: '0.5rem' }} />
              </Box>

              <UploadArea
                className={isDragging ? 'dragging' : ''}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                sx={{ py: 1.5, minHeight: 80 }}
              >
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                  {selectedFile ? (
                    <>
                      <InsertDriveFile sx={{ fontSize: 28, color: 'primary.main' }} />
                      <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                        {selectedFile.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </Typography>
                      <Stack direction="row" spacing={0.5}>
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<UploadFile sx={{ fontSize: 14 }} />}
                          onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                          disabled={uploading}
                          sx={{ fontSize: '0.6rem', py: 0.5 }}
                        >
                          {uploading ? 'Yükleniyor...' : 'Yükle'}
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          color="error"
                          startIcon={<Clear sx={{ fontSize: 14 }} />}
                          onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                          disabled={uploading}
                          sx={{ fontSize: '0.6rem', py: 0.5 }}
                        >
                          İptal
                        </Button>
                      </Stack>
                    </>
                  ) : (
                    <>
                      <CloudUpload sx={{ fontSize: 32, color: '#1f4e79' }} />
                      <Typography variant="body2" sx={{ fontWeight: 500, color: '#1f4e79', fontSize: '0.75rem' }}>
                        Dosyayı Sürükle veya Tıkla
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                        <Button
                          variant="text"
                          size="small"
                          startIcon={<DownloadLucide size={14} />}
                          onClick={(e) => { e.stopPropagation(); handleDownloadTemplate(); }}
                          sx={{ fontSize: '0.6rem', color: '#1f4e79' }}
                        >
                          Şablon
                        </Button>
                        {lastUploadedFile && (
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                            Son: {lastUploadedFile}
                          </Typography>
                        )}
                      </Stack>
                    </>
                  )}
                </Box>
              </UploadArea>

              <VisuallyHiddenInput
                type="file"
                accept=".xlsx,.xls"
                ref={fileInputRef}
                onChange={handleFileInputChange}
              />

              {uploading && (
                <Box sx={{ mt: 1 }}>
                  <LinearProgress variant="determinate" value={uploadProgress} sx={{ height: 4, borderRadius: 2 }} />
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                    %{uploadProgress}
                  </Typography>
                </Box>
              )}
              {uploadSuccess && (
                <Alert severity="success" sx={{ mt: 1, py: 0.5, fontSize: '0.65rem' }} onClose={() => setUploadSuccess(false)}>
                  ✅ Dosya yüklendi!
                </Alert>
              )}
              {uploadError && (
                <Alert severity="error" sx={{ mt: 1, py: 0.5, fontSize: '0.65rem' }} onClose={() => setUploadError(null)}>
                  {uploadError}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sağ: AI Yönetici Özeti */}
        <Grid size={{ xs: 12, md: 6 }}>
          <AIExecutiveSummary
            recommendation={aiRecommendation}
            loading={aiLoading}
          />
        </Grid>
      </Grid>

      {/* ✅ 2. HIZLI İSTATİSTİKLER */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={1.5}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <QuickStat
              value={userStats.totalMaterials}
              label="Malzeme"
              icon={<Inventory sx={{ fontSize: 16 }} />}
              color="#1976d2"
              loading={statsLoading}
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <QuickStat
              value={userStats.tokenBalance}
              label="Kredi"
              icon={<AccountBalanceWallet sx={{ fontSize: 16 }} />}
              color="#f9a825"
              loading={statsLoading}
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <QuickStat
              value={userStats.totalAnalyses}
              label="Analiz"
              icon={<Assessment sx={{ fontSize: 16 }} />}
              color="#2e7d32"
              loading={statsLoading}
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <QuickStat
              value={pendingTasks.length}
              label="Devam Eden"
              icon={<Schedule sx={{ fontSize: 16 }} />}
              color="#9c27b0"
              loading={tasksLoading}
            />
          </Grid>
        </Grid>
      </Box>

      {/* ✅ 3. HIZLI BAŞLAT */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1.5, fontSize: '0.85rem' }}>
          ⚡ Hızlı Başlat
        </Typography>
        <Grid container spacing={1.5}>
          {quickAnalyses.map((analysis, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={index}>
              <QuickAnalysisCard
                title={analysis.title}
                icon={analysis.icon}
                color={analysis.color}
                cost={getCost(analysis.key)}
                onClick={() => navigateTo(analysis.path)}
                isAsync={analysis.isAsync}
                loading={costsLoading || loading}
              />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* ✅ 4. SON ANALİZLER & DEVAM EDEN GÖREVLER */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  📋 Son Analizler
                </Typography>
              </Box>
              <Divider sx={{ mb: 1 }} />

              {loading ? (
                <Box sx={{ py: 2 }}>
                  <Skeleton variant="rectangular" height={32} sx={{ mb: 0.5 }} />
                  <Skeleton variant="rectangular" height={32} sx={{ mb: 0.5 }} />
                  <Skeleton variant="rectangular" height={32} />
                </Box>
              ) : allActivities.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Info color="disabled" sx={{ fontSize: 28 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    Henüz analiz yok
                  </Typography>
                </Box>
              ) : (
                <>
                  <List disablePadding>
                    {paginatedActivities.map((activity) => (
                      <ListItem key={activity.id} sx={{ px: 0, py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={activity.message}
                          secondary={activity.time}
                          slotProps={{
                            primary: { variant: 'body2', sx: { fontWeight: 500, fontSize: '0.75rem' } },
                            secondary: { variant: 'caption', sx: { fontSize: '0.6rem' } },
                          }}
                        />
                        <Button size="small" variant="outlined" sx={{ fontSize: '0.6rem', py: 0.5 }}>
                          Aç
                        </Button>
                      </ListItem>
                    ))}
                  </List>
                  <TablePagination
                    component="div"
                    count={allActivities.length}
                    page={page}
                    onPageChange={handleChangePage}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    rowsPerPageOptions={[5, 10, 25]}
                    labelRowsPerPage="Satır:"
                    sx={{
                      '& .MuiTablePagination-select': { fontSize: '0.7rem' },
                      '& .MuiTablePagination-displayedRows': { fontSize: '0.7rem' },
                    }}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card sx={{ height: '100%', borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, px: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1, fontSize: '0.8rem' }}>
                ⏳ Devam Eden Görevler
              </Typography>
              <Divider sx={{ mb: 1 }} />

              {tasksLoading ? (
                <Box sx={{ py: 1 }}>
                  <Skeleton variant="rectangular" height={44} sx={{ mb: 1 }} />
                  <Skeleton variant="rectangular" height={44} sx={{ mb: 1 }} />
                  <Skeleton variant="rectangular" height={44} />
                </Box>
              ) : pendingTasks.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <CheckCircle sx={{ color: 'success.main', fontSize: 28, mb: 0.5 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    Tüm görevler tamamlandı! 🎉
                  </Typography>
                </Box>
              ) : (
                pendingTasks.map((task, index) => (
                  <Box key={task.task_id} sx={{ mb: index < pendingTasks.length - 1 ? 1.5 : 0 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                        {task.report_name}
                      </Typography>
                      <Chip
                        label={`%${task.progress}`}
                        size="small"
                        color={task.status === 'processing' ? 'warning' : 'info'}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={task.progress}
                      sx={{ height: 3, borderRadius: 2, mt: 0.25 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                      {task.message || (task.status === 'processing' ? 'İşleniyor...' : 'Sırada')}
                    </Typography>
                    {index < pendingTasks.length - 1 && <Divider sx={{ mt: 1 }} />}
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}