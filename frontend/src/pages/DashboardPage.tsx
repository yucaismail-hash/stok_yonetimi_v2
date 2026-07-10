import { useState, useEffect, useRef } from 'react';
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
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  ShowChart,
  Security,
  Timeline,
  Backpack,
  LocalShipping,
  Analytics,
  MoreVert,
  CheckCircle,
  Warning,
  Error,
  Info,
  Inventory,
  AttachMoney,
  Visibility,
  CloudUpload,
  InsertDriveFile,
  Clear,
  UploadFile,
  ShoppingCart,
  CreditCard,
  Payments,
  Close,
  CancelOutlined,
  ErrorOutlined,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { useQuery } from '@tanstack/react-query';
import { styled } from '@mui/material/styles';
import PolarCheckout from '../components/PolarCheckout';

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
  padding: theme.spacing(4),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s',
  backgroundColor: theme.palette.background.default,
  '&:hover': {
    backgroundColor: theme.palette.primary.light + '20',
    borderColor: theme.palette.primary.dark,
  },
  '&.dragging': {
    backgroundColor: theme.palette.primary.light + '30',
    borderColor: theme.palette.primary.dark,
    transform: 'scale(1.02)',
  },
}));

// 📊 İstatistik Kartı Bileşeni
interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  loading?: boolean;
}

const StatCard = ({ title, value, icon, color, subtitle, loading }: StatCardProps) => {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              {title}
            </Typography>
            {loading ? (
              <CircularProgress size={24} sx={{ mt: 1 }} />
            ) : (
              <Typography variant="h4" sx={{ fontWeight: 'bold', mt: 0.5 }}>
                {value}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar
            sx={{
              bgcolor: color,
              width: 48,
              height: 48,
              boxShadow: `0 4px 12px ${color}40`,
            }}
          >
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
};

// 📋 Analiz Kartı Bileşeni
interface AnalysisCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  path: string;
  cost: number;
  isAsync?: boolean;
  onClick: () => void;
}

const AnalysisCard = ({ title, description, icon, color, path, cost, isAsync, onClick }: AnalysisCardProps) => {
  return (
    <Card
      sx={{
        height: '100%',
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
          <Avatar sx={{ bgcolor: color, width: 40, height: 40 }}>
            {icon}
          </Avatar>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              {title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
              <Chip
                label={`${cost} Kredi`}
                size="small"
                color="warning"
                sx={{ height: 18, fontSize: '0.6rem' }}
              />
              {isAsync && (
                <Chip
                  label="ASYNC"
                  size="small"
                  color="secondary"
                  sx={{ height: 18, fontSize: '0.6rem' }}
                />
              )}
            </Box>
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {description}
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Chip label="Başlat" size="small" sx={{ bgcolor: color, color: 'white' }} />
        </Box>
      </CardContent>
    </Card>
  );
};

// 📈 Son Aktivite Bileşeni
interface Activity {
  id: number;
  type: string;
  message: string;
  time: string;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
}

const ActivityItem = ({ activity }: { activity: Activity }) => {
  const getIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />;
      case 'warning':
        return <Warning sx={{ color: 'warning.main', fontSize: 16 }} />;
      case 'error':
        return <Error sx={{ color: 'error.main', fontSize: 16 }} />;
      default:
        return <Info sx={{ color: 'info.main', fontSize: 16 }} />;
    }
  };

  return (
    <ListItem sx={{ px: 0 }}>
      <ListItemIcon sx={{ minWidth: 32 }}>
        {getIcon(activity.status)}
      </ListItemIcon>
      <ListItemText
        primary={activity.message}
        secondary={activity.time}
        slotProps={{
          primary: { variant: 'body2' },
          secondary: { variant: 'caption' },
        }}
      />
      {activity.details && (
        <Chip label={activity.details} size="small" variant="outlined" sx={{ ml: 1 }} />
      )}
    </ListItem>
  );
};

// 💳 Kredi Satın Alma Dialog
interface CreditPackage {
  id: number;
  polar_product_id: string;
  name: string;
  credits: number;
  price_tl: number;
  is_active: boolean;
}

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
  const { user, updateUser, fetchUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [creditDialogOpen, setCreditDialogOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<CreditPackage | null>(null);
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false);

  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'canceled' | 'error'>('idle');
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);

  const [activities, setActivities] = useState<Activity[]>([]);
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [showAllActivities, setShowAllActivities] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: userStats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        const balance = user?.token_balance || 0;
        const uploadRes = await api.get('/api/upload/status');
        const totalMaterials = uploadRes.data.materials_count || 0;
        const historyRes = await api.get('/api/upload/results', {
          params: { limit: 100 },
        });
        const totalAnalyses = historyRes.data.total || 0;
        const tasksRes = await api.get('/api/tasks/async');
        const tasks = tasksRes.data.tasks || [];
        const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;

        return {
          tokenBalance: balance,
          totalMaterials,
          totalAnalyses,
          completedTasks,
        };
      } catch (error) {
        console.error('❌ Dashboard istatistik hatası:', error);
        return {
          tokenBalance: user?.token_balance || 0,
          totalMaterials: 0,
          totalAnalyses: 0,
          completedTasks: 0,
        };
      }
    },
    enabled: !!user,
  });

  const fetchActivities = async () => {
    try {
      const res = await api.get('/api/upload/results', {
        params: { limit: 100 },
      });

      const results = res.data.results || [];
      const activityList: Activity[] = results.map((item: any, index: number) => ({
        id: index,
        type: 'analysis',
        message: `${item.material_code || 'Analiz'} tamamlandı`,
        time: new Date(item.created_at).toLocaleString('tr-TR'),
        status: 'success' as const,
        details: item.result_type || 'Analiz',
      }));

      setAllActivities(activityList);
      setActivities(activityList.slice(0, 5));
    } catch (error) {
      console.error('❌ Aktivite hatası:', error);
      setAllActivities([]);
      setActivities([]);
    }
  };

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
        refetchStats();
        await fetchUser();
        fetchActivities();
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

  const handleShowAllActivities = () => {
    setShowAllActivities(true);
    setPage(0);
  };

  const handleCloseActivities = () => {
    setShowAllActivities(false);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

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
        // ✅ embed_origin'i zorla ekle
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

  // ✅ Başarılı ödeme
  const handleCheckoutSuccess = () => {
    console.log('🔍 [DEBUG] ====== handleCheckoutSuccess CALLED ======');
    
    // Kullanıcı bilgilerini yenile
    fetchUser();
    refetchStats();
    
    // ✅ Tüm dialog'ları kapat
    setCheckoutOpen(false);
    setCreditDialogOpen(false);
    
    // Başarılı mesajını göster
    setPaymentStatus('success');
    setPaymentMessage('Kredileriniz hesabınıza başarıyla eklendi!');
    setSuccessMessage('✅ Krediler başarıyla eklendi!');
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  // ✅ İptal / Kapatma
  const handleCheckoutCancel = () => {
    console.log('🔍 [DEBUG] ====== handleCheckoutCancel CALLED ======');
    
    // Tüm dialog'ları kapat
    setCheckoutOpen(false);
    setCreditDialogOpen(false);
    
    // İptal mesajını göster
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

  // ✅ Webhook bildirimi ile dialog'u kapat
  useEffect(() => {
    let intervalId: number | null = null;
    let lastUnreadCount = 0;

    if (checkoutOpen) {
      console.log('🔍 [DEBUG] Checkout açık, bildirim kontrolü başladı...');
      
      intervalId = window.setInterval(async () => {
        try {
          const res = await api.get('/api/notifications/unread-count');
          if (res.data.unread_count > lastUnreadCount) {
            lastUnreadCount = res.data.unread_count;
            console.log('🔍 [DEBUG] Yeni bildirim var! Dialog kapatılıyor...');
            
            await fetchUser();
            refetchStats();
            
            setCheckoutOpen(false);
            setPaymentStatus('success');
            setPaymentMessage('Kredileriniz hesabınıza başarıyla eklendi!');
            setSuccessMessage('✅ Krediler başarıyla eklendi!');
            setTimeout(() => setSuccessMessage(null), 5000);
            
            if (intervalId) {
              clearInterval(intervalId);
              intervalId = null;
            }
          }
        } catch (error) {
          console.error('❌ Bildirim kontrol hatası:', error);
        }
      }, 2000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
  }, [checkoutOpen]);

  // ✅ Kullanıcı oturumu - SADECE BİR KERE
  useEffect(() => {
    const initDashboard = async () => {
      if (user) {
        setLoading(false);
        await fetchActivities();
      }
    };
    initDashboard();
  }, []); // ✅ Boş dependency

  // ✅ Checkout durumu - SADECE checkoutOpen değişince
  useEffect(() => {
    if (checkoutOpen) {
      console.log('🔍 [DEBUG] Checkout açık, bekleniyor...');
    }
  }, [checkoutOpen]);

  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  const analysisCards = [
    {
      title: 'Talep Tahmini',
      description: '4 farklı model ile talep tahmini yapar. Pattern analizi ile zenginleştirilmiştir.',
      icon: <ShowChart />,
      color: '#1976d2',
      path: '/forecast',
      cost: 5,
      isAsync: true,
    },
    {
      title: 'Emniyet Stoğu',
      description: '6 farklı SS metodu ve talep pattern analizi ile optimum emniyet stok seviyelerini belirler.',
      icon: <Security />,
      color: '#2e7d32',
      path: '/safety-stock',
      cost: 3,
      isAsync: true,
    },
    {
      title: 'Monte Carlo Simülasyonu',
      description: 'Binlerce senaryo ile stok performansınızı simüle edin.',
      icon: <Timeline />,
      color: '#9c27b0',
      path: '/simulation',
      cost: 10,
      isAsync: true,
    },
    {
      title: 'Backtest',
      description: '8 farklı stratejiyi geçmiş veri üzerinde test eder.',
      icon: <Backpack />,
      color: '#ed6c02',
      path: '/backtest',
      cost: 15,
      isAsync: true,
    },
    {
      title: 'Tedarikçi Analizi',
      description: 'Tedarikçi performansını ve risklerini analiz eder.',
      icon: <LocalShipping />,
      color: '#d32f2f',
      path: '/supplier',
      cost: 8,
      isAsync: true,
    },
  ];

  const statCards = [
    {
      title: 'Kredi Bakiyesi',
      value: userStats?.tokenBalance || 0,
      icon: <AttachMoney />,
      color: '#f9a825',
      subtitle: '💰 Mevcut kredi',
    },
    {
      title: 'Yüklenen Malzeme',
      value: userStats?.totalMaterials || 0,
      icon: <Inventory />,
      color: '#1976d2',
      subtitle: "Excel'den yüklendi",
    },
    {
      title: 'Toplam Analiz',
      value: userStats?.totalAnalyses || 0,
      icon: <Assessment />,
      color: '#2e7d32',
      subtitle: 'Bugüne kadar yapılan',
    },
    {
      title: 'Tamamlanan ASYNC',
      value: userStats?.completedTasks || 0,
      icon: <CheckCircle />,
      color: '#9c27b0',
      subtitle: 'Arka plan işlemleri',
    },
  ];

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

      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              👋 Hoş Geldin{user?.full_name ? `, ${user.full_name}` : ''}!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Bugün stok durumunu analiz etmeye ne dersin?
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              color="warning"
              startIcon={<ShoppingCart />}
              onClick={() => {
                setPaymentStatus('idle');
                setPaymentMessage(null);
                setCreditDialogOpen(true);
              }}
              sx={{
                borderRadius: 3,
                px: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #f9a825 0%, #f57f17 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #f57f17 0%, #f9a825 100%)',
                },
              }}
            >
              🪙 Kredi Al
            </Button>
          </Box>
        </Box>
      </Box>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <CloudUpload color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Excel Dosyası Yükle
            </Typography>
            <Chip label="Ücretsiz" size="small" color="success" sx={{ ml: 1 }} />
          </Box>

          <UploadArea
            className={isDragging ? 'dragging' : ''}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              {selectedFile ? (
                <>
                  <InsertDriveFile sx={{ fontSize: 48, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<UploadFile />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUpload();
                      }}
                      disabled={uploading}
                    >
                      {uploading ? 'Yükleniyor...' : 'Yükle'}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Clear />}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setUploadError(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                      disabled={uploading}
                    >
                      İptal
                    </Button>
                  </Box>
                </>
              ) : (
                <>
                  <CloudUpload sx={{ fontSize: 64, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Dosyayı Sürükle & Bırak veya Tıkla
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Excel dosyaları desteklenir (.xlsx, .xls)
                  </Typography>
                  <Chip label="Maksimum dosya boyutu: 10 MB" size="small" variant="outlined" />
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
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                variant="determinate"
                value={uploadProgress}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Yükleniyor... %{uploadProgress}
              </Typography>
            </Box>
          )}

          {uploadSuccess && (
            <Alert severity="success" sx={{ mt: 2 }} onClose={() => setUploadSuccess(false)}>
              ✅ Dosya başarıyla yüklendi! Analizlere başlayabilirsiniz.
            </Alert>
          )}

          {uploadError && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setUploadError(null)}>
              {uploadError}
            </Alert>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <StatCard
              title={stat.title}
              value={stat.value}
              icon={stat.icon}
              color={stat.color}
              subtitle={stat.subtitle}
              loading={statsLoading}
            />
          </Grid>
        ))}
      </Grid>

      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
        🚀 Hızlı Analiz
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {analysisCards.map((card, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={index}>
            <AnalysisCard
              title={card.title}
              description={card.description}
              icon={card.icon}
              color={card.color}
              path={card.path}
              cost={card.cost}
              isAsync={card.isAsync}
              onClick={() => navigateTo(card.path)}
            />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  📋 Son Aktiviteler
                </Typography>
                {!showAllActivities && allActivities.length > 5 && (
                  <Button size="small" onClick={handleShowAllActivities}>
                    Tümünü Gör
                  </Button>
                )}
                {showAllActivities && (
                  <Button size="small" onClick={handleCloseActivities}>
                    Kapat
                  </Button>
                )}
              </Box>
              <Divider sx={{ mb: 2 }} />

              {allActivities.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Info color="disabled" sx={{ fontSize: 40 }} />
                  <Typography variant="body2" color="text.secondary">
                    Henüz aktivite yok. İlk analizini başlat!
                  </Typography>
                </Box>
              ) : (
                <>
                  {!showAllActivities ? (
                    <List disablePadding>
                      {activities.map((activity) => (
                        <ActivityItem key={activity.id} activity={activity} />
                      ))}
                    </List>
                  ) : (
                    <>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ bgcolor: 'grey.50' }}>
                              <TableCell>İşlem</TableCell>
                              <TableCell>Tarih</TableCell>
                              <TableCell>Detay</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {paginatedActivities.map((activity) => (
                              <TableRow key={activity.id} hover>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {activity.status === 'success' && (
                                      <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />
                                    )}
                                    {activity.status === 'warning' && (
                                      <Warning sx={{ color: 'warning.main', fontSize: 16 }} />
                                    )}
                                    {activity.status === 'error' && (
                                      <Error sx={{ color: 'error.main', fontSize: 16 }} />
                                    )}
                                    {activity.status === 'info' && (
                                      <Info sx={{ color: 'info.main', fontSize: 16 }} />
                                    )}
                                    {activity.message}
                                  </Box>
                                </TableCell>
                                <TableCell>{activity.time}</TableCell>
                                <TableCell>{activity.details || '-'}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <TablePagination
                        rowsPerPageOptions={[5, 10, 25]}
                        component="div"
                        count={allActivities.length}
                        rowsPerPage={rowsPerPage}
                        page={page}
                        onPageChange={handleChangePage}
                        onRowsPerPageChange={handleChangeRowsPerPage}
                        labelRowsPerPage="Sayfa başına satır:"
                        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
                      />
                    </>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                ℹ️ Hızlı Bilgiler
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Paper sx={{ p: 2, bgcolor: 'success.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    💡 ASYNC Görevler
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Uzun süren analizleri arka planda çalıştırın. <br />
                    <strong>{userStats?.completedTasks || 0}</strong> görev tamamlandı.
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    sx={{ mt: 1 }}
                    onClick={() => navigateTo('/tasks')}
                  >
                    Görevleri Görüntüle
                  </Button>
                </Paper>

                <Paper sx={{ p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    📊 Kredi Sistemi
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Her analiz belirli sayıda kredi harcar. <br />
                    Mevcut kredi: <strong>{userStats?.tokenBalance || 0}</strong>
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    color="warning"
                    sx={{ mt: 1 }}
                    onClick={() => {
                      setPaymentStatus('idle');
                      setPaymentMessage(null);
                      setCreditDialogOpen(true);
                    }}
                  >
                    Kredi Satın Al
                  </Button>
                </Paper>

                <Paper sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    📁 Veri Yönetimi
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    <strong>{userStats?.totalMaterials || 0}</strong> malzeme yüklü. <br />
                    Analiz sonuçları 15 gün saklanır.
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}