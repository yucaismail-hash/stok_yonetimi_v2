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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  People,
  Inventory,
  Analytics,
  AttachMoney,
  UploadFile,
  Warning,
  ExpandMore,
  Download,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import FileUploader from '../components/Upload/FileUploader';
import StatsCard from '../components/Dashboard/StatsCard';
import RecentActivity from '../components/Dashboard/RecentActivity';
import QuickStartGuide from '../components/Dashboard/QuickStartGuide';
import { useAuth } from '../hooks/useAuth';

interface UploadResult {
  material_code: string;
  pattern: string;
  safety_stock_methods: any;
  optimized_params: any;
  group: string;
}

export default function DashboardPage() {
  const theme = useTheme();
  const { user } = useAuth();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [resultDialogOpen, setResultDialogOpen] = useState(false);
  const [selectedMode, setSelectedMode] = useState<'quick' | 'detailed'>('quick');

  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
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

  // ✅ Dosya yükleme işlemi
  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadResults([]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('📤 Dosya yükleniyor:', file.name);
      
      const response = await api.post(`/api/upload?mode=${selectedMode}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('📥 Yükleme cevabı:', response.data);

      if (response.data.success) {
        setUploadSuccess(response.data.message || 'Dosya başarıyla yüklendi!');
        if (response.data.results) {
          setUploadResults(response.data.results);
          setResultDialogOpen(true);
        }
        // Dashboard istatistiklerini yenile
        refetch();
      } else {
        setUploadError(response.data.error || 'Yükleme başarısız oldu.');
      }
    } catch (err: any) {
      console.error('❌ Yükleme hatası:', err);
      setUploadError(err.response?.data?.detail || err.response?.data?.error || 'Dosya yüklenirken bir hata oluştu.');
    } finally {
      setIsUploading(false);
    }
  };

  // ✅ Rapor indir
  const handleDownloadReport = async () => {
    try {
      const response = await api.get('/api/upload/export-report', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `stok_raporu_${new Date().toISOString().slice(0,10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Rapor indirme hatası:', err);
      setUploadError('Rapor indirilemedi.');
    }
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
            Hoş Geldiniz {user?.full_name || user?.email?.split('@')[0] || 'Misafir'} 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI Destekli Stok Yönetim Sistemi ile stoklarınızı optimize edin.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, mt: { xs: 2, sm: 0 } }}>
          <Button
            variant={selectedMode === 'quick' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setSelectedMode('quick')}
          >
            Hızlı
          </Button>
          <Button
            variant={selectedMode === 'detailed' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setSelectedMode('detailed')}
          >
            Detaylı
          </Button>
        </Box>
      </Box>

      {/* Hata/başarı mesajları */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Bazı veriler yüklenemedi: {error.message}
        </Alert>
      )}
      {uploadError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setUploadError(null)}>
          {uploadError}
        </Alert>
      )}
      {uploadSuccess && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setUploadSuccess(null)}>
          {uploadSuccess}
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
              <FileUploader onDataExtracted={handleFileUpload} accept=".xlsx,.xls,.csv" />
              {isUploading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary">
                    Dosya işleniyor... Bu işlem birkaç dakika sürebilir.
                  </Typography>
                </Box>
              )}
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {selectedMode === 'quick' ? '⚡ Hızlı Mod: 100 simülasyon, 13 hafta' : '🔬 Detaylı Mod: 500 simülasyon, 26 hafta'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Sağ Taraf */}
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

      {/* ✅ Sonuç Dialog */}
      <Dialog open={resultDialogOpen} onClose={() => setResultDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📊 Analiz Sonuçları</Typography>
            <Box>
              <Button startIcon={<Download />} onClick={handleDownloadReport} size="small">
                Rapor İndir
              </Button>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Toplam {uploadResults.length} malzeme analiz edildi.
          </Typography>
          
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'primary.main' }}>
                  <TableCell sx={{ color: 'white' }}>Malzeme Kodu</TableCell>
                  <TableCell sx={{ color: 'white' }}>Grup</TableCell>
                  <TableCell sx={{ color: 'white' }}>Pattern</TableCell>
                  <TableCell sx={{ color: 'white' }} align="right">SS (Hybrid)</TableCell>
                  <TableCell sx={{ color: 'white' }} align="right">ROP</TableCell>
                  <TableCell sx={{ color: 'white' }} align="center">Risk</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {uploadResults.slice(0, 20).map((result, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{result.material_code}</TableCell>
                    <TableCell>{result.group}</TableCell>
                    <TableCell>
                      <Chip 
                        label={result.pattern} 
                        size="small" 
                        color={result.pattern.includes('SIFIR') ? 'default' : 'primary'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {result.safety_stock_methods?.hybrid_ss?.toFixed(0) || '-'}
                    </TableCell>
                    <TableCell align="right">
                      {result.optimized_params?.optimal_rop?.toFixed(0) || '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={result.optimized_params?.risk_level || '?'}
                        size="small"
                        color={
                          result.optimized_params?.risk_level === 'DÜŞÜK' ? 'success' :
                          result.optimized_params?.risk_level === 'ORTA' ? 'warning' : 'error'
                        }
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {uploadResults.length > 20 && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              ... ve {uploadResults.length - 20} malzeme daha
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}