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
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

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
        refund_type: 'money', // ✅ Tek seçenek: Para + Kredi iadesi
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
          onClick={() => { fetchTransactions(); fetchStats(); fetchUserStats(); }}
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
        <Tab label="👥 Kullanıcı İstatistikleri" />
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
                    {/* 📋 Tablo Satırı */}
                    <TableBody>
                      {paginatedTransactions.map((item) => {
                        // ✅ İade kontrolünü burada yap
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
                            
                            {/* ✅ İade Butonu - Düzeltilmiş */}
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

      {/* Tab 2: Kullanıcı İstatistikleri */}
      {tabValue === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
              👥 Kullanıcı Bazlı İstatistikler
            </Typography>
            
            {statsLoading ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : userStats.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary">Kullanıcı verisi yok</Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.50' }}>
                      <TableCell>Kullanıcı</TableCell>
                      <TableCell align="right">Toplam Satın Alma</TableCell>
                      <TableCell align="right">İade Sayısı</TableCell>
                      <TableCell align="right">Net Kredi</TableCell>
                      <TableCell align="center">Durum</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {userStats.map((stat) => (
                      <TableRow key={stat.user_id} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {stat.full_name || 'Bilinmiyor'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {stat.email}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">{stat.total_purchases}</TableCell>
                        <TableCell align="right" sx={{ color: stat.total_refunds > 0 ? 'error.main' : 'text.secondary' }}>
                          {stat.total_refunds}
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                          {stat.net_credits}
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={stat.net_credits > 0 ? 'Aktif' : 'Pasif'} 
                            size="small" 
                            color={stat.net_credits > 0 ? 'success' : 'error'} 
                          />
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

      {/* 🔄 İADE DIALOG - Tek Seçenek: Para + Kredi İadesi */}
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

              {/* ✅ Uyarı - Tek seçenek olduğu için */}
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
                  input: {
                    inputProps: { min: 1, max: selectedOrder?.amount || 0 }
                  }
                }}
              />

              {/* ✅ İade Nedeni Seçimi */}
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
    </Box>
  );
}