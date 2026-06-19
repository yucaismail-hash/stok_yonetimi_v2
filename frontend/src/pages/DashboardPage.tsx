import { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Divider,
  Chip,
  useTheme,
  Box,
  Alert,
} from '@mui/material';
import {
  People,
  Inventory,
  Analytics,
  AttachMoney,
  UploadFile,
  Warning,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import FileUploader from '../components/Upload/FileUploader';
import StatsCard from '../components/Dashboard/StatsCard';
import RecentActivity from '../components/Dashboard/RecentActivity';
import QuickStartGuide from '../components/Dashboard/QuickStartGuide';
import { useAuth } from '../hooks/useAuth';

export default function DashboardPage() {
  const theme = useTheme();
  const { user } = useAuth();
  const [isUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        // Admin değilse /admin/users çağrısı yapma
        let totalUsers = 0;
        if (user?.email === 'admin@stok.com') {
          try {
            const usersRes = await api.get('/admin/users');
            totalUsers = usersRes.data?.length || 0;
          } catch {
            totalUsers = 0;
          }
        }
        
        return {
          totalUsers: totalUsers,
          totalMaterials: 145,
          avgServiceLevel: 0.94,
          totalTokens: user?.token_balance || 100,
          riskLevel: 'Düşük',
        };
      } catch (err) {
        console.error('Dashboard verisi alınamadı:', err);
        return {
          totalUsers: 0,
          totalMaterials: 145,
          avgServiceLevel: 0.94,
          totalTokens: user?.token_balance || 100,
          riskLevel: 'Düşük',
        };
      }
    },
    initialData: {
      totalUsers: 0,
      totalMaterials: 0,
      avgServiceLevel: 0,
      totalTokens: 0,
      riskLevel: '—',
    },
  });

  const handleFileUpload = (data: any[], columns: string[]) => {
    console.log('Yüklenen veri:', data, columns);
    // Burada dosya yükleme işlemini gerçekleştireceğiz
  };

  const statCards = [
    {
      title: 'Toplam Kullanıcı',
      value: stats.totalUsers,
      icon: <People sx={{ fontSize: 40, color: theme.palette.primary.main }} />,
      color: theme.palette.primary.main,
    },
    {
      title: 'Toplam Malzeme',
      value: stats.totalMaterials,
      icon: <Inventory sx={{ fontSize: 40, color: theme.palette.success.main }} />,
      color: theme.palette.success.main,
    },
    {
      title: 'Ortalama Servis Seviyesi',
      value: `${(stats.avgServiceLevel * 100).toFixed(1)}%`,
      icon: <Analytics sx={{ fontSize: 40, color: theme.palette.warning.main }} />,
      color: theme.palette.warning.main,
    },
    {
      title: 'Toplam Token',
      value: stats.totalTokens,
      icon: <AttachMoney sx={{ fontSize: 40, color: theme.palette.info.main }} />,
      color: theme.palette.info.main,
    },
  ];

  // Eğer yükleniyorsa
  if (isLoading) {
    return (
      <Box sx={{ p: 4 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Dashboard yükleniyor...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Başlık */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
            Hoş Geldiniz {user?.email?.split('@')[0] || 'Misafir'} 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI Destekli Stok Yönetim Sistemi ile stoklarınızı optimize edin.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<UploadFile />} sx={{ mt: { xs: 2, sm: 0 } }}>
          Veri Yükle
        </Button>
      </Box>

      {/* Hata varsa göster */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Bazı veriler yüklenemedi: {error.message}
        </Alert>
      )}

      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={index}>
            <StatsCard
              title={card.title}
              value={card.value}
              icon={card.icon}
              color={card.color}
            />
          </Grid>
        ))}
      </Grid>

      {/* Ana İçerik */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                📁 Veri Yükle
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Excel veya CSV dosyası yükleyerek analiz yapın.
              </Typography>
              <FileUploader onDataExtracted={handleFileUpload} />
              {isUploading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary">
                    Dosya işleniyor...
                  </Typography>
                </Box>
              )}
              {uploadError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {uploadError}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sağ Taraf: Recent Activity + Quick Start Guide */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12 }}>
              <RecentActivity />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <QuickStartGuide />
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Sistem Durumu */}
      <Paper sx={{ mt: 4, p: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Warning color="warning" />
            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
              Sistem Durumu: {stats.riskLevel} Risk
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Son Güncelleme: {new Date().toLocaleDateString('tr-TR')}
            </Typography>
            <Divider orientation="vertical" flexItem />
            <Chip label="Canlı" size="small" sx={{ backgroundColor: '#4caf50', color: 'white' }} />
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}