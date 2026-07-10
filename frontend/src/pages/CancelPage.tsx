import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Divider,
} from '@mui/material';
import { CancelOutlined, Home, Refresh, ArrowBack } from '@mui/icons-material';

export default function CancelPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const checkoutId = searchParams.get('checkout_id');

  const handleGoToDashboard = () => {
    navigate('/dashboard');
  };

  const handleGoToPricing = () => {
    navigate('/pricing');
  };

  const handleRetry = () => {
    navigate('/pricing');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)',
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
              bgcolor: 'warning.light',
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
              bgcolor: 'warning.light',
              opacity: 0.05,
            }}
          />

          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Box
              sx={{
                width: 100,
                height: 100,
                borderRadius: '50%',
                bgcolor: 'warning.light',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3,
              }}
            >
              <CancelOutlined sx={{ fontSize: 64, color: 'warning.main' }} />
            </Box>

            <Typography
              variant="h4"
              sx={{ fontWeight: 800, color: 'warning.main', mb: 1 }}
            >
              ⏹️ Ödeme İptal Edildi
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              Ödeme işleminiz iptal edildi.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Herhangi bir ücret alınmamıştır.
            </Typography>

            {checkoutId && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>
                İşlem No: #{checkoutId.slice(0, 8)}
              </Typography>
            )}

            <Divider sx={{ my: 3 }} />

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              💡 Ödeme işlemini tamamlamak isterseniz tekrar deneyebilirsiniz.
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                color="warning"
                onClick={handleRetry}
                startIcon={<Refresh />}
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 3,
                  textTransform: 'none',
                  fontWeight: 'bold',
                }}
              >
                Tekrar Dene
              </Button>
              <Button
                variant="outlined"
                onClick={handleGoToDashboard}
                startIcon={<Home />}
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 3,
                  textTransform: 'none',
                }}
              >
                Dashboard'a Dön
              </Button>
            </Box>

            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                🔒 Ödeme işleminiz güvenli ödeme platformu Polar üzerinden gerçekleştirilmiştir.
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}