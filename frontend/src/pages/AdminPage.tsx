import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  Avatar,
  AppBar,
  Toolbar,
  Chip,
} from '@mui/material';
import {
  Analytics,
  Security,
  ShowChart,
  Inventory,
  LocalShipping,
  Warning,
  Rocket,
  EmojiEvents,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';

const features = [
  {
    icon: <Analytics fontSize="large" />,
    title: 'Akıllı Pattern Analizi',
    desc: '7 farklı talep paterni ile verilerinizi anında analiz edin.',
    color: '#1f4e79',
  },
  {
    icon: <Security fontSize="large" />,
    title: '6 Farklı SS Metodu',
    desc: 'Classic, Croston, SB, Bootstrap, ML ve Hybrid ile optimum stoğu bulun.',
    color: '#2e7d32',
  },
  {
    icon: <ShowChart fontSize="large" />,
    title: '4 Model ile Tahmin',
    desc: 'Holt-Winters, ARIMA ve daha fazlası ile geleceği öngörün.',
    color: '#ed6c02',
  },
  {
    icon: <Inventory fontSize="large" />,
    title: 'Monte Carlo Simülasyonu',
    desc: 'Binlerce senaryo ile stok performansınızı test edin.',
    color: '#0288d1',
  },
  {
    icon: <LocalShipping fontSize="large" />,
    title: 'Tedarikçi Yönetimi',
    desc: 'Risk ve performans analizi ile tedarikçilerinizi optimize edin.',
    color: '#6a1b9a',
  },
  {
    icon: <Warning fontSize="large" />,
    title: 'Risk Metrikleri',
    desc: 'Tail Risk, CVaR95 ve Servis Seviyesi Gap ile riskleri yönetin.',
    color: '#d32f2f',
  },
];

const stats = [
  { number: '6', label: 'SS Metodu' },
  { number: '8', label: 'Backtest Stratejisi' },
  { number: '4', label: 'Forecast Modeli' },
  { number: '7', label: 'Talep Paterni' },
];

export default function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleGetStarted = () => {
    if (user) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <Box>
      {/* Top Navigation */}
      <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: '1px solid #e0e0e0' }}>
        <Container maxWidth="lg">
          <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 0 } }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              📊 Stokonomi
            </Typography>
            <Box>
              {user ? (
                <Button variant="contained" onClick={() => navigate('/dashboard')}>
                  Dashboard
                </Button>
              ) : (
                <>
                  <Button color="inherit" onClick={() => navigate('/login')}>
                    Giriş Yap
                  </Button>
                  <Button variant="contained" onClick={() => navigate('/register')} sx={{ ml: 1 }}>
                    Kayıt Ol
                  </Button>
                </>
              )}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Hero Bölümü - Stokonomi Hikayesi */}
      <Box
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          py: { xs: 6, md: 10 },
          px: 2,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Chip
            label="🚀 AI Destekli Stok Yönetimi"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', mb: 2 }}
          />
          <Typography
            variant="h1"
            component="h1"
            sx={{
              fontWeight: 800,
              fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4.5rem' },
              mb: 2,
            }}
          >
            Stokonomi
          </Typography>
          <Typography variant="h5" sx={{ mb: 3, opacity: 0.9 }}>
            Akıllı stok yönetimi, kesin kararlar, kurumsal başarı.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, opacity: 0.8, maxWidth: 600, mx: 'auto' }}>
            Stokonomi, yapay zeka destekli analizlerle stok optimizasyonunu
            herkes için erişilebilir kılıyor. 6 farklı SS metodu, 4 tahmin modeli
            ve 8 backtest stratejisi ile işletmenizi bir üst seviyeye taşıyın.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': { bgcolor: 'grey.100' },
              }}
              onClick={handleGetStarted}
            >
              {user ? 'Dashboard\'a Git' : 'Hemen Başla'}
            </Button>
            <Button
              variant="outlined"
              size="large"
              sx={{ borderColor: 'white', color: 'white', '&:hover': { borderColor: 'grey.300' } }}
              href="#features"
            >
              Keşfet
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Hikaye Bölümü */}
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center', mb: 2 }}>
          📖 Stokonomi Hikayesi
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
          Stokonomi, işletmelerin stok yönetiminde karşılaştığı zorlukları
          yapay zeka ile çözmek için doğdu. Karmaşık hesaplamaları basitleştirir,
          öngörülebilirliği artırır ve maliyetleri düşürür.
        </Typography>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Rocket color="primary" sx={{ fontSize: 40 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Vizyonumuz</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Stok yönetimini veri odaklı, şeffaf ve akıllı hale getirerek
                işletmelerin rekabet gücünü artırmak.
              </Typography>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <EmojiEvents color="warning" sx={{ fontSize: 40 }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Misyonumuz</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Her ölçekteki işletmeye, kurumsal düzeyde stok optimizasyonu
                sunarak israfı önlemek ve karlılığı artırmak.
              </Typography>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Özellikler Bölümü */}
      <Box sx={{ bgcolor: 'grey.50', py: 6 }} id="features">
        <Container maxWidth="lg">
          <Typography variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center', mb: 2 }}>
            🚀 Güçlü Özellikler
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', mb: 6 }}>
            Stok yönetimini bir üst seviyeye taşıyan tüm araçlar tek platformda.
          </Typography>

          <Grid container spacing={3}>
            {features.map((feature, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
                <Card sx={{ height: '100%', textAlign: 'center', p: 2 }}>
                  <Avatar
                    sx={{
                      bgcolor: `${feature.color}15`,
                      color: feature.color,
                      width: 56,
                      height: 56,
                      mx: 'auto',
                      mb: 2,
                    }}
                  >
                    {feature.icon}
                  </Avatar>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.desc}
                  </Typography>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* İstatistikler Bölümü */}
      <Box sx={{ py: 6 }}>
        <Container maxWidth="lg">
          <Grid container spacing={3} sx={{ textAlign: 'center' }}>
            {stats.map((stat, index) => (
              <Grid size={{ xs: 6, md: 3 }} key={index}>
                <Typography variant="h2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  {stat.number}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stat.label}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Bölümü */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', py: 6, textAlign: 'center' }}>
        <Container maxWidth="sm">
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
            Stoklarınızı Akıllıca Yönetin
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, opacity: 0.9 }}>
            Stokonomi ile stok optimizasyonu, talep tahmini ve risk analizini
            tek bir platformda deneyimleyin.
          </Typography>
          <Button
            variant="contained"
            size="large"
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              '&:hover': { bgcolor: 'grey.100' },
            }}
            onClick={handleGetStarted}
          >
            {user ? 'Dashboard\'a Git' : 'Ücretsiz Başla'}
          </Button>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: 'grey.900', color: 'white', py: 4, textAlign: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
          📊 Stokonomi
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.7 }}>
          © {new Date().getFullYear()} Stokonomi - Tüm hakları saklıdır.
        </Typography>
        <Typography variant="caption" sx={{ opacity: 0.5 }}>
          AI Destekli Stok Yönetim Sistemi
        </Typography>
      </Box>
    </Box>
  );
}