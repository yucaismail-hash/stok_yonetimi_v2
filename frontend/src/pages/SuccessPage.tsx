import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Chip,
} from '@mui/material';
import { 
  CheckCircle, 
  ShoppingCart, 
  Home, 
  ArrowForward,
  Error as ErrorIcon  // ✅ "Error" yerine "ErrorIcon" olarak import et
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

export default function SuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, fetchUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transaction, setTransaction] = useState<any>(null);

  const checkoutId = searchParams.get('checkout_id');

  useEffect(() => {
    const verifyPayment = async () => {
      try {
        setLoading(true);
        await fetchUser();
        
        if (checkoutId) {
          try {
            const res = await api.get(`/api/polar/transaction/${checkoutId}`);
            setTransaction(res.data);
          } catch (err) {
            console.log('⚠️ İşlem detayları alınamadı:', err);
          }
        }
        setLoading(false);
      } catch (err: any) {
        console.error('❌ Ödeme doğrulama hatası:', err);
        setError(err.response?.data?.detail || 'Ödeme doğrulanamadı.');
        setLoading(false);
      }
    };

    verifyPayment();
  }, [checkoutId]);

  const handleGoToDashboard = () => {
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, fontWeight: 'bold' }}>
            Ödemeniz Kontrol Ediliyor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Lütfen bekleyin...
          </Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ py: 8 }}>
          <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 4 }}>
            <Box sx={{ color: 'error.main' }}>
              <ErrorIcon sx={{ fontSize: 80 }} />  {/* ✅ ErrorIcon kullan */}
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mt: 2, color: 'error.main' }}>
              Ödeme Doğrulanamadı
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 3 }}>
              {error}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={handleGoToDashboard}
              startIcon={<Home />}
            >
              Dashboard'a Dön
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)',
        p: 2,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          sx={{
            p: 5,
            textAlign: 'center',
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              top: -60,
              right: -60,
              width: 200,
              height: 200,
              borderRadius: '50%',
              bgcolor: 'success.light',
              opacity: 0.1,
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              bottom: -80,
              left: -80,
              width: 250,
              height: 250,
              borderRadius: '50%',
              bgcolor: 'success.light',
              opacity: 0.05,
            }}
          />

          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Box
              sx={{
                width: 100,
                height: 100,
                borderRadius: '50%',
                bgcolor: 'success.light',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3,
              }}
            >
              <CheckCircle sx={{ fontSize: 64, color: 'success.main' }} />
            </Box>

            <Typography
              variant="h4"
              sx={{ fontWeight: 800, color: 'success.main', mb: 1 }}
            >
              🎉 Ödeme Başarılı!
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              Kredileriniz hesabınıza başarıyla eklendi.
            </Typography>

            {checkoutId && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>
                İşlem No: #{checkoutId.slice(0, 8)}
              </Typography>
            )}

            <Divider sx={{ my: 3 }} />

            <Card sx={{ bgcolor: 'success.light', borderRadius: 3, mb: 3 }}>
              <CardContent>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'success.dark' }}>
                  📊 İşlem Özeti
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                  <Typography variant="body2" color="text.secondary">Paket</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {transaction?.package_name || 'Starter'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Eklenen Kredi</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'success.dark' }}>
                    +{transaction?.credits || 100}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Yeni Bakiye</Typography>
                  <Chip
                    label={`${user?.token_balance || 0} Kredi`}
                    size="small"
                    color="success"
                    sx={{ fontWeight: 'bold' }}
                  />
                </Box>
              </CardContent>
            </Card>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                onClick={handleGoToDashboard}
                startIcon={<Home />}
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 3,
                  textTransform: 'none',
                  fontWeight: 'bold',
                }}
              >
                Dashboard'a Dön
              </Button>
              <Button
                variant="outlined"
                onClick={() => navigate('/pricing')}
                endIcon={<ArrowForward />}
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 3,
                  textTransform: 'none',
                }}
              >
                Paketleri İncele
              </Button>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}