import { useState, useEffect } from 'react';
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
  Avatar,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
} from '@mui/material';
import {
  Person,
  Email,
  Business,
  AttachMoney,
  History,
  TrendingUp,
  TrendingDown,
  Refresh,
  Download,
  Visibility,
  Close,
  Lock,
  CheckCircle,
  Edit,
  Save,
  Cancel,
  AdminPanelSettings,
  CalendarToday,
  LocationCity,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

interface TokenHistoryItem {
  id: number;
  endpoint: string;
  cost: number;
  balance_after: number;
  created_at: string;
  type: 'spend' | 'purchase' | 'bonus';
}

interface TransactionItem {
  id: number;
  amount: number;
  type: string;
  description: string;
  balance_after: number;
  created_at: string;
}

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  
  // ✅ Profil formu
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [companyName, setCompanyName] = useState(user?.company_name || '');
  const [isEditing, setIsEditing] = useState(false);
  
  // ✅ Şifre değiştirme
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);
  
  // ✅ Tab
  const [tabValue, setTabValue] = useState(0);
  
  // ✅ Token Geçmişi
  const [tokenHistory, setTokenHistory] = useState<TokenHistoryItem[]>([]);
  const [tokenTotal, setTokenTotal] = useState(0);
  const [tokenPage, setTokenPage] = useState(0);
  const [tokenRowsPerPage, setTokenRowsPerPage] = useState(5);
  const [tokenLoading, setTokenLoading] = useState(false);
  
  // ✅ İşlem Geçmişi
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [transactionTotal, setTransactionTotal] = useState(0);
  const [transactionPage, setTransactionPage] = useState(0);
  const [transactionRowsPerPage, setTransactionRowsPerPage] = useState(5);
  const [transactionLoading, setTransactionLoading] = useState(false);
  
  // ✅ Detay Dialog
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);

  // ✅ Token geçmişini getir (sadece cost > 0)
  const fetchTokenHistory = async (page: number = 0) => {
    setTokenLoading(true);
    try {
      const res = await api.get('/api/profile/token-history', {
        params: {
          limit: tokenRowsPerPage,
          offset: page * tokenRowsPerPage
        }
      });
      if (res.data.success) {
        setTokenHistory(res.data.history || []);
        setTokenTotal(res.data.total || 0);
      }
    } catch (error) {
      console.error('❌ Token geçmişi hatası:', error);
    } finally {
      setTokenLoading(false);
    }
  };

  // ✅ İşlem geçmişini getir
  const fetchTransactions = async (page: number = 0) => {
    setTransactionLoading(true);
    try {
      const res = await api.get('/api/profile/transactions', {
        params: {
          limit: transactionRowsPerPage,
          offset: page * transactionRowsPerPage
        }
      });
      if (res.data.success) {
        setTransactions(res.data.transactions || []);
        setTransactionTotal(res.data.total || 0);
      }
    } catch (error) {
      console.error('❌ İşlem geçmişi hatası:', error);
    } finally {
      setTransactionLoading(false);
    }
  };

  // ✅ Profil güncelle
  const handleSaveProfile = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.put('/api/profile/', {
        full_name: fullName,
        company_name: companyName
      });
      if (res.data.success) {
        setSuccess('Profil başarıyla güncellendi!');
        updateUser(res.data.user);
        setIsEditing(false);
        setSnackbar({
          open: true,
          message: '✅ Profil başarıyla güncellendi!',
          severity: 'success',
        });
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Profil güncellenemedi');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Profil güncellenemedi',
        severity: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  // ✅ Şifre değiştir
  const handleChangePassword = async () => {
    setPasswordError(null);
    setPasswordSuccess(null);
    setPasswordLoading(true);
    
    if (newPassword.length < 6) {
      setPasswordError('Yeni şifre en az 6 karakter olmalı');
      setPasswordLoading(false);
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordError('Şifreler eşleşmiyor');
      setPasswordLoading(false);
      return;
    }
    
    try {
      const res = await api.post('/api/profile/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      
      if (res.data.success) {
        setPasswordSuccess('Şifre başarıyla değiştirildi!');
        setSnackbar({
          open: true,
          message: '✅ Şifre başarıyla değiştirildi!',
          severity: 'success',
        });
        setTimeout(() => {
          setPasswordDialog(false);
          setPasswordSuccess(null);
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
        }, 2000);
      }
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Şifre değiştirilemedi');
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Şifre değiştirilemedi',
        severity: 'error',
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  // ✅ Tab değişimi
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    if (newValue === 0) {
      fetchTokenHistory(0);
      setTokenPage(0);
    } else if (newValue === 1) {
      fetchTransactions(0);
      setTransactionPage(0);
    }
  };

  // ✅ Pagination
  const handleTokenPageChange = (event: unknown, newPage: number) => {
    setTokenPage(newPage);
    fetchTokenHistory(newPage);
  };

  const handleTransactionPageChange = (event: unknown, newPage: number) => {
    setTransactionPage(newPage);
    fetchTransactions(newPage);
  };

  // ✅ İlk yükleme
  useEffect(() => {
    fetchTokenHistory(0);
  }, []);

  // ✅ Detay göster
  const showDetail = (item: any) => {
    setSelectedItem(item);
    setDetailOpen(true);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  const getTypeChip = (type: string) => {
    switch(type) {
      case 'spend':
        return <Chip label="Harcama" size="small" color="error" icon={<TrendingDown />} />;
      case 'purchase':
        return <Chip label="Satın Alma" size="small" color="success" icon={<TrendingUp />} />;
      case 'bonus':
        return <Chip label="Bonus" size="small" color="warning" icon={<TrendingUp />} />;
      default:
        return <Chip label={type} size="small" />;
    }
  };

  const getEndpointName = (endpoint: string) => {
    const names: Record<string, string> = {
      '/api/forecast/batch': 'Talep Tahmini',
      '/api/forecast/batch/async': 'Talep Tahmini (ASYNC)',
      '/api/safety-stock': 'Emniyet Stoğu',
      '/api/simulate': 'Monte Carlo Simülasyonu',
      '/api/backtest': 'Backtest',
      '/api/supplier/optimize-shares': 'Tedarikçi Analizi',
    };
    return names[endpoint] || endpoint;
  };

  return (
    <Box>
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          👤 Profil Yönetimi
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* 📌 Profil Kartı */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ position: 'relative', overflow: 'visible' }}>
            {/* Arka plan gradient */}
            <Box
              sx={{
                height: 100,
                background: 'linear-gradient(135deg, #1f4e79 0%, #1976d2 100%)',
                borderRadius: '12px 12px 0 0',
                position: 'relative',
              }}
            />
            
            {/* Avatar */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mt: -5,
                position: 'relative',
                zIndex: 1,
              }}
            >
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: '#1f4e79',
                  fontSize: 32,
                  border: '4px solid white',
                  boxShadow: 3,
                }}
              >
                {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
              </Avatar>
            </Box>

            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {user?.full_name || 'Kullanıcı'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {user?.email}
              </Typography>
              
              <Chip
                label={`🪙 ${user?.token_balance || 0} Token`}
                color="warning"
                size="small"
                sx={{ mb: 1 }}
              />
              
              <Divider sx={{ my: 2 }} />

              {/* Bilgiler */}
              <Box sx={{ textAlign: 'left', '& .MuiTypography-root': { mb: 1 } }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Business fontSize="small" color="action" />
                  <strong>Şirket:</strong> {user?.company_name || 'Belirtilmemiş'}
                </Typography>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocationCity fontSize="small" color="action" />
                  <strong>Sektör:</strong> {user?.sector_name || 'Belirtilmemiş'}
                </Typography>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarToday fontSize="small" color="action" />
                  <strong>Üyelik:</strong> {user?.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Butonlar */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
                <Button
                  variant={isEditing ? 'contained' : 'outlined'}
                  size="small"
                  startIcon={isEditing ? <Save /> : <Edit />}
                  onClick={isEditing ? handleSaveProfile : () => setIsEditing(true)}
                  disabled={saving}
                >
                  {isEditing ? (saving ? 'Kaydediliyor...' : 'Kaydet') : 'Düzenle'}
                </Button>
                {isEditing && (
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    startIcon={<Cancel />}
                    onClick={() => {
                      setIsEditing(false);
                      setFullName(user?.full_name || '');
                      setCompanyName(user?.company_name || '');
                    }}
                  >
                    İptal
                  </Button>
                )}
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Lock />}
                  onClick={() => setPasswordDialog(true)}
                >
                  Şifre Değiştir
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Profil Düzenleme Alanı */}
          {isEditing && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                  ✏️ Profil Bilgilerini Düzenle
                </Typography>
                <TextField
                  fullWidth
                  label="Ad Soyad"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  sx={{ mb: 2 }}
                  slotProps={{ input: { startAdornment: <Person sx={{ mr: 1, color: 'text.secondary' }} /> } }}
                />
                <TextField
                  fullWidth
                  label="Şirket Adı"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  sx={{ mb: 2 }}
                  slotProps={{ input: { startAdornment: <Business sx={{ mr: 1, color: 'text.secondary' }} /> } }}
                />
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* 📌 Geçmiş Tab'ları */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
              >
                <Tab label={`🪙 Token Harcamaları (${tokenTotal})`} />
                <Tab label={`💳 İşlem Geçmişi (${transactionTotal})`} />
              </Tabs>

              {/* Tab 0: Token Geçmişi */}
              {tabValue === 0 && (
                <Box>
                  {tokenLoading ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : (
                    <>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ bgcolor: 'grey.50' }}>
                              <TableCell>İşlem</TableCell>
                              <TableCell align="right">Maliyet</TableCell>
                              <TableCell align="right">Bakiye</TableCell>
                              <TableCell>Tarih</TableCell>
                              <TableCell align="center">İşlem</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {tokenHistory.length === 0 ? (
                              <TableRow>
                                <TableCell colSpan={5} align="center">
                                  <Typography variant="body2" color="text.secondary">Henüz token harcaması yok</Typography>
                                </TableCell>
                              </TableRow>
                            ) : (
                              tokenHistory.map((item) => (
                                <TableRow key={item.id} hover>
                                  <TableCell>{getEndpointName(item.endpoint)}</TableCell>
                                  <TableCell align="right" sx={{ color: 'error.main', fontWeight: 'bold' }}>
                                    -{item.cost}
                                  </TableCell>
                                  <TableCell align="right">{item.balance_after}</TableCell>
                                  <TableCell>{formatDate(item.created_at)}</TableCell>
                                  <TableCell align="center">
                                    <Tooltip title="Detay">
                                      <IconButton size="small" onClick={() => showDetail(item)}>
                                        <Visibility fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  </TableCell>
                                </TableRow>
                              ))
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <TablePagination
                        rowsPerPageOptions={[5, 10, 25]}
                        component="div"
                        count={tokenTotal}
                        rowsPerPage={tokenRowsPerPage}
                        page={tokenPage}
                        onPageChange={handleTokenPageChange}
                        onRowsPerPageChange={(e) => {
                          setTokenRowsPerPage(parseInt(e.target.value, 10));
                          setTokenPage(0);
                          fetchTokenHistory(0);
                        }}
                        labelRowsPerPage="Sayfa başına satır:"
                      />
                    </>
                  )}
                </Box>
              )}

              {/* Tab 1: İşlem Geçmişi */}
              {tabValue === 1 && (
                <Box>
                  {transactionLoading ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : (
                    <>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ bgcolor: 'grey.50' }}>
                              <TableCell>Tür</TableCell>
                              <TableCell>Açıklama</TableCell>
                              <TableCell align="right">Miktar</TableCell>
                              <TableCell align="right">Bakiye</TableCell>
                              <TableCell>Tarih</TableCell>
                              <TableCell align="center">İşlem</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {transactions.length === 0 ? (
                              <TableRow>
                                <TableCell colSpan={6} align="center">
                                  <Typography variant="body2" color="text.secondary">Henüz işlem geçmişi yok</Typography>
                                </TableCell>
                              </TableRow>
                            ) : (
                              transactions.map((item) => (
                                <TableRow key={item.id} hover>
                                  <TableCell>{getTypeChip(item.type)}</TableCell>
                                  <TableCell>{item.description}</TableCell>
                                  <TableCell align="right" sx={{ color: item.amount > 0 ? 'success.main' : 'error.main', fontWeight: 'bold' }}>
                                    {item.amount > 0 ? '+' : ''}{item.amount}
                                  </TableCell>
                                  <TableCell align="right">{item.balance_after}</TableCell>
                                  <TableCell>{formatDate(item.created_at)}</TableCell>
                                  <TableCell align="center">
                                    <Tooltip title="Detay">
                                      <IconButton size="small" onClick={() => showDetail(item)}>
                                        <Visibility fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  </TableCell>
                                </TableRow>
                              ))
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <TablePagination
                        rowsPerPageOptions={[5, 10, 25]}
                        component="div"
                        count={transactionTotal}
                        rowsPerPage={transactionRowsPerPage}
                        page={transactionPage}
                        onPageChange={handleTransactionPageChange}
                        onRowsPerPageChange={(e) => {
                          setTransactionRowsPerPage(parseInt(e.target.value, 10));
                          setTransactionPage(0);
                          fetchTransactions(0);
                        }}
                        labelRowsPerPage="Sayfa başına satır:"
                      />
                    </>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ✅ Şifre Değiştirme Dialog */}
      <Dialog open={passwordDialog} onClose={() => setPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">🔒 Şifre Değiştir</Typography>
            <IconButton onClick={() => setPasswordDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {passwordError && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setPasswordError(null)}>
              {passwordError}
            </Alert>
          )}
          {passwordSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {passwordSuccess}
            </Alert>
          )}
          <TextField
            fullWidth
            type="password"
            label="Mevcut Şifre"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            sx={{ mt: 2 }}
            slotProps={{ input: { startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          />
          <TextField
            fullWidth
            type="password"
            label="Yeni Şifre"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{ mt: 2 }}
            helperText="En az 6 karakter"
            slotProps={{ input: { startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          />
          <TextField
            fullWidth
            type="password"
            label="Yeni Şifre (Tekrar)"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            sx={{ mt: 2 }}
            slotProps={{ input: { startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialog(false)}>İptal</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={passwordLoading || !currentPassword || !newPassword || !confirmPassword}
          >
            {passwordLoading ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ✅ Detay Dialog */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📋 İşlem Detayı</Typography>
            <IconButton onClick={() => setDetailOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedItem && (
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>ID: {selectedItem.id}</Typography>
              <Divider sx={{ my: 1 }} />
              {selectedItem.endpoint && (
                <Typography variant="body2">
                  <strong>İşlem:</strong> {getEndpointName(selectedItem.endpoint)}
                </Typography>
              )}
              {selectedItem.cost !== undefined && (
                <Typography variant="body2">
                  <strong>Maliyet:</strong> <span style={{ color: 'red', fontWeight: 'bold' }}>-{selectedItem.cost}</span> Token
                </Typography>
              )}
              {selectedItem.amount !== undefined && (
                <Typography variant="body2">
                  <strong>Miktar:</strong> {selectedItem.amount > 0 ? '+' : ''}{selectedItem.amount} Token
                </Typography>
              )}
              <Typography variant="body2">
                <strong>Bakiye:</strong> {selectedItem.balance_after}
              </Typography>
              {selectedItem.description && (
                <Typography variant="body2">
                  <strong>Açıklama:</strong> {selectedItem.description}
                </Typography>
              )}
              <Typography variant="body2">
                <strong>Tarih:</strong> {formatDate(selectedItem.created_at)}
              </Typography>
              {selectedItem.type && (
                <Box sx={{ mt: 1 }}>
                  <strong>Tür:</strong> {getTypeChip(selectedItem.type)}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}