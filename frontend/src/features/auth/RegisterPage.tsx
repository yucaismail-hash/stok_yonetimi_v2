// frontend/src/pages/RegisterPage.tsx

import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  InputAdornment,
  IconButton,
  Alert,
  CircularProgress,
  Container,
  Divider,
  Link,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
} from '@mui/material';
import {
  Email,
  Lock,
  Person,
  Business,
  Visibility,
  VisibilityOff,
  AppRegistration,
  CheckCircle,
  LocationOn,
  Receipt,
  AccountBalance,
  CreditCard,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [sectors, setSectors] = useState<any[]>([]);
  const [loadingSectors, setLoadingSectors] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    companyName: '',
    sectorId: '',
    billingAddress: '',
    billingCity: '',
    billingState: '',
    billingCountry: 'TR',
    billingPostalCode: '',
    taxId: '',
    taxOffice: '',
    identityNumber: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const steps = ['Hesap Bilgileri', 'Profil Bilgileri', 'Fatura Bilgileri', 'Tamamlandı'];

  // Sektör listesini al
  useEffect(() => {
    const fetchSectors = async () => {
      try {
        setLoadingSectors(true);
        const res = await axios.get(`${API_BASE}/api/sectors`);
        console.log('Sektörler yüklendi:', res.data);
        setSectors(res.data);
      } catch (error) {
        console.error('Sektörler yüklenemedi:', error);
      } finally {
        setLoadingSectors(false);
      }
    };
    fetchSectors();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(null);
  };

  const handleSelectChange = (e: any) => {
    setFormData({ ...formData, sectorId: e.target.value });
    setError(null);
  };

  const validateStep1 = () => {
    if (!formData.email) {
      setError('E-posta adresi gerekli');
      return false;
    }
    if (!formData.password) {
      setError('Şifre gerekli');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Şifre en az 6 karakter olmalı');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Şifreler eşleşmiyor');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.fullName) {
      setError('Ad ve soyad gerekli');
      return false;
    }
    if (!formData.companyName) {
      setError('Şirket adı gerekli');
      return false;
    }
    if (!formData.sectorId) {
      setError('Lütfen sektörünüzü seçin');
      return false;
    }
    return true;
  };

  const validateStep3 = () => {
    if (!formData.billingAddress) {
      setError('Fatura adresi gerekli');
      return false;
    }
    if (!formData.billingCity) {
      setError('Şehir gerekli');
      return false;
    }
    if (!formData.taxId) {
      setError('Vergi numarası gerekli');
      return false;
    }
    if (!formData.taxOffice) {
      setError('Vergi dairesi gerekli');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (activeStep === 0 && validateStep1()) {
      setActiveStep(1);
    } else if (activeStep === 1 && validateStep2()) {
      setActiveStep(2);
    } else if (activeStep === 2 && validateStep3()) {
      handleSubmit();
    }
  };

  const handleBack = () => {
    setActiveStep(activeStep - 1);
    setError(null);
  };

  // ✅ DÜZELTİLMİŞ handleSubmit - register'a TEK OBJE gönder
  const handleSubmit = async () => {
    setError(null);

    try {
      const success = await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName,
        company_name: formData.companyName,
        sector_id: formData.sectorId ? parseInt(formData.sectorId) : null,
        billing_address: formData.billingAddress,
        billing_city: formData.billingCity,
        billing_state: formData.billingState,
        billing_country: formData.billingCountry || 'TR',
        billing_postal_code: formData.billingPostalCode,
        tax_id: formData.taxId,
        tax_office: formData.taxOffice,
        identity_number: formData.identityNumber,
      });

      if (success) {
        setSuccess(true);
        setActiveStep(3);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    } catch (err: any) {
      console.error('Kayıt hatası:', err);
      setError(err.response?.data?.detail || 'Kayıt başarısız. Lütfen tekrar deneyin.');
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Hesap bilgilerinizi oluşturun
            </Typography>
            <TextField
              fullWidth
              label="E-posta Adresi"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ mb: 3 }}
              placeholder="ornek@firma.com"
            />
            <TextField
              fullWidth
              label="Şifre"
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              helperText="En az 6 karakter"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ mb: 3 }}
            />
            <TextField
              fullWidth
              label="Şifre Tekrar"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end">
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Profil bilgilerinizi tamamlayın
            </Typography>
            <TextField
              fullWidth
              label="Ad ve Soyad"
              name="fullName"
              value={formData.fullName}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ mb: 3 }}
              placeholder="Ahmet Yılmaz"
            />
            <TextField
              fullWidth
              label="Firma Adı"
              name="companyName"
              value={formData.companyName}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Business color="action" />
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ mb: 3 }}
              placeholder="ABC Teknoloji A.Ş."
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Sektörünüz</InputLabel>
              <Select
                value={formData.sectorId}
                label="Sektörünüz"
                onChange={handleSelectChange}
                disabled={isLoading || loadingSectors}
                required
              >
                <MenuItem value="">Seçiniz</MenuItem>
                {sectors.map((s: any) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.name}
                  </MenuItem>
                ))}
              </Select>
              {loadingSectors && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Sektörler yükleniyor...
                </Typography>
              )}
            </FormControl>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                mb: 3,
                bgcolor: 'info.light',
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Receipt color="info" />
              <Typography variant="body2" color="info.dark">
                <strong>📋 Fatura Bilgileri</strong> — Ödemeleriniz sonrası faturanız bu adrese kesilecektir.
              </Typography>
            </Paper>

            {/* ✅ Grid kullanımı - item prop'u yok, Grid container içinde doğrudan Grid */}
            <Grid container spacing={2}>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Fatura Adresi"
                  name="billingAddress"
                  value={formData.billingAddress}
                  onChange={handleInputChange}
                  required
                  disabled={isLoading}
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <LocationOn color="action" />
                        </InputAdornment>
                      ),
                    },
                  }}
                  placeholder="Örnek: İstanbul, Kadıköy, Moda Cad. No:123"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Şehir"
                  name="billingCity"
                  value={formData.billingCity}
                  onChange={handleInputChange}
                  required
                  disabled={isLoading}
                  placeholder="İstanbul"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="İlçe / Semt"
                  name="billingState"
                  value={formData.billingState}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  placeholder="Kadıköy"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Posta Kodu"
                  name="billingPostalCode"
                  value={formData.billingPostalCode}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  placeholder="34700"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Ülke</InputLabel>
                  <Select
                    value={formData.billingCountry}
                    label="Ülke"
                    onChange={(e) => setFormData({ ...formData, billingCountry: e.target.value })}
                    disabled={isLoading}
                  >
                    <MenuItem value="TR">Türkiye</MenuItem>
                    <MenuItem value="US">Amerika Birleşik Devletleri</MenuItem>
                    <MenuItem value="GB">İngiltere</MenuItem>
                    <MenuItem value="DE">Almanya</MenuItem>
                    <MenuItem value="FR">Fransa</MenuItem>
                    <MenuItem value="IT">İtalya</MenuItem>
                    <MenuItem value="ES">İspanya</MenuItem>
                    <MenuItem value="NL">Hollanda</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
              💳 Vergi Bilgileri
            </Typography>

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Vergi Numarası"
                  name="taxId"
                  value={formData.taxId}
                  onChange={handleInputChange}
                  required
                  disabled={isLoading}
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <CreditCard color="action" />
                        </InputAdornment>
                      ),
                    },
                  }}
                  placeholder="1234567890"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Vergi Dairesi"
                  name="taxOffice"
                  value={formData.taxOffice}
                  onChange={handleInputChange}
                  required
                  disabled={isLoading}
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <AccountBalance color="action" />
                        </InputAdornment>
                      ),
                    },
                  }}
                  placeholder="İstanbul Vergi Dairesi"
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3 }}>
              <TextField
                fullWidth
                label="TC Kimlik / Vergi Kimlik No"
                name="identityNumber"
                value={formData.identityNumber}
                onChange={handleInputChange}
                disabled={isLoading}
                helperText="Bireysel kullanıcılar için TC Kimlik No, kurumlar için vergi numarası"
                placeholder="12345678901"
              />
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
              Kayıt Tamamlandı! 🎉
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Hesabınız başarıyla oluşturuldu.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Fatura bilgileriniz kaydedildi.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Yönlendiriliyorsunuz...
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1f4e79 0%, #2b6a9e 100%)',
        p: 2,
      }}
    >
      <Container maxWidth="md">
        <Card sx={{ borderRadius: 4, boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <AppRegistration sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                Stokonomi'ye Katıl
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ücretsiz hesap oluşturun, hemen başlayın
              </Typography>
            </Box>

            <Stepper activeStep={activeStep} sx={{ mb: 4, overflow: 'auto' }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {!success ? (
              <>
                {getStepContent(activeStep)}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                  <Button
                    variant="outlined"
                    onClick={handleBack}
                    disabled={activeStep === 0 || isLoading}
                  >
                    Geri
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleNext}
                    disabled={isLoading}
                    startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
                  >
                    {isLoading
                      ? 'Kaydediliyor...'
                      : activeStep === 2
                      ? 'Kaydol'
                      : 'Devam'}
                  </Button>
                </Box>
              </>
            ) : (
              getStepContent(3)
            )}

            {activeStep < 2 && (
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Zaten hesabınız var mı?{' '}
                  <Link href="/login" sx={{ fontWeight: 'bold', cursor: 'pointer' }}>
                    Giriş Yap
                  </Link>
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="caption" color="rgba(255,255,255,0.7)">
            © {new Date().getFullYear()} Stokonomi - Tüm hakları saklıdır.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}