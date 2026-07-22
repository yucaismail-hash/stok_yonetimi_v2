// frontend/src/components/Layout/Navbar.tsx - V3.0 (STATUS BAR)

import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Chip,
  Box,
  Popover,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  CircularProgress,
  Skeleton,
  Tooltip,
} from '@mui/material';
import {
  Notifications,
  Logout,
  CheckCircle,
  Warning,
  Error,
  Info,
  AccountBalanceWallet,
  AddCircleOutlined,
} from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../../services/api';
import {
  LayoutDashboard,
  TrendingUp,
  Shield,
  Dice5,
  School,
  Truck,
  ClipboardList,
  User,
  ShieldCheck,
  FileText,
  Calendar,
  CircleCheck,
  CircleAlert,
  CircleX,
  Sparkles,
  Clock,
} from 'lucide-react';
import CreditPurchaseDialog from '../CreditPurchaseDialog';

interface CreditPackage {
  id: number;
  polar_product_id: string;
  name: string;
  credits: number;
  price_tl: number;
  is_active: boolean;
}

interface NavbarProps {
  drawerWidth: number;
}

interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  link?: string;
  created_at: string;
}

interface DatasetStatus {
  id: number | null;
  file_name: string | null;
  product_count: number;
  period_count: number;
  data_points: number;
  created_at: string | null;
  is_active: boolean;
  status: 'ready' | 'old' | 'none';
  last_update: string | null;
}

// 📌 Sayfa Bilgileri - Lucide Icons ile
const pageInfo: Record<string, { title: string; subtitle: string; icon: React.ReactNode }> = {
  '/dashboard': {
    title: 'Dashboard',
    subtitle: 'Stok durumuna genel bakış',
    icon: <LayoutDashboard size={20} strokeWidth={1.8} />,
  },
  '/forecast': {
    title: 'Talep Tahmini',
    subtitle: '4 farklı model ile akıllı talep tahmini',
    icon: <TrendingUp size={20} strokeWidth={1.8} />,
  },
  '/safety-stock': {
    title: 'Emniyet Stoğu',
    subtitle: '6 farklı metod ile optimum stok seviyesi',
    icon: <Shield size={20} strokeWidth={1.8} />,
  },
  '/simulation': {
    title: 'Monte Carlo Simülasyonu',
    subtitle: 'Binlerce senaryo ile stok performans analizi',
    icon: <Dice5 size={20} strokeWidth={1.8} />,
  },
  '/backtest': {
    title: 'Backtest Analizi',
    subtitle: '8 strateji ile geçmiş veri testi',
    icon: <School size={20} strokeWidth={1.8} />,
  },
  '/supplier': {
    title: 'Tedarikçi Analizi',
    subtitle: 'Tedarikçi performans ve risk analizi',
    icon: <Truck size={20} strokeWidth={1.8} />,
  },
  '/tasks': {
    title: 'ASYNC Görevler',
    subtitle: 'Arka plan işlemlerini takip edin',
    icon: <ClipboardList size={20} strokeWidth={1.8} />,
  },
  '/profile': {
    title: 'Profil Yönetimi',
    subtitle: 'Hesap bilgilerinizi yönetin',
    icon: <User size={20} strokeWidth={1.8} />,
  },
  '/admin': {
    title: 'Admin Panel',
    subtitle: 'Sistem yönetimi ve analiz',
    icon: <ShieldCheck size={20} strokeWidth={1.8} />,
  },
};

// 📌 Dosya adını kısalt
const truncateFileName = (name: string, maxLength: number = 28): string => {
  if (!name) return 'Bilinmeyen';
  if (name.length <= maxLength) return name;
  const ext = name.split('.').pop() || '';
  const base = name.slice(0, maxLength - ext.length - 4);
  return `${base}...${ext}`;
};

// 📌 Zaman farkını hesapla
const getTimeAgo = (dateStr: string | null): string => {
  if (!dateStr) return 'Bugün';
  const now = new Date();
  const past = new Date(dateStr);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Şimdi';
  if (diffMins < 60) return `${diffMins} dakika önce`;
  if (diffHours < 24) return `${diffHours} saat önce`;
  if (diffDays < 7) return `${diffDays} gün önce`;
  return past.toLocaleDateString('tr-TR');
};

export default function Navbar({ drawerWidth }: NavbarProps) {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [tokenBalance, setTokenBalance] = useState(user?.token_balance || 0);

  const [datasetStatus, setDatasetStatus] = useState<DatasetStatus>({
    id: null,
    file_name: null,
    product_count: 0,
    period_count: 0,
    data_points: 0,
    created_at: null,
    is_active: false,
    status: 'none',
    last_update: null,
  });
  const [datasetLoading, setDatasetLoading] = useState(true);

  const [creditDialogOpen, setCreditDialogOpen] = useState(false);
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'canceled' | 'error'>('idle');
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);

  const currentPage = pageInfo[location.pathname] || {
    title: 'Stokonomi',
    subtitle: 'Karar Destek Platformu',
    icon: <LayoutDashboard size={20} strokeWidth={1.8} />,
  };

  // 📌 Dataset Status'ü Getir
  const fetchDatasetStatus = async () => {
    setDatasetLoading(true);
    try {
      const res = await api.get('/api/upload/datasets?limit=1');
      if (res.data.success && res.data.datasets?.length > 0) {
        const ds = res.data.datasets[0];
        const createdDate = new Date(ds.created_at);
        const now = new Date();
        const diffHours = (now.getTime() - createdDate.getTime()) / (1000 * 60 * 60);

        setDatasetStatus({
          id: ds.id,
          file_name: ds.source_name || 'Bilinmeyen',
          product_count: ds.product_count || 0,
          period_count: ds.period_count || 0,
          data_points: ds.data_points || 0,
          created_at: ds.created_at,
          is_active: ds.is_active,
          status: ds.is_active ? (diffHours > 24 ? 'old' : 'ready') : 'none',
          last_update: ds.created_at,
        });
      } else {
        setDatasetStatus({
          id: null,
          file_name: null,
          product_count: 0,
          period_count: 0,
          data_points: 0,
          created_at: null,
          is_active: false,
          status: 'none',
          last_update: null,
        });
      }
    } catch (error) {
      console.error('❌ Dataset durumu alınamadı:', error);
      setDatasetStatus({
        id: null,
        file_name: null,
        product_count: 0,
        period_count: 0,
        data_points: 0,
        created_at: null,
        is_active: false,
        status: 'none',
        last_update: null,
      });
    } finally {
      setDatasetLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasetStatus();
    const interval = setInterval(fetchDatasetStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setTokenBalance(user?.token_balance || 0);
  }, [user?.token_balance]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await refreshUser();
        const state = useAuth.getState();
        setTokenBalance(state.user?.token_balance || 0);
      } catch (error) {
        console.error('❌ Bakiye yenileme hatası:', error);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [refreshUser]);

  const refreshTokenBalance = async () => {
    try {
      await refreshUser();
      const state = useAuth.getState();
      setTokenBalance(state.user?.token_balance || 0);
    } catch (error) {
      console.error('❌ Bakiye yenileme hatası:', error);
    }
  };

  useEffect(() => {
    if (paymentStatus === 'success') {
      refreshTokenBalance();
      fetchDatasetStatus();
    }
  }, [paymentStatus]);

  const handlePurchase = async (pkg: CreditPackage) => {
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
        window.location.href = checkoutUrl.toString();
        setIsCreatingCheckout(false);
        setCreditDialogOpen(false);
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

  const handlePaymentReset = () => {
    setPaymentStatus('idle');
    setPaymentMessage(null);
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    handleClose();
  };

  const handleProfile = () => {
    navigate('/profile');
    handleClose();
  };

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
    fetchNotifications();
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/notifications/?limit=20');
      if (res.data.success) {
        setNotifications(res.data.notifications || []);
      }
    } catch (error) {
      console.error('❌ Bildirim hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/api/notifications/unread-count');
      let count = res.data.unread_count || 0;
      if (count > 9 && count <= 99) {
        count = 9;
      } else if (count > 99) {
        count = 99;
      }
      setUnreadCount(count);
    } catch (error) {
      console.error('❌ Okunmamış bildirim hatası:', error);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      await api.post(`/api/notifications/mark-read/${id}`);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
      await fetchUnreadCount();
    } catch (error) {
      console.error('❌ Bildirim okundu hatası:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/api/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('❌ Tümünü okundu hatası:', error);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    if (notification.link) {
      navigate(notification.link);
      handleNotificationClose();
    }
  };

  const getNotificationIcon = (type: string) => {
    switch(type) {
      case 'success': return <CheckCircle sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main', fontSize: 20 }} />;
      case 'error': return <Error sx={{ color: 'error.main', fontSize: 20 }} />;
      default: return <Info sx={{ color: 'info.main', fontSize: 20 }} />;
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const open = Boolean(notificationAnchor);

  // ✅ STATUS BAR - Tek satır, nokta ayırıcılı
  const renderStatusBar = () => {
    if (datasetLoading) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, height: 32 }}>
          <Skeleton variant="text" width={120} height={18} />
          <Skeleton variant="circular" width={4} height={4} />
          <Skeleton variant="text" width={60} height={16} />
          <Skeleton variant="circular" width={4} height={4} />
          <Skeleton variant="text" width={80} height={16} />
          <Skeleton variant="circular" width={4} height={4} />
          <Skeleton variant="text" width={70} height={16} />
        </Box>
      );
    }

    if (datasetStatus.status === 'none') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, height: 32 }}>
          <Typography variant="body2" sx={{ color: '#d32f2f', fontSize: '0.8rem', fontWeight: 500 }}>
            Veri Yüklenmemiş
          </Typography>
          <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
            Lütfen Excel yükleyin
          </Typography>
        </Box>
      );
    }

    const statusConfig = {
      ready: { label: 'Hazır', color: '#2e7d32', dot: <CircleCheck size={14} color="#2e7d32" /> },
      old: { label: 'Güncel Değil', color: '#ed6c02', dot: <CircleAlert size={14} color="#ed6c02" /> },
    };

    const config = statusConfig[datasetStatus.status as keyof typeof statusConfig];
    const displayName = truncateFileName(datasetStatus.file_name || 'Bilinmeyen', 28);
    const timeAgo = getTimeAgo(datasetStatus.created_at);

    return (
      <Tooltip 
        title={datasetStatus.file_name || 'Bilinmeyen'} 
        arrow 
        placement="bottom"
        slotProps={{
          tooltip: {
            sx: {
              fontSize: '0.7rem',
              bgcolor: '#1f4e79',
              color: 'white',
              maxWidth: 400,
              py: 1,
              px: 1.5,
            },
          },
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2,
          height: 32,
          color: '#1f4e79',
        }}>
          {/* 📄 Dosya Adı */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <FileText size={14} color="#1f4e79" />
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: '#1f4e79',
                fontSize: '0.85rem',
                letterSpacing: '-0.2px',
                whiteSpace: 'nowrap',
              }}
            >
              {displayName}
            </Typography>
          </Box>

          {/* • Ayırıcı */}
          <Typography variant="body2" sx={{ color: '#d0d0d0', fontSize: '1.2rem', fontWeight: 300, lineHeight: 1 }}>
            •
          </Typography>

          {/* 📊 Ürün Sayısı */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.65rem', fontWeight: 500, whiteSpace: 'nowrap' }}>
              {datasetStatus.product_count} Ürün
            </Typography>
          </Box>

          {/* • Ayırıcı */}
          <Typography variant="body2" sx={{ color: '#d0d0d0', fontSize: '1.2rem', fontWeight: 300, lineHeight: 1 }}>
            •
          </Typography>

          {/* 🕐 Zaman */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Clock size={12} color="#9e9e9e" />
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem', fontWeight: 400, whiteSpace: 'nowrap' }}>
              {timeAgo}
            </Typography>
          </Box>

          {/* • Ayırıcı */}
          <Typography variant="body2" sx={{ color: '#d0d0d0', fontSize: '1.2rem', fontWeight: 300, lineHeight: 1 }}>
            •
          </Typography>

          {/* 🟢 Durum Chip */}
          <Chip
            icon={config.dot}
            label={config.label}
            size="small"
            sx={{
              height: 24,
              fontSize: '0.6rem',
              fontWeight: 600,
              backgroundColor: datasetStatus.status === 'ready' ? '#e8f5e9' : '#fff3e0',
              color: config.color,
              '& .MuiChip-icon': { fontSize: 14, marginLeft: 0.5 },
              '& .MuiChip-label': { px: 1, py: 0 },
            }}
          />

          {/* • Ayırıcı */}
          <Typography variant="body2" sx={{ color: '#d0d0d0', fontSize: '1.2rem', fontWeight: 300, lineHeight: 1 }}>
            •
          </Typography>

          {/* 🧠 AI Hazır (sadece ready ise) */}
          {datasetStatus.status === 'ready' && (
            <Chip
              icon={<Sparkles size={14} color="#6b7280" />}
              label="AI Hazır"
              size="small"
              sx={{
                height: 24,
                fontSize: '0.55rem',
                fontWeight: 500,
                backgroundColor: '#f5f5f5',
                color: '#6b7280',
                '& .MuiChip-icon': { fontSize: 14, marginLeft: 0.5 },
                '& .MuiChip-label': { px: 1, py: 0 },
              }}
            />
          )}
        </Box>
      </Tooltip>
    );
  };

  return (
    <>
      <CreditPurchaseDialog
        open={creditDialogOpen}
        onClose={() => {
          setCreditDialogOpen(false);
          setPaymentStatus('idle');
          setPaymentMessage(null);
        }}
        onPurchase={handlePurchase}
        currentBalance={tokenBalance}
        isLoading={isCreatingCheckout}
        paymentStatus={paymentStatus}
        paymentMessage={paymentMessage}
        onReset={handlePaymentReset}
      />

      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: '#ffffff',
          color: '#1f4e79',
          boxShadow: '0 1px 4px rgba(31, 78, 121, 0.06)',
          borderBottom: '1px solid #f0f0f0',
          height: 64,
          minHeight: 64,
        }}
      >
        <Toolbar sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          minHeight: 64,
          height: 64,
          px: { xs: 2, sm: 3 },
          gap: 2,
        }}>
          {/* ✅ SOL BÖLÜM - Sayfa Bilgisi */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: { xs: 120, sm: 160 }, flexShrink: 0 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 36,
                height: 36,
                borderRadius: 2,
                backgroundColor: '#f0f7ff',
                flexShrink: 0,
              }}
            >
              {currentPage.icon}
            </Box>

            <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 600,
                  color: '#1f4e79',
                  fontSize: '0.9rem',
                  lineHeight: 1.2,
                  letterSpacing: '-0.2px',
                  whiteSpace: 'nowrap',
                }}
              >
                {currentPage.title}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: '#8c8c8c',
                  fontSize: '0.55rem',
                  fontWeight: 400,
                  display: { xs: 'none', md: 'block' },
                  whiteSpace: 'nowrap',
                }}
              >
                {currentPage.subtitle}
              </Typography>
            </Box>
          </Box>

          {/* ✅ ORTA BÖLÜM - Status Bar */}
          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              minWidth: 0,
              overflow: 'hidden',
            }}
          >
            {renderStatusBar()}
          </Box>

          {/* ✅ SAĞ BÖLÜM - Kredi, Bildirim, Profil */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexShrink: 0 }}>
            {/* Analiz Kredisi */}
            <Tooltip title="Mevcut Analiz Kredisi" arrow placement="bottom">
              <Chip
                icon={<AccountBalanceWallet sx={{ fontSize: 18, color: '#f57c00' }} />}
                label={
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: '#e65100',
                      fontSize: '0.7rem',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {tokenBalance.toLocaleString('tr-TR')} Analiz Kredisi
                  </Typography>
                }
                size="small"
                sx={{
                  backgroundColor: '#fff8e1',
                  border: '1px solid #ffecb3',
                  borderRadius: 2,
                  height: 32,
                  '& .MuiChip-label': {
                    px: 1,
                    py: 0,
                  },
                  '& .MuiChip-icon': {
                    marginLeft: 1,
                    marginRight: 0.5,
                  },
                }}
              />
            </Tooltip>

            {/* Kredi Al Butonu */}
            <Button
              size="small"
              variant="outlined"
              startIcon={<AddCircleOutlined sx={{ fontSize: 16, color: '#f57c00' }} />}
              onClick={() => {
                setPaymentStatus('idle');
                setPaymentMessage(null);
                setCreditDialogOpen(true);
              }}
              sx={{
                borderColor: '#ffb300',
                color: '#e65100',
                borderRadius: 2,
                fontSize: '0.55rem',
                fontWeight: 600,
                textTransform: 'none',
                px: 1.5,
                py: 0.5,
                minWidth: 'auto',
                whiteSpace: 'nowrap',
                height: 32,
                '&:hover': {
                  backgroundColor: '#fff8e1',
                  borderColor: '#f57c00',
                },
              }}
            >
              Kredi Al
            </Button>

            {/* Bildirim Butonu */}
            <IconButton
              onClick={handleNotificationOpen}
              size="small"
              sx={{
                color: '#6b7280',
                '&:hover': { backgroundColor: '#f0f7ff' },
              }}
            >
              <Badge
                badgeContent={unreadCount > 0 ? (unreadCount > 9 ? '9+' : unreadCount) : 0}
                color="error"
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: 9,
                    height: 18,
                    minWidth: 18,
                    fontWeight: 600,
                  },
                }}
              >
                <Notifications sx={{ fontSize: 20 }} />
              </Badge>
            </IconButton>

            {/* Kullanıcı Menüsü */}
            <IconButton
              onClick={handleMenu}
              size="small"
              sx={{
                p: 0.5,
                '&:hover': { opacity: 0.8 },
              }}
            >
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: '#1f4e79',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                }}
              >
                {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
              </Avatar>
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              keepMounted
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
              slotProps={{
                paper: {
                  sx: {
                    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                    borderRadius: 2,
                    minWidth: 160,
                  },
                },
              }}
            >
              <MenuItem onClick={handleProfile} sx={{ fontSize: '0.8rem', py: 1 }}>
                <User size={16} style={{ marginRight: 10, color: '#6b7280' }} />
                Profil
              </MenuItem>
              <MenuItem onClick={handleLogout} sx={{ fontSize: '0.8rem', py: 1, color: 'error.main' }}>
                <Logout fontSize="small" sx={{ mr: 1, fontSize: 16 }} />
                Çıkış Yap
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* ✅ Bildirim Popover */}
      <Popover
        open={open}
        anchorEl={notificationAnchor}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            sx: {
              width: 380,
              maxHeight: 400,
              borderRadius: 2,
              boxShadow: '0 8px 40px rgba(0,0,0,0.12)',
              overflow: 'hidden',
            },
          },
        }}
      >
        <Box sx={{ p: 2, borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            🔔 Bildirimler
          </Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={markAllAsRead} sx={{ fontSize: '0.6rem', textTransform: 'none' }}>
              Tümünü Okundu İşaretle
            </Button>
          )}
        </Box>

        {loading ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress size={28} />
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              Bildirim bulunmuyor.
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0, overflow: 'auto' }}>
            {notifications.map((notification) => (
              <ListItem
                key={notification.id}
                sx={{
                  px: 2,
                  py: 1.5,
                  borderBottom: '1px solid #f5f5f5',
                  backgroundColor: notification.is_read ? 'transparent' : '#f8faff',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: '#f0f7ff',
                  },
                }}
                onClick={() => handleNotificationClick(notification)}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {getNotificationIcon(notification.type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ fontWeight: notification.is_read ? 400 : 600, fontSize: '0.75rem' }}>
                      {notification.title}
                    </Typography>
                  }
                  secondary={
                    <>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.55rem' }}>
                        {new Date(notification.created_at).toLocaleString('tr-TR')}
                      </Typography>
                    </>
                  }
                />
                {!notification.is_read && (
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main', flexShrink: 0 }} />
                )}
              </ListItem>
            ))}
          </List>
        )}
      </Popover>
    </>
  );
}