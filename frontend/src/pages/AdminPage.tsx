// frontend/src/pages/AdminPage.tsx - TAM DOSYA (GÜNCELLENMİŞ)
// 🆕 3 yeni tab eklendi: Endpoint Profilleri, Score Aralıkları, İşlem Logları

import { useState, useEffect, useMemo } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
  Snackbar,
  Tab,
  Tabs,
  Avatar,
  TablePagination,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Refresh,
  Payments,
  Receipt,
  Search,
  AdminPanelSettings,
  ShoppingCart,
  AttachMoney,
  Person,
  Email,
  FilterList,
  Clear,
  Cancel,
  AccountBalance,
  Warning as WarningIcon,
  Edit,
  Delete,
  Add,
  Save,
  Close,
  Check,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api, {
  getEndpointProfiles,
  createEndpointProfile,
  updateEndpointProfile,
  deleteEndpointProfile,
  initDefaultEndpointProfiles,
  getScoreRanges,
  createScoreRange,
  updateScoreRange,
  deleteScoreRange,
  initDefaultScoreRanges,
  getProcessingTransactions,
} from '../services/api';

// 📊 İşlem Tipi
interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  price: number;
  transaction_type: 'purchase' | 'refund' | 'bonus';
  polar_order_id: string;
  polar_product_id: string;
  description: string;
  created_at: string;
  user?: {
    email: string;
    full_name: string;
    token_balance: number;
  };
}

// 📊 Kullanıcı İstatistikleri
interface UserStats {
  user_id: number;
  email: string;
  full_name: string;
  total_purchases: number;
  total_refunds: number;
  net_credits: number;
}

// 📊 Endpoint Profili
interface EndpointProfile {
  id: number;
  endpoint: string;
  method: string;
  base_credit: number;
  pricing_type: string;
  algorithm_weight: number;
  avg_time_per_unit: number;
  is_active: boolean;
  description?: string;
  version: string;
  created_at: string;
  updated_at: string;
}

// 📊 Score Range
interface ScoreRange {
  id: number;
  min_score: number;
  max_score: number;
  credit_cost: number;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 📊 Processing Transaction
interface ProcessingTransaction {
  id: number;
  user_id: number;
  user_email?: string;
  dataset_id?: number;
  endpoint: string;
  processing_score: number;
  credit_cost: number;
  balance_after: number;
  elapsed_time_ms?: number;
  avg_time_per_unit_ms?: number;
  status: string;
  created_at: string;
  dataset?: {
    product_count: number;
    period_count: number;
    data_points: number;
  };
}

export default function AdminPage() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [refundDialogOpen, setRefundDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Transaction | null>(null);
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('customer_request');
  const [refundLoading, setRefundLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [userStats, setUserStats] = useState<UserStats[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);

  // 🆕 YENİ STATE'LER
  const [endpointProfiles, setEndpointProfiles] = useState<EndpointProfile[]>([]);
  const [scoreRanges, setScoreRanges] = useState<ScoreRange[]>([]);
  const [processingTransactions, setProcessingTransactions] = useState<ProcessingTransaction[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);
  const [rangesLoading, setRangesLoading] = useState(false);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [rangeDialogOpen, setRangeDialogOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<EndpointProfile | null>(null);
  const [editingRange, setEditingRange] = useState<ScoreRange | null>(null);
  const [profileForm, setProfileForm] = useState<Partial<EndpointProfile>>({
    endpoint: '',
    method: 'POST',
    base_credit: 1,
    pricing_type: 'DATA_POINTS',
    algorithm_weight: 1.0,
    avg_time_per_unit: 0.0,
    is_active: true,
    description: '',
  });
  const [rangeForm, setRangeForm] = useState<Partial<ScoreRange>>({
    min_score: 0,
    max_score: 10000,
    credit_cost: 3,
    is_active: true,
    description: '',
  });

  // 📊 İstatistikler
  const [stats, setStats] = useState({
    total_transactions: 0,
    total_credits_sold: 0,
    total_refunds: 0,
    total_revenue: 0,
    total_users: 0,
    refund_rate: 0,
  });

  // Admin kontrolü
  const isAdmin = user?.email === 'admin@stok.com' || user?.email === 'admin@admin.com';

  useEffect(() => {
    if (isAdmin) {
      fetchTransactions();
      fetchStats();
      fetchUserStats();
      fetchEndpointProfiles();
      fetchScoreRanges();
      fetchProcessingTransactions();
    }
  }, [isAdmin]);

  // 📌 VERİ ÇEKME FONKSİYONLARI
  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/admin/credit-transactions');
      console.log('🔍 [DEBUG] Transactions response:', res.data);
      
      if (res.data && res.data.items && Array.isArray(res.data.items)) {
        setTransactions(res.data.items);
      } else if (res.data && Array.isArray(res.data)) {
        setTransactions(res.data);
      } else {
        setTransactions([]);
      }
    } catch (err: any) {
      console.error('❌ İşlem hatası:', err);
      setError(err.response?.data?.detail || 'İşlemler yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get('/admin/dashboard/stats');
      if (res.data) {
        const data = res.data;
        setStats({
          total_transactions: data.credit_sales?.total_transactions || 0,
          total_credits_sold: data.credit_sales?.total_credits_sold || 0,
          total_refunds: data.credit_sales?.total_refunds || 0,
          total_revenue: data.credit_sales?.total_revenue || 0,
          total_users: data.users?.total || 0,
          refund_rate: data.credit_sales?.total_transactions > 0 
            ? (data.credit_sales?.total_refunds || 0) / data.credit_sales?.total_transactions * 100 
            : 0,
        });
      }
    } catch (err) {
      console.error('❌ İstatistik hatası:', err);
    }
  };

  const fetchUserStats = async () => {
    setStatsLoading(true);
    try {
      const res = await api.get('/admin/users/stats');
      if (res.data) {
        setUserStats(res.data);
      }
    } catch (err) {
      console.error('❌ Kullanıcı istatistikleri hatası:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  // 🆕 ENDPOINT PROFİLLERİ
  const fetchEndpointProfiles = async () => {
    setProfilesLoading(true);
    try {
      const res = await getEndpointProfiles();
      setEndpointProfiles(res.data || []);
    } catch (err) {
      console.error('❌ Profil hatası:', err);
      setError('Endpoint profilleri yüklenemedi.');
    } finally {
      setProfilesLoading(false);
    }
  };

  const handleCreateProfile = async () => {
    try {
      const res = await createEndpointProfile(profileForm);
      setSuccess('✅ Profil başarıyla oluşturuldu!');
      setProfileDialogOpen(false);
      setProfileForm({
        endpoint: '',
        method: 'POST',
        base_credit: 1,
        pricing_type: 'DATA_POINTS',
        algorithm_weight: 1.0,
        avg_time_per_unit: 0.0,
        is_active: true,
        description: '',
      });
      fetchEndpointProfiles();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Profil oluşturulamadı.');
    }
  };

  const handleUpdateProfile = async () => {
    if (!editingProfile) return;
    try {
      const res = await updateEndpointProfile(editingProfile.id, profileForm);
      setSuccess('✅ Profil başarıyla güncellendi!');
      setProfileDialogOpen(false);
      setEditingProfile(null);
      setProfileForm({
        endpoint: '',
        method: 'POST',
        base_credit: 1,
        pricing_type: 'DATA_POINTS',
        algorithm_weight: 1.0,
        avg_time_per_unit: 0.0,
        is_active: true,
        description: '',
      });
      fetchEndpointProfiles();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Profil güncellenemedi.');
    }
  };

  const handleDeleteProfile = async (id: number) => {
    if (!window.confirm('Bu profili silmek istediğinize emin misiniz?')) return;
    try {
      await deleteEndpointProfile(id);
      setSuccess('✅ Profil silindi!');
      fetchEndpointProfiles();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Profil silinemedi.');
    }
  };

  const handleInitDefaultProfiles = async () => {
    try {
      await initDefaultEndpointProfiles();
      setSuccess('✅ Varsayılan profiller yüklendi!');
      fetchEndpointProfiles();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Varsayılan profiller yüklenemedi.');
    }
  };

  // 🆕 SCORE RANGES
  const fetchScoreRanges = async () => {
    setRangesLoading(true);
    try {
      const res = await getScoreRanges();
      setScoreRanges(res.data || []);
    } catch (err) {
      console.error('❌ Aralık hatası:', err);
      setError('Score aralıkları yüklenemedi.');
    } finally {
      setRangesLoading(false);
    }
  };

  const handleCreateRange = async () => {
    try {
      const res = await createScoreRange(rangeForm);
      setSuccess('✅ Aralık başarıyla oluşturuldu!');
      setRangeDialogOpen(false);
      setRangeForm({
        min_score: 0,
        max_score: 10000,
        credit_cost: 3,
        is_active: true,
        description: '',
      });
      fetchScoreRanges();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Aralık oluşturulamadı.');
    }
  };

  const handleUpdateRange = async () => {
    if (!editingRange) return;
    try {
      const res = await updateScoreRange(editingRange.id, rangeForm);
      setSuccess('✅ Aralık başarıyla güncellendi!');
      setRangeDialogOpen(false);
      setEditingRange(null);
      setRangeForm({
        min_score: 0,
        max_score: 10000,
        credit_cost: 3,
        is_active: true,
        description: '',
      });
      fetchScoreRanges();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Aralık güncellenemedi.');
    }
  };

  const handleDeleteRange = async (id: number) => {
    if (!window.confirm('Bu aralığı silmek istediğinize emin misiniz?')) return;
    try {
      await deleteScoreRange(id);
      setSuccess('✅ Aralık silindi!');
      fetchScoreRanges();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Aralık silinemedi.');
    }
  };

  const handleInitDefaultRanges = async () => {
    try {
      await initDefaultScoreRanges();
      setSuccess('✅ Varsayılan aralıklar yüklendi!');
      fetchScoreRanges();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Varsayılan aralıklar yüklenemedi.');
    }
  };

  // 🆕 PROCESSING TRANSACTIONS
  const fetchProcessingTransactions = async () => {
    setTransactionsLoading(true);
    try {
      const res = await getProcessingTransactions(100);
      setProcessingTransactions(res.data?.items || []);
    } catch (err) {
      console.error('❌ İşlem hatası:', err);
      setError('İşlem logları yüklenemedi.');
    } finally {
      setTransactionsLoading(false);
    }
  };

  // 🔄 İADE İŞLEMİ
  const handleRefund = async () => {
    if (!selectedOrder) return;
    
    setRefundLoading(true);
    setError(null);
    
    try {
      const payload: any = {
        order_id: selectedOrder.polar_order_id,
        refund_credits: refundAmount ? parseFloat(refundAmount) : selectedOrder.amount,
        reason: refundReason,
        refund_type: 'money',
      };
      
      const res = await api.post('/api/polar/refund', payload);
      
      if (res.data.success) {
        setSuccess(`✅ İade başarıyla oluşturuldu! Kullanıcı: ${res.data.user_email}, İade: ${res.data.refund_amount} Kredi, Tutar: ₺${res.data.refund_price?.toFixed(2) || '0'}`);
        setRefundDialogOpen(false);
        setSelectedOrder(null);
        setRefundAmount('');
        setRefundReason('customer_request');
        fetchTransactions();
        fetchStats();
        fetchUserStats();
      }
    } catch (err: any) {
      console.error('❌ İade hatası:', err);
      setError(err.response?.data?.detail || 'İade oluşturulamadı.');
    } finally {
      setRefundLoading(false);
    }
  };

  // 🔍 FİLTRELEME VE ARAMA
  const filteredTransactions = useMemo(() => {
    let filtered = transactions;
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(t => 
        t.user?.email?.toLowerCase().includes(term) ||
        t.user?.full_name?.toLowerCase().includes(term) ||
        t.polar_order_id?.toLowerCase().includes(term) ||
        t.description?.toLowerCase().includes(term)
      );
    }
    
    if (filterType !== 'all') {
      filtered = filtered.filter(t => t.transaction_type === filterType);
    }
    
    return filtered;
  }, [transactions, searchTerm, filterType]);

  // 📋 SAYFALAMA
  const paginatedTransactions = filteredTransactions.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // 🎨 YARDIMCI FONKSİYONLAR
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatCurrency = (value: number) => {
    if (!value) return '-';
    return `₺${value.toFixed(2)}`;
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const formatCredits = (amount: number, type: string) => {
    const sign = type === 'refund' ? '-' : '+';
    return `${sign}${amount}`;
  };

  const getStatusChip = (type: string) => {
    switch(type) {
      case 'purchase':
        return <Chip label="Satın Alma" size="small" color="success" icon={<ShoppingCart />} />;
      case 'refund':
        return <Chip label="İade" size="small" color="error" icon={<Cancel />} />;
      case 'bonus':
        return <Chip label="Bonus" size="small" color="warning" icon={<AttachMoney />} />;
      default:
        return <Chip label={type} size="small" />;
    }
  };

  const getPackageName = (description: string) => {
    if (description.includes('Starter')) return 'Starter';
    if (description.includes('Growth')) return 'Growth';
    if (description.includes('Business')) return 'Business';
    return 'Bilinmiyor';
  };

  const openRefundDialog = (transaction: Transaction) => {
    setSelectedOrder(transaction);
    setRefundAmount(transaction.amount.toString());
    setRefundDialogOpen(true);
  };

  // 🚫 Yetki kontrolü
  if (!isAdmin) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Card sx={{ p: 4, textAlign: 'center', maxWidth: 400 }}>
          <AdminPanelSettings sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
            ⛔ Yetkisiz Erişim
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Bu sayfaya erişim yetkiniz yok. Admin hesabı ile giriş yapın.
          </Typography>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      {/* 📢 Snackbar */}
      <Snackbar
        open={!!error || !!success}
        autoHideDuration={6000}
        onClose={() => { setError(null); setSuccess(null); }}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity={error ? 'error' : 'success'} onClose={() => { setError(null); setSuccess(null); }}>
          {error || success}
        </Alert>
      </Snackbar>

      {/* 📌 HEADER */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            🛡️ Admin Panel
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Kredi satışlarını ve iadeleri yönetin
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
          onClick={() => { fetchTransactions(); fetchStats(); fetchUserStats(); fetchEndpointProfiles(); fetchScoreRanges(); fetchProcessingTransactions(); }}
          disabled={loading}
        >
          {loading ? 'Yükleniyor...' : 'Yenile'}
        </Button>
      </Box>

      {/* 📊 İSTATİSTİK KARTLARI */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Toplam İşlem</Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{stats.total_transactions}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {stats.total_users} aktif kullanıcı
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.light', color: 'primary.main' }}>
                  <Receipt />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Satılan Kredi</Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{stats.total_credits_sold}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.light', color: 'success.main' }}>
                  <AttachMoney />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">İade Oranı</Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {formatPercent(stats.refund_rate)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {stats.total_refunds} iade işlemi
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'error.light', color: 'error.main' }}>
                  <Cancel />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Toplam Gelir</Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {formatCurrency(stats.total_revenue)}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.light', color: 'warning.main' }}>
                  <Payments />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 🔍 FİLTRELEME ALANI */}
      <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="🔍 Kullanıcı, Email, Sipariş ID ara..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ flex: 1, minWidth: 200 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={() => setSearchTerm('')}>
                    <Clear />
                  </IconButton>
                </InputAdornment>
              ),
            }
          }}
        />
        
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>İşlem Tipi</InputLabel>
          <Select
            value={filterType}
            label="İşlem Tipi"
            onChange={(e) => setFilterType(e.target.value)}
          >
            <MenuItem value="all">Tümü</MenuItem>
            <MenuItem value="purchase">Satın Alma</MenuItem>
            <MenuItem value="refund">İade</MenuItem>
            <MenuItem value="bonus">Bonus</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          size="small"
          onClick={() => { setSearchTerm(''); setFilterType('all'); }}
          startIcon={<FilterList />}
        >
          Temizle
        </Button>
      </Paper>

      {/* 📋 TABLOLAR */}
      <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="📋 Tüm İşlemler" />
        <Tab label="🔄 İade İşlemleri" />
        <Tab label="📊 Endpoint Profilleri" />
        <Tab label="📈 Score Aralıkları" />
        <Tab label="📋 İşlem Logları" />
      </Tabs>

      {/* Tab 0: Tüm İşlemler */}
      {tabValue === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              Kredi İşlemleri ({filteredTransactions.length})
            </Typography>
            
            {loading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : filteredTransactions.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary">İşlem bulunamadı</Typography>
              </Box>
            ) : (
              <>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'grey.50' }}>
                        <TableCell>Kullanıcı</TableCell>
                        <TableCell>Paket</TableCell>
                        <TableCell>İşlem</TableCell>
                        <TableCell align="right">Kredi</TableCell>
                        <TableCell align="right">Tutar (TL)</TableCell>
                        <TableCell>Sipariş ID</TableCell>
                        <TableCell>Tarih</TableCell>
                        <TableCell align="center">İşlem</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paginatedTransactions.map((item) => {
                        const isRefunded = transactions.some(t => 
                          t.polar_order_id === item.polar_order_id && 
                          t.transaction_type === 'refund'
                        );
                        
                        return (
                          <TableRow key={item.id} hover>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                  {item.user?.full_name || 'Bilinmiyor'}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  <Email fontSize="inherit" /> {item.user?.email || '-'}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={getPackageName(item.description)} 
                                size="small" 
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>{getStatusChip(item.transaction_type)}</TableCell>
                            <TableCell align="right" sx={{ 
                              fontWeight: 'bold',
                              color: item.transaction_type === 'refund' ? 'error.main' : 'success.main'
                            }}>
                              {formatCredits(item.amount, item.transaction_type)}
                            </TableCell>
                            <TableCell align="right" sx={{ 
                              fontWeight: 'bold',
                              color: item.transaction_type === 'refund' ? 'error.main' : 'success.main'
                            }}>
                              {formatCurrency(item.price)}
                            </TableCell>
                            <TableCell>
                              <Tooltip title={item.polar_order_id} arrow>
                                <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                                  {item.polar_order_id?.slice(0, 10)}...
                                </Typography>
                              </Tooltip>
                            </TableCell>
                            <TableCell>{formatDate(item.created_at)}</TableCell>
                            <TableCell align="center">
                              {item.transaction_type === 'purchase' && (
                                !isRefunded ? (
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    color="error"
                                    startIcon={<Cancel />}
                                    onClick={() => openRefundDialog(item)}
                                  >
                                    İade
                                  </Button>
                                ) : (
                                  <Chip label="İade Edildi" size="small" color="success" />
                                )
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                <TablePagination
                  rowsPerPageOptions={[10, 20, 50, 100]}
                  component="div"
                  count={filteredTransactions.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={(e, newPage) => setPage(newPage)}
                  onRowsPerPageChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value, 10));
                    setPage(0);
                  }}
                  labelRowsPerPage="Sayfa başına satır:"
                  labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
                />
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 1: İadeler */}
      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              İade İşlemleri
            </Typography>
            
            {loading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light' }}>
                      <TableCell>Kullanıcı</TableCell>
                      <TableCell>Paket</TableCell>
                      <TableCell align="right">İade Kredi</TableCell>
                      <TableCell align="right">İade Tutarı (TL)</TableCell>
                      <TableCell>Sipariş ID</TableCell>
                      <TableCell>Neden</TableCell>
                      <TableCell>Tarih</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredTransactions.filter(t => t.transaction_type === 'refund').length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          <Typography variant="body2" color="text.secondary">Henüz iade yok</Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredTransactions.filter(t => t.transaction_type === 'refund').map((item) => (
                        <TableRow key={item.id} hover>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                {item.user?.full_name || 'Bilinmiyor'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {item.user?.email || '-'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={getPackageName(item.description)} 
                              size="small" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'error.main', fontWeight: 'bold' }}>
                            -{item.amount}
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'error.main', fontWeight: 'bold' }}>
                            {formatCurrency(item.price)}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={item.polar_order_id} arrow>
                              <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                                {item.polar_order_id?.slice(0, 10)}...
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {item.description?.replace('İade - ', '') || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>{formatDate(item.created_at)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Endpoint Profilleri */}
      {tabValue === 2 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                📊 Endpoint Profilleri
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" onClick={handleInitDefaultProfiles}>
                  Varsayılanları Yükle
                </Button>
                <Button 
                  size="small" 
                  variant="contained" 
                  startIcon={<Add />}
                  onClick={() => { 
                    setEditingProfile(null); 
                    setProfileForm({
                      endpoint: '',
                      method: 'POST',
                      base_credit: 1,
                      pricing_type: 'DATA_POINTS',
                      algorithm_weight: 1.0,
                      avg_time_per_unit: 0.0,
                      is_active: true,
                      description: '',
                    });
                    setProfileDialogOpen(true); 
                  }}
                >
                  + Ekle
                </Button>
              </Box>
            </Box>
            {profilesLoading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>
            ) : endpointProfiles.length === 0 ? (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                Henüz endpoint profili yok. "Varsayılanları Yükle" butonuna tıklayın.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell>Endpoint</TableCell>
                      <TableCell>Method</TableCell>
                      <TableCell align="center">Base Credit</TableCell>
                      <TableCell>Pricing Type</TableCell>
                      <TableCell align="center">Weight</TableCell>
                      <TableCell align="center">Aktif</TableCell>
                      <TableCell align="center">İşlem</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {endpointProfiles.map((p) => (
                      <TableRow key={p.id} hover>
                        <TableCell sx={{ fontSize: '0.7rem', fontFamily: 'monospace' }}>{p.endpoint}</TableCell>
                        <TableCell>{p.method}</TableCell>
                        <TableCell align="center">{p.base_credit}</TableCell>
                        <TableCell>
                          <Chip label={p.pricing_type} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell align="center">{p.algorithm_weight}</TableCell>
                        <TableCell align="center">
                          <Chip label={p.is_active ? 'Aktif' : 'Pasif'} size="small" color={p.is_active ? 'success' : 'error'} />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton 
                            size="small" 
                            onClick={() => { 
                              setEditingProfile(p); 
                              setProfileForm({
                                endpoint: p.endpoint,
                                method: p.method,
                                base_credit: p.base_credit,
                                pricing_type: p.pricing_type,
                                algorithm_weight: p.algorithm_weight,
                                avg_time_per_unit: p.avg_time_per_unit,
                                is_active: p.is_active,
                                description: p.description || '',
                              });
                              setProfileDialogOpen(true); 
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton size="small" color="error" onClick={() => handleDeleteProfile(p.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Score Aralıkları */}
      {tabValue === 3 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                📈 Processing Score Aralıkları
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" onClick={handleInitDefaultRanges}>
                  Varsayılanları Yükle
                </Button>
                <Button 
                  size="small" 
                  variant="contained" 
                  startIcon={<Add />}
                  onClick={() => { 
                    setEditingRange(null); 
                    setRangeForm({
                      min_score: 0,
                      max_score: 10000,
                      credit_cost: 3,
                      is_active: true,
                      description: '',
                    });
                    setRangeDialogOpen(true); 
                  }}
                >
                  + Ekle
                </Button>
              </Box>
            </Box>
            {rangesLoading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>
            ) : scoreRanges.length === 0 ? (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                Henüz score aralığı yok. "Varsayılanları Yükle" butonuna tıklayın.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell align="center">Min Score</TableCell>
                      <TableCell align="center">Max Score</TableCell>
                      <TableCell align="center">Credit Cost</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="center">Aktif</TableCell>
                      <TableCell align="center">İşlem</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {scoreRanges.map((r) => (
                      <TableRow key={r.id} hover>
                        <TableCell align="center">{r.min_score.toLocaleString()}</TableCell>
                        <TableCell align="center">{r.max_score.toLocaleString()}</TableCell>
                        <TableCell align="center" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {r.credit_cost}
                        </TableCell>
                        <TableCell>{r.description || '-'}</TableCell>
                        <TableCell align="center">
                          <Chip label={r.is_active ? 'Aktif' : 'Pasif'} size="small" color={r.is_active ? 'success' : 'error'} />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton 
                            size="small" 
                            onClick={() => { 
                              setEditingRange(r); 
                              setRangeForm({
                                min_score: r.min_score,
                                max_score: r.max_score,
                                credit_cost: r.credit_cost,
                                is_active: r.is_active,
                                description: r.description || '',
                              });
                              setRangeDialogOpen(true); 
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton size="small" color="error" onClick={() => handleDeleteRange(r.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: İşlem Logları */}
      {tabValue === 4 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              📋 İşlem Kredisi Logları
            </Typography>
            {transactionsLoading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>
            ) : processingTransactions.length === 0 ? (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                Henüz işlem logu yok.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell>Kullanıcı</TableCell>
                      <TableCell>Endpoint</TableCell>
                      <TableCell align="center">Score</TableCell>
                      <TableCell align="center">Cost</TableCell>
                      <TableCell align="center">Bakiye</TableCell>
                      <TableCell align="center">Süre (ms)</TableCell>
                      <TableCell>Tarih</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {processingTransactions.map((t) => (
                      <TableRow key={t.id} hover>
                        <TableCell>{t.user_email || t.user_id}</TableCell>
                        <TableCell sx={{ fontSize: '0.65rem', fontFamily: 'monospace' }}>{t.endpoint}</TableCell>
                        <TableCell align="center">{t.processing_score}</TableCell>
                        <TableCell align="center" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {t.credit_cost}
                        </TableCell>
                        <TableCell align="center">{t.balance_after}</TableCell>
                        <TableCell align="center">{t.elapsed_time_ms?.toFixed(0) || '-'}</TableCell>
                        <TableCell>{formatDate(t.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* 🔄 İADE DIALOG */}
      <Dialog open={refundDialogOpen} onClose={() => setRefundDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Cancel color="error" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              🔄 İade Oluştur (Para + Kredi)
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <Box sx={{ mt: 2 }}>
              <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 3 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  👤 Kullanıcı Bilgileri
                </Typography>
                <Typography variant="body2">
                  <Person fontSize="inherit" /> {selectedOrder.user?.full_name || 'Bilinmiyor'}
                </Typography>
                <Typography variant="body2">
                  <Email fontSize="inherit" /> {selectedOrder.user?.email || '-'}
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  📦 Sipariş Bilgileri
                </Typography>
                <Typography variant="body2">Paket: {getPackageName(selectedOrder.description)}</Typography>
                <Typography variant="body2">Kredi: <strong>{selectedOrder.amount}</strong></Typography>
                <Typography variant="body2">Tutar: <strong>{formatCurrency(selectedOrder.price)}</strong></Typography>
                <Typography variant="body2">Sipariş ID: <strong>{selectedOrder.polar_order_id}</strong></Typography>
                <Typography variant="body2">Tarih: <strong>{formatDate(selectedOrder.created_at)}</strong></Typography>
              </Paper>

              <Alert severity="info" sx={{ mb: 2 }}>
                💡 Bu işlem hem <strong>kredi iadesi</strong> (kullanıcı bakiyesinden düşer) 
                hem de <strong>para iadesi</strong> (Polar üzerinden kredi kartına iade) yapacaktır.
              </Alert>

              <TextField
                fullWidth
                label="İade Miktarı (Kredi)"
                type="number"
                value={refundAmount}
                onChange={(e) => setRefundAmount(e.target.value)}
                sx={{ mb: 2 }}
                helperText="Boş bırakırsanız tam iade yapılır"
                slotProps={{
                  htmlInput: { min: 1, max: selectedOrder?.amount || 0 }
                }}
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>İade Nedeni</InputLabel>
                <Select
                  value={refundReason}
                  label="İade Nedeni"
                  onChange={(e) => setRefundReason(e.target.value)}
                >
                  <MenuItem value="customer_request">Müşteri Talebi</MenuItem>
                  <MenuItem value="duplicate">Çift Ödeme</MenuItem>
                  <MenuItem value="fraudulent">Sahtekarlık</MenuItem>
                  <MenuItem value="service_disruption">Hizmet Kesintisi</MenuItem>
                  <MenuItem value="satisfaction_guarantee">Memnuniyet Garantisi</MenuItem>
                  <MenuItem value="other">Diğer</MenuItem>
                </Select>
              </FormControl>

              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  ⚠️ İade işlemi geri alınamaz. Kullanıcının kredi bakiyesinden düşülecek 
                  ve Polar üzerinden para iadesi gerçekleştirilecektir.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRefundDialogOpen(false)}>İptal</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRefund}
            disabled={refundLoading}
            startIcon={refundLoading ? <CircularProgress size={20} /> : <Cancel />}
          >
            {refundLoading ? 'İşleniyor...' : 'İade Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 📝 PROFİL DIALOG */}
      <Dialog open={profileDialogOpen} onClose={() => setProfileDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              {editingProfile ? '✏️ Profil Düzenle' : '➕ Yeni Profil'}
            </Typography>
            <IconButton onClick={() => setProfileDialogOpen(false)} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Endpoint"
            value={profileForm.endpoint || ''}
            onChange={(e) => setProfileForm({ ...profileForm, endpoint: e.target.value })}
            sx={{ mt: 2 }}
            disabled={!!editingProfile}
            helperText={editingProfile ? 'Endpoint değiştirilemez' : 'Örn: /api/forecast/batch'}
          />
          <TextField
            fullWidth
            select
            label="Method"
            value={profileForm.method || 'POST'}
            onChange={(e) => setProfileForm({ ...profileForm, method: e.target.value })}
            sx={{ mt: 2 }}
          >
            <MenuItem value="POST">POST</MenuItem>
            <MenuItem value="GET">GET</MenuItem>
            <MenuItem value="PUT">PUT</MenuItem>
            <MenuItem value="DELETE">DELETE</MenuItem>
          </TextField>
          <TextField
            fullWidth
            type="number"
            label="Base Credit"
            value={profileForm.base_credit || 1}
            onChange={(e) => setProfileForm({ ...profileForm, base_credit: parseInt(e.target.value) || 1 })}
            sx={{ mt: 2 }}
            helperText="Taban kredi miktarı"
          />
          <TextField
            fullWidth
            select
            label="Pricing Type"
            value={profileForm.pricing_type || 'DATA_POINTS'}
            onChange={(e) => setProfileForm({ ...profileForm, pricing_type: e.target.value })}
            sx={{ mt: 2 }}
          >
            <MenuItem value="FIXED">FIXED</MenuItem>
            <MenuItem value="DATA_POINTS">DATA_POINTS</MenuItem>
            <MenuItem value="DATA_POINTS_ITERATION">DATA_POINTS_ITERATION</MenuItem>
            <MenuItem value="AI_USAGE">AI_USAGE</MenuItem>
            <MenuItem value="CUSTOM">CUSTOM</MenuItem>
          </TextField>
          <TextField
            fullWidth
            type="number"
            label="Algorithm Weight"
            value={profileForm.algorithm_weight || 1.0}
            onChange={(e) => setProfileForm({ ...profileForm, algorithm_weight: parseFloat(e.target.value) || 1.0 })}
            sx={{ mt: 2 }}
              slotProps={{
              htmlInput: { step: 0.1 }
            }}
          />
          <TextField
            fullWidth
            label="Description"
            value={profileForm.description || ''}
            onChange={(e) => setProfileForm({ ...profileForm, description: e.target.value })}
            sx={{ mt: 2 }}
            multiline
            rows={2}
          />
          <FormControlLabel
            control={
              <Switch
                checked={profileForm.is_active !== false}
                onChange={(e) => setProfileForm({ ...profileForm, is_active: e.target.checked })}
              />
            }
            label="Aktif"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProfileDialogOpen(false)}>İptal</Button>
          <Button 
            variant="contained" 
            onClick={editingProfile ? handleUpdateProfile : handleCreateProfile}
          >
            {editingProfile ? 'Güncelle' : 'Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 📈 RANGE DIALOG */}
      <Dialog open={rangeDialogOpen} onClose={() => setRangeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              {editingRange ? '✏️ Aralık Düzenle' : '➕ Yeni Aralık'}
            </Typography>
            <IconButton onClick={() => setRangeDialogOpen(false)} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            type="number"
            label="Min Score"
            value={rangeForm.min_score || 0}
            onChange={(e) => setRangeForm({ ...rangeForm, min_score: parseInt(e.target.value) || 0 })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            type="number"
            label="Max Score"
            value={rangeForm.max_score || 10000}
            onChange={(e) => setRangeForm({ ...rangeForm, max_score: parseInt(e.target.value) || 10000 })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            type="number"
            label="Credit Cost"
            value={rangeForm.credit_cost || 3}
            onChange={(e) => setRangeForm({ ...rangeForm, credit_cost: parseInt(e.target.value) || 3 })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            value={rangeForm.description || ''}
            onChange={(e) => setRangeForm({ ...rangeForm, description: e.target.value })}
            sx={{ mt: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={rangeForm.is_active !== false}
                onChange={(e) => setRangeForm({ ...rangeForm, is_active: e.target.checked })}
              />
            }
            label="Aktif"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRangeDialogOpen(false)}>İptal</Button>
          <Button 
            variant="contained" 
            onClick={editingRange ? handleUpdateRange : handleCreateRange}
          >
            {editingRange ? 'Güncelle' : 'Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}