import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  IconButton,
  InputAdornment,
  Link,
  TextField,
  Typography,
} from '@mui/material';
import { AppRegistration, Business, Email, Lock, Person, Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';


export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '', password: '', confirmPassword: '', fullName: '', companyName: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
    setError(null);
  };

  const submit = async () => {
    if (!formData.email || !formData.password || !formData.fullName || !formData.companyName) {
      setError('E-posta, şifre, ad soyad ve şirket adı gerekli.');
      return;
    }
    if (formData.password.length < 6) {
      setError('Şifre en az 6 karakter olmalı.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Şifreler eşleşmiyor.');
      return;
    }
    const created = await register({
      email: formData.email,
      password: formData.password,
      full_name: formData.fullName,
      company_name: formData.companyName,
    });
    if (created) navigate('/dashboard');
    else setError(useAuth.getState().error || 'Kayıt başarısız. Lütfen tekrar deneyin.');
  };

  const passwordAdornment = (visible: boolean, toggle: () => void) => ({
    input: {
      startAdornment: <InputAdornment position="start"><Lock color="action" /></InputAdornment>,
      endAdornment: <InputAdornment position="end"><IconButton onClick={toggle} edge="end">{visible ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment>,
    },
  });

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #1f4e79 0%, #2b6a9e 100%)', p: 2 }}>
      <Container maxWidth="sm">
        <Card sx={{ borderRadius: 4, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box sx={{ width: 64, height: 64, borderRadius: '50%', bgcolor: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center', mx: 'auto', mb: 2 }}>
                <AppRegistration sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Stokonomi'ye Katıl</Typography>
              <Typography variant="body2" color="text.secondary">Şirketinizi ve sahip hesabınızı oluşturun</Typography>
            </Box>
            {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
            <TextField fullWidth required label="E-posta Adresi" name="email" type="email" value={formData.email} onChange={update} disabled={isLoading} sx={{ mb: 2 }} slotProps={{ input: { startAdornment: <InputAdornment position="start"><Email color="action" /></InputAdornment> } }} />
            <TextField fullWidth required label="Şifre" name="password" type={showPassword ? 'text' : 'password'} value={formData.password} onChange={update} disabled={isLoading} helperText="En az 6 karakter" sx={{ mb: 2 }} slotProps={passwordAdornment(showPassword, () => setShowPassword(!showPassword))} />
            <TextField fullWidth required label="Şifre Tekrar" name="confirmPassword" type={showConfirmPassword ? 'text' : 'password'} value={formData.confirmPassword} onChange={update} disabled={isLoading} sx={{ mb: 2 }} slotProps={passwordAdornment(showConfirmPassword, () => setShowConfirmPassword(!showConfirmPassword))} />
            <TextField fullWidth required label="Ad ve Soyad" name="fullName" value={formData.fullName} onChange={update} disabled={isLoading} sx={{ mb: 2 }} slotProps={{ input: { startAdornment: <InputAdornment position="start"><Person color="action" /></InputAdornment> } }} />
            <TextField fullWidth required label="Şirket Adı" name="companyName" value={formData.companyName} onChange={update} disabled={isLoading} sx={{ mb: 3 }} slotProps={{ input: { startAdornment: <InputAdornment position="start"><Business color="action" /></InputAdornment> } }} />
            <Button fullWidth variant="contained" onClick={submit} disabled={isLoading} startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <AppRegistration />}>
              {isLoading ? 'Kaydediliyor...' : 'Şirket ve Hesap Oluştur'}
            </Button>
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" color="text.secondary">Zaten hesabınız var mı? <Link href="/login" sx={{ fontWeight: 'bold' }}>Giriş Yap</Link></Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
