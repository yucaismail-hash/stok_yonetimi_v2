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
  Receipt,
  SupportAgent,
  Send,
  ReceiptLong,
  Home,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import api from '../../services/api';

interface TransactionItem {
  id: number;
  amount: number;
  type: string;
  description: string;
  balance_after: number;
  created_at: string;
  price?: number;
  tax?: number;
  total_price?: number;
  polar_order_id?: string;
}

interface SupportTicket {
  id: number;
  subject: string;
  message: string;
  priority: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
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
  
  // 🆕 FATURA BİLGİLERİ
  const [billingAddress, setBillingAddress] = useState(user?.billing_address || '');
  const [billingCity, setBillingCity] = useState(user?.billing_city || '');
  const [billingState, setBillingState] = useState(user?.billing_state || '');
  const [billingCountry, setBillingCountry] = useState(user?.billing_country || 'TR');
  const [billingPostalCode, setBillingPostalCode] = useState(user?.billing_postal_code || '');
  const [taxId, setTaxId] = useState(user?.tax_id || '');
  const [taxOffice, setTaxOffice] = useState(user?.tax_office || '');
  const [identityNumber, setIdentityNumber] = useState(user?.identity_number || '');
  
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
  
  // ✅ İşlem Geçmişi
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [transactionTotal, setTransactionTotal] = useState(0);
  const [transactionPage, setTransactionPage] = useState(0);
  const [transactionRowsPerPage, setTransactionRowsPerPage] = useState(10);
  const [transactionLoading, setTransactionLoading] = useState(false);
  
  // ✅ Destek Talepleri
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [ticketDialogOpen, setTicketDialogOpen] = useState(false);
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMessage, setTicketMessage] = useState('');
  const [ticketPriority, setTicketPriority] = useState('medium');
  const [ticketLoading, setTicketLoading] = useState(false);
  
  // ✅ Detay Dialog
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [invoiceLoading, setInvoiceLoading] = useState(false);

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

  // ✅ Destek taleplerini getir
  const fetchTickets = async () => {
    try {
      const res = await api.get('/api/profile/support-tickets');
      if (res.data.success) {
        setTickets(res.data.tickets || []);
      }
    } catch (error) {
      console.error('❌ Destek talebi hatası:', error);
    }
  };

  // ✅ Destek talebi oluştur
  const handleCreateTicket = async () => {
    if (!ticketSubject.trim() || !ticketMessage.trim()) {
      setSnackbar({
        open: true,
        message: 'Lütfen konu ve mesaj girin.',
        severity: 'error',
      });
      return;
    }
    
    setTicketLoading(true);
    try {
      const res = await api.post('/api/profile/support-ticket', {
        subject: ticketSubject,
        message: ticketMessage,
        priority: ticketPriority,
      });
      
      if (res.data.success) {
        setSnackbar({
          open: true,
          message: '✅ Destek talebiniz başarıyla oluşturuldu.',
          severity: 'success',
        });
        setTicketDialogOpen(false);
        setTicketSubject('');
        setTicketMessage('');
        setTicketPriority('medium');
        fetchTickets();
      }
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Destek talebi oluşturulamadı.',
        severity: 'error',
      });
    } finally {
      setTicketLoading(false);
    }
  };

  // ✅ Profil güncelle (Fatura bilgileri dahil)
  const handleSaveProfile = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.put('/api/profile/', {
        full_name: fullName,
        company_name: companyName,
        billing_address: billingAddress,
        billing_city: billingCity,
        billing_state: billingState,
        billing_country: billingCountry,
        billing_postal_code: billingPostalCode,
        tax_id: taxId,
        tax_office: taxOffice,
        identity_number: identityNumber,
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

  // ✅ İşlem detayını göster
  const showDetail = async (item: any) => {
    setSelectedItem(item);
    setDetailOpen(true);
  };

  // ✅ PDF indir
  const handleDownloadInvoice = async (transactionId: number) => {
    setInvoiceLoading(true);
    try {
      const res = await api.get(`/api/profile/transaction/${transactionId}/polar-invoice`);
      if (res.data.success) {
        if (res.data.type === 'dashboard' && res.data.dashboard_url) {
          window.open(res.data.dashboard_url, '_blank');
          setSnackbar({
            open: true,
            message: '📄 Fatura sayfası yeni sekmede açıldı.',
            severity: 'info',
          });
          setInvoiceLoading(false);
          return;
        }
        
        if (res.data.pdf_base64) {
          const link = document.createElement('a');
          link.href = `data:application/pdf;base64,${res.data.pdf_base64}`;
          link.download = res.data.filename || `fatura_${transactionId}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          setSnackbar({
            open: true,
            message: '✅ Fatura başarıyla indirildi.',
            severity: 'success',
          });
        }
      }
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Fatura indirilemedi.',
        severity: 'error',
      });
    } finally {
      setInvoiceLoading(false);
    }
  };

  // ✅ Tab değişimi
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    if (newValue === 0) {
      fetchTransactions(0);
      setTransactionPage(0);
    } else if (newValue === 1) {
      fetchTickets();
    }
  };

  // ✅ Pagination
  const handleTransactionPageChange = (event: unknown, newPage: number) => {
    setTransactionPage(newPage);
    fetchTransactions(newPage);
  };

  // ✅ İlk yükleme
  useEffect(() => {
    fetchTransactions(0);
  }, []);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  const getTypeChip = (type: string) => {
    switch(type) {
      case 'purchase':
        return <Chip label="Satın Alma" size="small" color="success" icon={<TrendingUp />} />;
      case 'refund':
        return <Chip label="İade" size="small" color="error" icon={<TrendingDown />} />;
      case 'bonus':
        return <Chip label="Bonus" size="small" color="warning" icon={<TrendingUp />} />;
      case 'spend':
        return <Chip label="Harcama" size="small" color="error" icon={<TrendingDown />} />;
      default:
        return <Chip label={type} size="small" />;
    }
  };

  const getPriorityChip = (priority: string) => {
    switch(priority) {
      case 'high':
        return <Chip label="Yüksek" size="small" color="error" />;
      case 'medium':
        return <Chip label="Orta" size="small" color="warning" />;
      case 'low':
        return <Chip label="Düşük" size="small" color="success" />;
      default:
        return <Chip label={priority} size="small" />;
    }
  };

  const getStatusChip = (status: string) => {
    switch(status) {
      case 'open':
        return <Chip label="Açık" size="small" color="error" />;
      case 'in_progress':
        return <Chip label="İşleniyor" size="small" color="warning" />;
      case 'resolved':
        return <Chip label="Çözüldü" size="small" color="success" />;
      case 'closed':
        return <Chip label="Kapalı" size="small" color="default" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  // 📊 İstatistikler
  const stats = {
    total_credits: user?.token_balance || 0,
    total_purchases: transactions.filter(t => t.type === 'purchase').reduce((sum, t) => sum + t.amount, 0),
    total_refunds: transactions.filter(t => t.type === 'refund').reduce((sum, t) => sum + Math.abs(t.amount), 0),
    total_transactions: transactions.length,
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
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SupportAgent />}
            onClick={() => setTicketDialogOpen(true)}
          >
            Destek Talebi
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => fetchTransactions(transactionPage)}
            disabled={transactionLoading}
          >
            Yenile
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* 📌 Profil Kartı */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ position: 'relative', overflow: 'visible' }}>
            <Box
              sx={{
                height: 120,
                background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #1976d2 100%)',
                borderRadius: '12px 12px 0 0',
                position: 'relative',
              }}
            />
            
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mt: -6,
                position: 'relative',
                zIndex: 1,
              }}
            >
              <Avatar
                sx={{
                  width: 96,
                  height: 96,
                  bgcolor: '#1a237e',
                  fontSize: 40,
                  border: '4px solid white',
                  boxShadow: 3,
                }}
              >
                {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
              </Avatar>
            </Box>

            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                {user?.full_name || 'Kullanıcı'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {user?.email}
              </Typography>
              
              <Chip
                label={`🪙 ${user?.token_balance || 0} Kredi`}
                color="warning"
                size="medium"
                sx={{ mb: 2, fontWeight: 'bold', fontSize: '0.9rem' }}
              />
              
              <Divider sx={{ my: 2 }} />

              {/* İstatistik Kartları */}
              <Grid container spacing={1} sx={{ mb: 2 }}>
                <Grid size={{ xs: 6 }}>
                  <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="caption" color="text.secondary">Toplam Satın Alma</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{stats.total_purchases}</Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'error.light' }}>
                    <Typography variant="caption" color="text.secondary">Toplam İade</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{stats.total_refunds}</Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="caption" color="text.secondary">Toplam İşlem</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{stats.total_transactions}</Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.light' }}>
                    <Typography variant="caption" color="text.secondary">Mevcut Kredi</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{stats.total_credits}</Typography>
                  </Paper>
                </Grid>
              </Grid>

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
                      setBillingAddress(user?.billing_address || '');
                      setBillingCity(user?.billing_city || '');
                      setBillingState(user?.billing_state || '');
                      setBillingCountry(user?.billing_country || 'TR');
                      setBillingPostalCode(user?.billing_postal_code || '');
                      setTaxId(user?.tax_id || '');
                      setTaxOffice(user?.tax_office || '');
                      setIdentityNumber(user?.identity_number || '');
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

          {/* 🆕 Fatura Bilgilerini Düzenleme Alanı */}
          {isEditing && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                  ✏️ Profil ve Fatura Bilgilerini Düzenle
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
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  🏢 Fatura Bilgileri
                </Typography>
                
                <TextField
                  fullWidth
                  label="Fatura Adresi"
                  value={billingAddress}
                  onChange={(e) => setBillingAddress(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: İstiklal Cad. No:123"
                  slotProps={{ input: { startAdornment: <Home sx={{ mr: 1, color: 'text.secondary' }} /> } }}
                />
                <TextField
                  fullWidth
                  label="Şehir"
                  value={billingCity}
                  onChange={(e) => setBillingCity(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: İstanbul"
                />
                <TextField
                  fullWidth
                  label="İl/İlçe"
                  value={billingState}
                  onChange={(e) => setBillingState(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: Kadıköy"
                />
                <TextField
                  fullWidth
                  label="Posta Kodu"
                  value={billingPostalCode}
                  onChange={(e) => setBillingPostalCode(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: 34700"
                />
                <TextField
                  fullWidth
                  select
                  label="Ülke"
                  value={billingCountry}
                  onChange={(e) => setBillingCountry(e.target.value)}
                  sx={{ mb: 2 }}
                  slotProps={{
                    select: {
                      native: true,
                    },
                  }}
                >
                  <option value="TR">Türkiye</option>
                  <option value="US">Amerika Birleşik Devletleri</option>
                  <option value="GB">Birleşik Krallık</option>
                  <option value="DE">Almanya</option>
                  <option value="FR">Fransa</option>
                  <option value="IT">İtalya</option>
                </TextField>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  📋 Vergi Bilgileri
                </Typography>
                
                <TextField
                  fullWidth
                  label="Vergi Numarası"
                  value={taxId}
                  onChange={(e) => setTaxId(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: 1234567890"
                />
                <TextField
                  fullWidth
                  label="Vergi Dairesi"
                  value={taxOffice}
                  onChange={(e) => setTaxOffice(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: İstanbul Vergi Dairesi"
                />
                <TextField
                  fullWidth
                  label="TC Kimlik Numarası"
                  value={identityNumber}
                  onChange={(e) => setIdentityNumber(e.target.value)}
                  sx={{ mb: 2 }}
                  placeholder="Örn: 12345678901"
                />

                <Button
                  fullWidth
                  variant="contained"
                  color="primary"
                  onClick={handleSaveProfile}
                  disabled={saving}
                  sx={{ mt: 2 }}
                >
                  {saving ? 'Kaydediliyor...' : 'Bilgileri Güncelle'}
                </Button>
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
                <Tab label={`💳 İşlem Geçmişi (${transactionTotal})`} />
                <Tab label={`📩 Destek Taleplerim (${tickets.length})`} />
              </Tabs>

              {/* Tab 0: İşlem Geçmişi */}
              {tabValue === 0 && (
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
                              <TableCell align="right">Toplam (TL)</TableCell>
                              <TableCell align="right">Bakiye</TableCell>
                              <TableCell>Tarih</TableCell>
                              <TableCell align="center">İşlem</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {transactions.length === 0 ? (
                              <TableRow>
                                <TableCell colSpan={7} align="center">
                                  <Typography variant="body2" color="text.secondary">Henüz işlem geçmişi yok</Typography>
                                </TableCell>
                              </TableRow>
                            ) : (
                              transactions.map((item) => {
                                const totalPrice = item.total_price || (item.price || 0) + (item.tax || 0);
                                return (
                                  <TableRow key={item.id} hover>
                                    <TableCell>{getTypeChip(item.type)}</TableCell>
                                    <TableCell>{item.description}</TableCell>
                                    <TableCell align="right" sx={{ 
                                      fontWeight: 'bold',
                                      color: item.amount > 0 ? 'success.main' : 'error.main'
                                    }}>
                                      {item.amount > 0 ? '+' : ''}{item.amount}
                                    </TableCell>
                                    <TableCell align="right" sx={{ 
                                      fontWeight: 'bold',
                                      color: item.amount > 0 ? 'success.main' : 'error.main'
                                    }}>
                                      {totalPrice ? `₺${totalPrice.toFixed(2)}` : '-'}
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
                                );
                              })
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <TablePagination
                        rowsPerPageOptions={[10, 25, 50]}
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

              {/* Tab 1: Destek Talepleri */}
              {tabValue === 1 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<SupportAgent />}
                      onClick={() => setTicketDialogOpen(true)}
                    >
                      Yeni Talep
                    </Button>
                  </Box>
                  
                  {tickets.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography variant="body2" color="text.secondary">Henüz destek talebiniz yok</Typography>
                    </Box>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow sx={{ bgcolor: 'grey.50' }}>
                            <TableCell>Konu</TableCell>
                            <TableCell>Öncelik</TableCell>
                            <TableCell>Durum</TableCell>
                            <TableCell>Tarih</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {tickets.map((ticket) => (
                            <TableRow key={ticket.id} hover>
                              <TableCell>{ticket.subject}</TableCell>
                              <TableCell>{getPriorityChip(ticket.priority)}</TableCell>
                              <TableCell>{getStatusChip(ticket.status)}</TableCell>
                              <TableCell>{formatDate(ticket.created_at)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
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
              <Typography variant="body2">
                <strong>Tür:</strong> {getTypeChip(selectedItem.type)}
              </Typography>
              <Typography variant="body2">
                <strong>Açıklama:</strong> {selectedItem.description}
              </Typography>
              <Typography variant="body2">
                <strong>Miktar:</strong> {selectedItem.amount > 0 ? '+' : ''}{selectedItem.amount} Kredi
              </Typography>
              
              {/* 🆕 Fiyat bilgileri */}
              {selectedItem.price !== undefined && (
                <>
                  <Typography variant="body2">
                    <strong>KDV'siz Tutar:</strong> ₺{(selectedItem.price || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2">
                    <strong>KDV:</strong> ₺{(selectedItem.tax || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    <strong>Toplam:</strong> ₺{((selectedItem.price || 0) + (selectedItem.tax || 0)).toFixed(2)}
                  </Typography>
                </>
              )}
              
              <Typography variant="body2">
                <strong>Bakiye:</strong> {selectedItem.balance_after}
              </Typography>
              <Typography variant="body2">
                <strong>Tarih:</strong> {formatDate(selectedItem.created_at)}
              </Typography>
              {selectedItem.polar_order_id && (
                <Typography variant="body2">
                  <strong>Sipariş ID:</strong> {selectedItem.polar_order_id}
                </Typography>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Button
                variant="contained"
                color="primary"
                fullWidth
                startIcon={invoiceLoading ? <CircularProgress size={20} /> : <ReceiptLong />}
                onClick={() => handleDownloadInvoice(selectedItem.id)}
                disabled={invoiceLoading}
              >
                {invoiceLoading ? 'İndiriliyor...' : '📄 Faturayı İndir (PDF)'}
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>

      {/* ✅ Destek Talebi Dialog */}
      <Dialog open={ticketDialogOpen} onClose={() => setTicketDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📩 Destek Talebi Oluştur</Typography>
            <IconButton onClick={() => setTicketDialogOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Konu"
            value={ticketSubject}
            onChange={(e) => setTicketSubject(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
            placeholder="Örn: Kredi iadesi talebi"
          />
          <TextField
            fullWidth
            label="Mesaj"
            multiline
            rows={4}
            value={ticketMessage}
            onChange={(e) => setTicketMessage(e.target.value)}
            sx={{ mb: 2 }}
            placeholder="Lütfen talebinizi detaylı olarak açıklayın..."
          />
          <TextField
            fullWidth
            select
            label="Öncelik"
            value={ticketPriority}
            onChange={(e) => setTicketPriority(e.target.value)}
            slotProps={{
              select: {
                native: true,
              },
            }}
          >
            <option value="low">Düşük</option>
            <option value="medium">Orta</option>
            <option value="high">Yüksek</option>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTicketDialogOpen(false)}>İptal</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleCreateTicket}
            disabled={ticketLoading || !ticketSubject || !ticketMessage}
            startIcon={ticketLoading ? <CircularProgress size={20} /> : <Send />}
          >
            {ticketLoading ? 'Gönderiliyor...' : 'Gönder'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}