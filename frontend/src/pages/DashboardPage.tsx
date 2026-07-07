import { useState, useEffect, useRef } from 'react';
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
  LinearProgress,
  Avatar,
  AvatarGroup,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  ShowChart,
  Security,
  Timeline,
  Backpack,
  LocalShipping,
  Analytics,
  Download,
  Refresh,
  MoreVert,
  CheckCircle,
  Warning,
  Error,
  Info,
  Speed,
  Store,
  Inventory,
  AttachMoney,
  Visibility,
  CloudUpload,
  InsertDriveFile,
  Clear,
  Check,
  UploadFile,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { useQuery } from '@tanstack/react-query';
import { styled } from '@mui/material/styles';

// 📁 Styled Upload Area
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const UploadArea = styled(Paper)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.spacing(2),
  padding: theme.spacing(4),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s',
  backgroundColor: theme.palette.background.default,
  '&:hover': {
    backgroundColor: theme.palette.primary.light + '20',
    borderColor: theme.palette.primary.dark,
  },
  '&.dragging': {
    backgroundColor: theme.palette.primary.light + '30',
    borderColor: theme.palette.primary.dark,
    transform: 'scale(1.02)',
  },
}));

// 📊 İstatistik Kartı Bileşeni
interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  trend?: number;
  loading?: boolean;
}

const StatCard = ({ title, value, icon, color, subtitle, trend, loading }: StatCardProps) => {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              {title}
            </Typography>
            {loading ? (
              <CircularProgress size={24} sx={{ mt: 1 }} />
            ) : (
              <Typography variant="h4" sx={{ fontWeight: 'bold', mt: 0.5 }}>
                {value}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
            {trend !== undefined && (
              <Chip
                label={`${trend > 0 ? '+' : ''}${trend}%`}
                size="small"
                color={trend > 0 ? 'success' : 'error'}
                sx={{ mt: 1, height: 20, fontSize: '0.7rem' }}
              />
            )}
          </Box>
          <Avatar
            sx={{
              bgcolor: color,
              width: 48,
              height: 48,
              boxShadow: `0 4px 12px ${color}40`,
            }}
          >
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
};

// 📋 Analiz Kartı Bileşeni
interface AnalysisCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  path: string;
  tokenCost: number;
  isAsync?: boolean;
  onClick: () => void;
}

const AnalysisCard = ({ title, description, icon, color, path, tokenCost, isAsync, onClick }: AnalysisCardProps) => {
  return (
    <Card 
      sx={{ 
        height: '100%',
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
          <Avatar sx={{ bgcolor: color, width: 40, height: 40 }}>
            {icon}
          </Avatar>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              {title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
              <Chip 
                label={`${tokenCost} Token`} 
                size="small" 
                color="warning" 
                sx={{ height: 18, fontSize: '0.6rem' }} 
              />
              {isAsync && (
                <Chip 
                  label="ASYNC" 
                  size="small" 
                  color="secondary" 
                  sx={{ height: 18, fontSize: '0.6rem' }} 
                />
              )}
            </Box>
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {description}
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Chip label="Başlat" size="small" sx={{ bgcolor: color, color: 'white' }} />
        </Box>
      </CardContent>
    </Card>
  );
};

// 📈 Son Aktivite Bileşeni
interface Activity {
  id: number;
  type: string;
  message: string;
  time: string;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
}

const ActivityItem = ({ activity }: { activity: Activity }) => {
  const getIcon = (status: string) => {
    switch(status) {
      case 'success': return <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main', fontSize: 16 }} />;
      case 'error': return <Error sx={{ color: 'error.main', fontSize: 16 }} />;
      default: return <Info sx={{ color: 'info.main', fontSize: 16 }} />;
    }
  };

  return (
    <ListItem sx={{ px: 0 }}>
      <ListItemIcon sx={{ minWidth: 32 }}>
        {getIcon(activity.status)}
      </ListItemIcon>
      <ListItemText
        primary={activity.message}
        secondary={activity.time}
        slotProps={{
          primary: { variant: 'body2' },
          secondary: { variant: 'caption' },
        }}
      />
      {activity.details && (
        <Chip label={activity.details} size="small" variant="outlined" sx={{ ml: 1 }} />
      )}
    </ListItem>
  );
};

export default function DashboardPage() {
  const { user, fetchUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [stats, setStats] = useState({
    totalMaterials: 0,
    totalAnalyses: 0,
    avgServiceLevel: 0,
    tokenBalance: 0,
    activeSuppliers: 0,
    completedTasks: 0,
  });
  const [activities, setActivities] = useState<Activity[]>([]);
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [showAllActivities, setShowAllActivities] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  // ✅ Kullanıcı istatistiklerini getir
  const { data: userStats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        const balance = user?.token_balance || 0;
        const uploadRes = await api.get('/api/upload/status');
        const totalMaterials = uploadRes.data.materials_count || 0;
        const historyRes = await api.get('/api/upload/results', {
          params: { limit: 100 }
        });
        const totalAnalyses = historyRes.data.total || 0;
        const tasksRes = await api.get('/api/tasks/async');
        const tasks = tasksRes.data.tasks || [];
        const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;
        
        return {
          tokenBalance: balance,
          totalMaterials,
          totalAnalyses,
          completedTasks,
          avgServiceLevel: 0,
          activeSuppliers: 0,
        };
      } catch (error) {
        console.error('❌ Dashboard istatistik hatası:', error);
        return {
          tokenBalance: user?.token_balance || 0,
          totalMaterials: 0,
          totalAnalyses: 0,
          completedTasks: 0,
          avgServiceLevel: 0,
          activeSuppliers: 0,
        };
      }
    },
    enabled: !!user,
  });

  // ✅ Son aktiviteleri getir
  const fetchActivities = async () => {
    try {
      const res = await api.get('/api/upload/results', {
        params: { limit: 100 }
      });
      
      const results = res.data.results || [];
      const activityList: Activity[] = results.map((item: any, index: number) => ({
        id: index,
        type: 'analysis',
        message: `${item.material_code || 'Analiz'} tamamlandı`,
        time: new Date(item.created_at).toLocaleString('tr-TR'),
        status: 'success' as const,
        details: item.result_type || 'Analiz',
      }));
      
      setAllActivities(activityList);
      setActivities(activityList.slice(0, 5));
    } catch (error) {
      console.error('❌ Aktivite hatası:', error);
      setAllActivities([]);
      setActivities([]);
    }
  };

  // ✅ Dosya Seç
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(false);
    setUploadProgress(0);
  };

  // ✅ Dosya Yükleme
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Lütfen bir dosya seçin.');
      return;
    }

    setUploading(true);
    setUploadProgress(10);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadProgress(30);
      const response = await api.post('/api/upload?mode=quick', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(30 + percent * 0.6);
          }
        },
      });

      setUploadProgress(100);
      
      if (response.data.success) {
        setUploadSuccess(true);
        // ✅ İstatistikleri yenile
        refetchStats();
        // ✅ Kullanıcı bilgilerini yenile
        await fetchUser();
        // ✅ Aktivite listesini yenile
        fetchActivities();
        // ✅ 3 saniye sonra başarı mesajını kapat
        setTimeout(() => setUploadSuccess(false), 5000);
      } else {
        setUploadError(response.data.error || 'Dosya yüklenirken hata oluştu.');
      }
    } catch (err: any) {
      console.error('❌ Upload hatası:', err);
      setUploadError(err.response?.data?.detail || 'Dosya yüklenirken hata oluştu.');
    } finally {
      setUploading(false);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // ✅ Dosya seçim input'u
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      handleFileSelect(event.target.files[0]);
    }
  };

  // ✅ Drag & Drop
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleShowAllActivities = () => {
    setShowAllActivities(true);
    setPage(0);
  };

  const handleCloseActivities = () => {
    setShowAllActivities(false);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  useEffect(() => {
    if (user) {
      setLoading(false);
      fetchActivities();
    }
  }, [user]);

  // Analiz sayfalarına yönlendirme
  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  // Analiz kartları
  const analysisCards = [
    {
      title: 'Talep Tahmini',
      description: '4 farklı model ile talep tahmini yapar. Pattern analizi ile zenginleştirilmiştir.',
      icon: <ShowChart />,
      color: '#1976d2',
      path: '/forecast',
      tokenCost: 5,
      isAsync: true,
    },
    {
      title: 'Emniyet Stoğu',
      description: '6 farklı SS metodu ve talep pattern analizi ile optimum emniyet stok seviyelerini belirler.',
      icon: <Security />,
      color: '#2e7d32',
      path: '/safety-stock',
      tokenCost: 3,
      isAsync: true,
    },
    {
      title: 'Monte Carlo Simülasyonu',
      description: 'Binlerce senaryo ile stok performansınızı simüle edin.',
      icon: <Timeline />,
      color: '#9c27b0',
      path: '/simulation',
      tokenCost: 10,
      isAsync: true,
    },
    {
      title: 'Backtest',
      description: '8 farklı stratejiyi geçmiş veri üzerinde test eder.',
      icon: <Backpack />,
      color: '#ed6c02',
      path: '/backtest',
      tokenCost: 15,
      isAsync: true,
    },
    {
      title: 'Tedarikçi Analizi',
      description: 'Tedarikçi performansını ve risklerini analiz eder.',
      icon: <LocalShipping />,
      color: '#d32f2f',
      path: '/supplier',
      tokenCost: 8,
      isAsync: true,
    },
  ];

  // İstatistik kartları
  const statCards = [
    {
      title: 'Token Bakiyesi',
      value: userStats?.tokenBalance || 0,
      icon: <AttachMoney />,
      color: '#f9a825',
      subtitle: '💰 Mevcut token',
    },
    {
      title: 'Yüklenen Malzeme',
      value: userStats?.totalMaterials || 0,
      icon: <Inventory />,
      color: '#1976d2',
      subtitle: 'Excel\'den yüklendi',
    },
    {
      title: 'Toplam Analiz',
      value: userStats?.totalAnalyses || 0,
      icon: <Assessment />,
      color: '#2e7d32',
      subtitle: 'Bugüne kadar yapılan',
      trend: 12,
    },
    {
      title: 'Tamamlanan ASYNC',
      value: userStats?.completedTasks || 0,
      icon: <CheckCircle />,
      color: '#9c27b0',
      subtitle: 'Arka plan işlemleri',
    },
  ];

  // Pagination için aktiviteler
  const paginatedActivities = allActivities.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              👋 Hoş Geldin{user?.full_name ? `, ${user.full_name}` : ''}!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Bugün stok durumunu analiz etmeye ne dersin?
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => window.location.reload()}
              size="small"
            >
              Yenile
            </Button>
          </Box>
        </Box>
      </Box>

      {/* 📁 Excel Yükleme Alanı */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <CloudUpload color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Excel Dosyası Yükle
            </Typography>
            <Chip 
              label="Ücretsiz" 
              size="small" 
              color="success" 
              sx={{ ml: 1 }} 
            />
          </Box>

          <UploadArea
            className={isDragging ? 'dragging' : ''}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              {selectedFile ? (
                <>
                  <InsertDriveFile sx={{ fontSize: 48, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<UploadFile />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUpload();
                      }}
                      disabled={uploading}
                    >
                      {uploading ? 'Yükleniyor...' : 'Yükle'}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Clear />}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setUploadError(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                      disabled={uploading}
                    >
                      İptal
                    </Button>
                  </Box>
                </>
              ) : (
                <>
                  <CloudUpload sx={{ fontSize: 64, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Dosyayı Sürükle & Bırak veya Tıkla
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Excel dosyaları desteklenir (.xlsx, .xls)
                  </Typography>
                  <Chip 
                    label="Maksimum dosya boyutu: 10 MB" 
                    size="small" 
                    variant="outlined" 
                  />
                </>
              )}
            </Box>
          </UploadArea>

          <VisuallyHiddenInput
            type="file"
            accept=".xlsx,.xls"
            ref={fileInputRef}
            onChange={handleFileInputChange}
          />

          {/* Upload Progress */}
          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress 
                variant="determinate" 
                value={uploadProgress} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Yükleniyor... %{uploadProgress}
              </Typography>
            </Box>
          )}

          {/* Upload Success */}
          {uploadSuccess && (
            <Alert severity="success" sx={{ mt: 2 }} onClose={() => setUploadSuccess(false)}>
              ✅ Dosya başarıyla yüklendi! Analizlere başlayabilirsiniz.
            </Alert>
          )}

          {/* Upload Error */}
          {uploadError && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setUploadError(null)}>
              {uploadError}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <StatCard
              title={stat.title}
              value={stat.value}
              icon={stat.icon}
              color={stat.color}
              subtitle={stat.subtitle}
              trend={stat.trend}
              loading={statsLoading}
            />
          </Grid>
        ))}
      </Grid>

      {/* Hızlı Erişim Analizleri */}
      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
        🚀 Hızlı Analiz
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {analysisCards.map((card, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={index}>
            <AnalysisCard
              title={card.title}
              description={card.description}
              icon={card.icon}
              color={card.color}
              path={card.path}
              tokenCost={card.tokenCost}
              isAsync={card.isAsync}
              onClick={() => navigateTo(card.path)}
            />
          </Grid>
        ))}
      </Grid>

      {/* Alt Kısım: Aktivite ve Bilgiler */}
      <Grid container spacing={3}>
        {/* Son Aktiviteler */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  📋 Son Aktiviteler
                </Typography>
                {!showAllActivities && allActivities.length > 5 && (
                  <Button size="small" onClick={handleShowAllActivities}>
                    Tümünü Gör
                  </Button>
                )}
                {showAllActivities && (
                  <Button size="small" onClick={handleCloseActivities}>
                    Kapat
                  </Button>
                )}
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {allActivities.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Info color="disabled" sx={{ fontSize: 40 }} />
                  <Typography variant="body2" color="text.secondary">
                    Henüz aktivite yok. İlk analizini başlat!
                  </Typography>
                </Box>
              ) : (
                <>
                  {!showAllActivities ? (
                    <List disablePadding>
                      {activities.map((activity) => (
                        <ActivityItem key={activity.id} activity={activity} />
                      ))}
                    </List>
                  ) : (
                    <>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ bgcolor: 'grey.50' }}>
                              <TableCell>İşlem</TableCell>
                              <TableCell>Tarih</TableCell>
                              <TableCell>Detay</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {paginatedActivities.map((activity) => (
                              <TableRow key={activity.id} hover>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {activity.status === 'success' && <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />}
                                    {activity.status === 'warning' && <Warning sx={{ color: 'warning.main', fontSize: 16 }} />}
                                    {activity.status === 'error' && <Error sx={{ color: 'error.main', fontSize: 16 }} />}
                                    {activity.status === 'info' && <Info sx={{ color: 'info.main', fontSize: 16 }} />}
                                    {activity.message}
                                  </Box>
                                </TableCell>
                                <TableCell>{activity.time}</TableCell>
                                <TableCell>{activity.details || '-'}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <TablePagination
                        rowsPerPageOptions={[5, 10, 25]}
                        component="div"
                        count={allActivities.length}
                        rowsPerPage={rowsPerPage}
                        page={page}
                        onPageChange={handleChangePage}
                        onRowsPerPageChange={handleChangeRowsPerPage}
                        labelRowsPerPage="Sayfa başına satır:"
                        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
                      />
                    </>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Hızlı Bilgiler */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                ℹ️ Hızlı Bilgiler
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Paper sx={{ p: 2, bgcolor: 'success.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    💡 ASYNC Görevler
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Uzun süren analizleri arka planda çalıştırın. <br />
                    <strong>{userStats?.completedTasks || 0}</strong> görev tamamlandı.
                  </Typography>
                  <Button 
                    size="small" 
                    variant="outlined" 
                    sx={{ mt: 1 }}
                    onClick={() => navigateTo('/tasks')}
                  >
                    Görevleri Görüntüle
                  </Button>
                </Paper>

                <Paper sx={{ p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    📊 Token Sistemi
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Her analiz belirli sayıda token harcar. <br />
                    Mevcut token: <strong>{userStats?.tokenBalance || 0}</strong>
                  </Typography>
                </Paper>

                <Paper sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    📁 Veri Yönetimi
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    <strong>{userStats?.totalMaterials || 0}</strong> malzeme yüklü. <br />
                    Analiz sonuçları 15 gün saklanır.
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}