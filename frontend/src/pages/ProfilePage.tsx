import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Grid,
  Avatar,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Lock,
  Save,
  Logout,
  Close,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useQuery } from '@tanstack/react-query';
import Swal from 'sweetalert2';

interface TokenHistoryItem {
  id: number;
  date: string;
  endpoint: string;
  cost: number;
  balance_after: number;
}

interface TokenPurchaseItem {
  id: number;
  date: string;
  amount: number;
  price: number;
  currency: string;
  status: string;
}

export default function ProfilePage() {
  const { user, logout, token, updateUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);
  const [sectors, setSectors] = useState<any[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [fetching, setFetching] = useState(true);
  
  const [formData, setFormData] = useState({
    fullName: '',
    companyName: '',
    sectorId: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // ✅ Kullanıcı bilgilerini çek
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        console.warn('⚠️ Token yok, kullanıcı bilgileri çekilemedi');
        setFetching(false);
        return;
      }
      try {
        console.log('🔄 Kullanıcı bilgileri çekiliyor...');
        const res = await api.get('/auth/me');
        console.log('✅ /auth/me cevabı:', res.data);
        
        setCurrentUser(res.data);
        setFormData(prev => ({
          ...prev,
          fullName: res.data.full_name || '',
          companyName: res.data.company_name || '',
          sectorId: res.data.sector_id?.toString() || '',
        }));
      } catch (error: any) {
        console.error('❌ Kullanıcı bilgileri alınamadı:', error);
        if (error.response?.status === 401) {
          console.error('🔴 Token geçersiz, çıkış yapılıyor...');
          logout();
          navigate('/login');
        }
      } finally {
        setFetching(false);
      }
    };
    fetchUser();
  }, [token, logout, navigate]);

  // ✅ Sektör listesini al (/api/sectors)
  useEffect(() => {
    const fetchSectors = async () => {
      try {
        const res = await api.get('/api/sectors');
        setSectors(res.data);
      } catch (error) {
        console.error('Sektörler yüklenemedi:', error);
      }
    };
    fetchSectors();
  }, []);

  // ✅ Token geçmişini getir (/api/profile/token-history)
  const { data: tokenHistory, isLoading: historyLoading } = useQuery({
    queryKey: ['token-history'],
    queryFn: async (): Promise<TokenHistoryItem[]> => {
      try {
        const res = await api.get('/api/profile/token-history');
        return res.data;
      } catch {
        return [];
      }
    },
    enabled: !!token,
  });

  // ✅ Token satın alma geçmişi (/api/profile/purchase-history)
  const { data: purchaseHistory, isLoading: purchaseLoading } = useQuery({
    queryKey: ['purchase-history'],
    queryFn: async (): Promise<TokenPurchaseItem[]> => {
      try {
        const res = await api.get('/api/profile/purchase-history');
        return res.data;
      } catch {
        return [];
      }
    },
    enabled: !!token,
  });

  // ✅ Form alanları değişiklikleri
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(null);
    setSuccess(false);
  };

  const handleSelectChange = (e: any) => {
    setFormData({ ...formData, sectorId: e.target.value });
    setError(null);
    setSuccess(false);
  };

  // ✅ PROFİLİ GÜNCELLE (/api/profile) + SweetAlert2 Onay
  const handleUpdateProfile = async () => {
    // 📌 SweetAlert2 onay penceresi
    const result = await Swal.fire({
      title: '⚠️ Uyarı!',
      text: 'Profil bilgilerinizi güncellemek istediğinize emin misiniz?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Evet, Güncelle!',
      cancelButtonText: 'Vazgeç'
    });

    if (!result.isConfirmed) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const res = await api.put('/api/profile', {
        full_name: formData.fullName,
        company_name: formData.companyName,
        sector_id: formData.sectorId ? parseInt(formData.sectorId) : null,
      });
      
      console.log('📦 Profil güncelleme cevabı:', res.data);
      
      // ✅ Başarılı
      if (res.status >= 200 && res.status < 300) {
        setSuccess(true);
        
        if (res.data) {
          setCurrentUser(res.data);
          updateUser(res.data);
          setFormData(prev => ({
            ...prev,
            sectorId: res.data.sector_id?.toString() || '',
          }));
        }
        
        // SweetAlert2 başarılı mesajı
        await Swal.fire({
          title: '✅ Başarılı!',
          text: 'Profil bilgileriniz başarıyla güncellendi.',
          icon: 'success',
          confirmButtonText: 'Tamam'
        });
      }
      
    } catch (err: any) {
      console.error('❌ Profil güncelleme hatası:', err);
      setError(err.response?.data?.detail || 'Güncelleme başarısız');
    } finally {
      setLoading(false);
    }
  };

  // ✅ ŞİFRE DEĞİŞTİR (/api/profile/password)
  const handleChangePassword = async () => {
    if (formData.newPassword !== formData.confirmPassword) {
      setError('Şifreler eşleşmiyor');
      return;
    }
    if (formData.newPassword.length < 6) {
      setError('Yeni şifre en az 6 karakter olmalı');
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await api.put('/api/profile/password', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword,
      });
      setSuccess(true);
      setFormData({ ...formData, currentPassword: '', newPassword: '', confirmPassword: '' });
      setOpenPasswordDialog(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Şifre değiştirme başarısız');
    } finally {
      setLoading(false);
    }
  };

  // ✅ ÇIKIŞ YAP
  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // ✅ displayUser: önce currentUser, yoksa user
  const displayUser = currentUser || user;

  // ✅ Sektör adını ayrıca al
  const sectorName = currentUser?.sector_name || user?.sector_name || null;

  // Yükleniyor durumu
  if (fetching) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Kullanıcı yoksa
  if (!displayUser) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh', flexDirection: 'column', gap: 2 }}>
        <Typography color="error">Kullanıcı bilgileri yüklenemedi.</Typography>
        <Button variant="contained" onClick={() => navigate('/login')}>
          Tekrar Giriş Yap
        </Button>
      </Box>
    );
  }

  // Toplam harcama hesapla
  const totalSpent = tokenHistory?.reduce((sum: number, item: TokenHistoryItem) => sum + item.cost, 0) || 0;
  const totalPurchased = purchaseHistory?.reduce((sum: number, item: TokenPurchaseItem) => sum + item.amount, 0) || 0;

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        👤 Profil
      </Typography>

      <Grid container spacing={3}>
        {/* Sol: Profil Bilgileri */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main' }}>
                  {displayUser?.email?.charAt(0).toUpperCase()}
                </Avatar>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {displayUser?.full_name || displayUser?.email}
                  </Typography>
                  <Chip
                    label={displayUser?.role === 'admin' ? 'Admin' : 'Kullanıcı'}
                    color={displayUser?.role === 'admin' ? 'primary' : 'default'}
                    size="small"
                  />
                  {sectorName && (
                    <Chip
                      label={sectorName}
                      color="info"
                      variant="outlined"
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Typography variant="subtitle2" gutterBottom>
                💰 Token Bakiyesi
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 3 }}>
                {displayUser?.token_balance || 0} 🪙
              </Typography>

              {/* 📝 Profil Güncelleme Formu */}
              <TextField
                fullWidth
                label="Ad Soyad"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Firma Adı"
                name="companyName"
                value={formData.companyName}
                onChange={handleChange}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Sektör</InputLabel>
                <Select
                  value={formData.sectorId}
                  label="Sektör"
                  onChange={handleSelectChange}
                >
                  <MenuItem value="">Seçiniz</MenuItem>
                  {sectors.map((s: any) => (
                    <MenuItem key={s.id} value={s.id}>
                      {s.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <Save />}
                  onClick={handleUpdateProfile}
                  disabled={loading}
                >
                  Profili Güncelle
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Lock />}
                  onClick={() => setOpenPasswordDialog(true)}
                >
                  Şifre Değiştir
                </Button>
                <Button
                  variant="text"
                  startIcon={<Logout />}
                  color="error"
                  onClick={handleLogout}
                >
                  Çıkış Yap
                </Button>
              </Box>

              {success && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Profil başarıyla güncellendi.
                </Alert>
              )}
              {error && (
                <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sağ: Token Geçmişi */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                📊 Token Harcama Geçmişi
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Son 50 işlem
              </Typography>

              {historyLoading ? (
                <CircularProgress size={24} />
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'primary.main' }}>
                        <TableCell sx={{ color: 'white' }}>Tarih</TableCell>
                        <TableCell sx={{ color: 'white' }}>Endpoint</TableCell>
                        <TableCell sx={{ color: 'white' }} align="right">Harcama</TableCell>
                        <TableCell sx={{ color: 'white' }} align="right">Kalan</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {tokenHistory && tokenHistory.length > 0 ? (
                        tokenHistory.map((item: TokenHistoryItem) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.date}</TableCell>
                            <TableCell>{item.endpoint}</TableCell>
                            <TableCell align="right">
                              <Chip label={`-${item.cost}`} size="small" color="error" />
                            </TableCell>
                            <TableCell align="right">{item.balance_after}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                              Henüz token harcaması yapılmamış.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Toplam Harcama: {totalSpent} 🪙
                </Typography>
                <Chip
                  label={`Kalan: ${displayUser?.token_balance || 0} 🪙`}
                  color="primary"
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>

          {/* Satın Alma Geçmişi */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                💳 Token Satın Alma Geçmişi
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Satın aldığınız token paketleri
              </Typography>

              {purchaseLoading ? (
                <CircularProgress size={24} />
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'success.main' }}>
                        <TableCell sx={{ color: 'white' }}>Tarih</TableCell>
                        <TableCell sx={{ color: 'white' }} align="right">Miktar</TableCell>
                        <TableCell sx={{ color: 'white' }} align="right">Fiyat</TableCell>
                        <TableCell sx={{ color: 'white' }} align="center">Durum</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {purchaseHistory && purchaseHistory.length > 0 ? (
                        purchaseHistory.map((item: TokenPurchaseItem) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.date}</TableCell>
                            <TableCell align="right">
                              <Chip label={`+${item.amount} 🪙`} size="small" color="success" />
                            </TableCell>
                            <TableCell align="right">{item.price} {item.currency}</TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={item.status === 'completed' ? '✅ Tamamlandı' : '⏳ Bekliyor'} 
                                size="small" 
                                color={item.status === 'completed' ? 'success' : 'warning'} 
                              />
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                              Henüz token satın alımı yapılmamış.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Toplam Satın Alım: {totalPurchased} 🪙
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 🔐 Şifre Değiştirme Dialog */}
      <Dialog open={openPasswordDialog} onClose={() => setOpenPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">🔐 Şifre Değiştir</Typography>
            <IconButton onClick={() => setOpenPasswordDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            type="password"
            label="Mevcut Şifre"
            name="currentPassword"
            value={formData.currentPassword}
            onChange={handleChange}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            type="password"
            label="Yeni Şifre"
            name="newPassword"
            value={formData.newPassword}
            onChange={handleChange}
            sx={{ mb: 2 }}
            helperText="En az 6 karakter"
          />
          <TextField
            fullWidth
            type="password"
            label="Yeni Şifre Tekrar"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPasswordDialog(false)}>İptal</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}