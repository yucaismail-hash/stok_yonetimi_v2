import { AppBar, Toolbar, Typography, IconButton, Badge, Avatar, Menu, MenuItem, Chip, Box, Popover, List, ListItem, ListItemText, ListItemIcon, Button, Divider, Breadcrumbs, Link } from '@mui/material';
import { 
  Notifications, 
  Logout, 
  CheckCircle, 
  Warning, 
  Error, 
  Info, 
  Close, 
  Home, 
  Add, 
  NavigateNext,
  AddCircleOutlined,
  AccountBalanceWallet,
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

const pageInfo: Record<string, { title: string; subtitle: string; icon: React.ReactNode }> = {
  '/dashboard': {
    title: 'Dashboard',
    subtitle: 'Stok durumuna genel bakış',
    icon: <LayoutDashboard size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/forecast': {
    title: 'Talep Tahmini',
    subtitle: '4 farklı model ile akıllı talep tahmini',
    icon: <TrendingUp size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/safety-stock': {
    title: 'Emniyet Stoğu',
    subtitle: '6 farklı metod ile optimum stok seviyesi',
    icon: <Shield size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/simulation': {
    title: 'Monte Carlo Simülasyonu',
    subtitle: 'Binlerce senaryo ile stok performans analizi',
    icon: <Dice5 size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/backtest': {
    title: 'Backtest Analizi',
    subtitle: '8 strateji ile geçmiş veri testi',
    icon: <School size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/supplier': {
    title: 'Tedarikçi Analizi',
    subtitle: 'Tedarikçi performans ve risk analizi',
    icon: <Truck size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/tasks': {
    title: 'ASYNC Görevler',
    subtitle: 'Arka plan işlemlerini takip edin',
    icon: <ClipboardList size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/profile': {
    title: 'Profil Yönetimi',
    subtitle: 'Hesap bilgilerinizi yönetin',
    icon: <User size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
  '/admin': {
    title: 'Admin Panel',
    subtitle: 'Sistem yönetimi ve analiz',
    icon: <ShieldCheck size={20} color="#1f4e79" strokeWidth={1.8} />,
  },
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

  const [creditDialogOpen, setCreditDialogOpen] = useState(false);
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'canceled' | 'error'>('idle');
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);

  const currentPage = pageInfo[location.pathname] || {
    title: 'Stokonomi',
    subtitle: 'Karar Destek Platformu',
    icon: <LayoutDashboard size={20} color="#1f4e79" strokeWidth={1.8} />,
  };

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
      setUnreadCount(res.data.unread_count || 0);
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
      setUnreadCount(prev => Math.max(0, prev - 1));
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
          boxShadow: '0 1px 4px rgba(31, 78, 121, 0.08)',
          borderBottom: '1px solid #e8f0fe',
        }}
      >
        <Toolbar sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          minHeight: 56,
          px: { xs: 2, sm: 3 },
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: 1.5,
                backgroundColor: '#f0f7ff',
                flexShrink: 0,
              }}
            >
              {currentPage.icon}
            </Box>

            <Box>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 600,
                  color: '#1f4e79',
                  fontSize: '0.95rem',
                  lineHeight: 1.2,
                  letterSpacing: '-0.2px',
                }}
              >
                {currentPage.title}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: '#8c8c8c',
                  fontSize: '0.65rem',
                  fontWeight: 400,
                  display: { xs: 'none', sm: 'block' },
                }}
              >
                {currentPage.subtitle}
              </Typography>
            </Box>

            <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', ml: 1 }}>
              <Breadcrumbs
                separator={<NavigateNext fontSize="small" sx={{ color: '#d0d0d0', fontSize: 14 }} />}
                sx={{
                  '& .MuiBreadcrumbs-ol': {
                    alignItems: 'center',
                  },
                }}
              >
                <Link
                  underline="hover"
                  color="text.secondary"
                  href="/dashboard"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    fontSize: '0.7rem',
                    '&:hover': { color: '#1f4e79' },
                  }}
                >
                  <Home sx={{ fontSize: 13 }} />
                  Ana Sayfa
                </Link>
                <Typography
                  color="primary"
                  sx={{
                    fontSize: '0.7rem',
                    fontWeight: 500,
                    color: '#1f4e79',
                  }}
                >
                  {currentPage.title}
                </Typography>
              </Breadcrumbs>
            </Box>
          </Box>

          {/* ✅ Sağ Taraf - Kredi ve Bildirimler */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* ✅ Kredi Bakiyesi - AccountBalanceWallet Icon ile */}
            <Chip
              icon={<AccountBalanceWallet sx={{ fontSize: 18, color: '#f57c00' }} />}
              label={
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: '#e65100',
                    fontSize: '0.8rem',
                  }}
                >
                  {tokenBalance.toLocaleString('tr-TR')} Kredi
                </Typography>
              }
              size="small"
              sx={{
                backgroundColor: '#fff8e1',
                border: '1px solid #ffecb3',
                borderRadius: 2,
                height: 30,
                '& .MuiChip-label': {
                  px: 1.5,
                  py: 0,
                },
                '& .MuiChip-icon': {
                  marginLeft: 1,
                  marginRight: 0.5,
                },
              }}
            />

            {/* ✅ Kredi Al Butonu - Çerçeveli */}
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
                fontSize: '0.65rem',
                fontWeight: 600,
                textTransform: 'none',
                px: 1.5,
                py: 0.5,
                minWidth: 'auto',
                whiteSpace: 'nowrap',
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
                badgeContent={unreadCount}
                color="error"
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: 9,
                    height: 18,
                    minWidth: 18,
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
                  width: 30,
                  height: 30,
                  bgcolor: '#1f4e79',
                  fontSize: '0.8rem',
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
    </>
  );
}