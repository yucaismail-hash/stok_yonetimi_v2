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
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
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
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const steps = ['Hesap Bilgileri', 'Profil Bilgileri', 'Tamamlandı'];

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
    if (!formData.sectorId) {
      setError('Lütfen sektörünüzü seçin');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (activeStep === 0 && validateStep1()) {
      setActiveStep(1);
    } else if (activeStep === 1 && validateStep2()) {
      handleSubmit();
    }
  };

  const handleBack = () => {
    setActiveStep(activeStep - 1);
    setError(null);
  };

  const handleSubmit = async () => {
    setError(null);

      // ============ DEBUG ALERT ============
    alert(`📝 Kayıt Verileri:
    Email: ${formData.email}
    Full Name: ${formData.fullName}
    Company: ${formData.companyName}
    Sector ID: ${formData.sectorId}
    Sector ID Type: ${typeof formData.sectorId}
    `);
  
    try {
      const registerData = {
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName,
        company_name: formData.companyName,
        sector_id: formData.sectorId ? parseInt(formData.sectorId) : null,
      };

      alert(`📤 Backend'e Gönderilen Veri:
      ${JSON.stringify(registerData, null, 2)}`);

      console.log('Kayıt verisi:', registerData);

      const success = await register(
        registerData.email,
        registerData.password,
        registerData.full_name,
        registerData.company_name,
        registerData.sector_id
      );

      if (success) {
        setSuccess(true);
        setActiveStep(2);
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
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Sektörünüz</InputLabel>
              <Select
                value={formData.sectorId}
                label="Sektörünüz"
                onChange={handleSelectChange}
                disabled={isLoading || loadingSectors}
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
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
              Kayıt Tamamlandı! 🎉
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Hesabınız başarıyla oluşturuldu.
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
      <Container maxWidth="sm">
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

            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
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
                    {isLoading ? 'Kaydediliyor...' : activeStep === 1 ? 'Kaydol' : 'Devam'}
                  </Button>
                </Box>
              </>
            ) : (
              getStepContent(2)
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