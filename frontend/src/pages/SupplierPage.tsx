import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TablePagination,
  Tooltip,
  Snackbar,
  LinearProgress,
} from '@mui/material';
import {
  LocalShipping,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface SupplierResult {
  supplier_id: string;
  name: string;
  risk_score: number;
  performance_score: number;
  ontime_rate: number;
  lt_mean: number;
  lt_std: number;
  factor: number;
  material_count: number;
  total_share: number;
  risk_level: string;
  performance_level: string;
  recommendation: string;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function SupplierPage() {
  const { user, fetchUser } = useAuth();
  const [hasSupplierData, setHasSupplierData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [suppliers, setSuppliers] = useState<SupplierResult[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [asyncLoading, setAsyncLoading] = useState(false);

  // ✅ State'ler
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);

  // ✅ Snackbar
  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'info' 
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // ✅ Kredi maliyeti
  const { data: costData } = useQuery({
    queryKey: ['supplier-cost'],
    queryFn: async () => {
      try {
        const res = await api.get('/api/cost', {
          params: {
            endpoint: '/api/supplier/optimize-shares',
            method: 'POST'
          }
        });
        return res.data;
      } catch (error) {
        console.error('❌ Kredi cost hatası:', error);
        return { cost: 8 };
      }
    },
    initialData: { cost: 8 },
    staleTime: 60000,
  });

  useEffect(() => {
    checkSupplierData();
  }, []);

  const checkSupplierData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/supplier/check');
      const hasData = res.data.has_suppliers === true;
      setHasSupplierData(hasData);
      if (!hasData) {
        setError('Tedarikçi verisi bulunamadı. Lütfen Excel\'e "Tedarikciler" ve "Malzeme_Tedarikciler" sheet\'lerini ekleyin.');
      }
    } catch (error) {
      console.error('❌ Tedarikçi veri kontrolü hatası:', error);
      setHasSupplierData(false);
      setError('Veri kontrolü sırasında hata oluştu.');
    } finally {
      setIsCheckingData(false);
    }
  };

  // 📌 SENKRON Tedarikçi Analizi
  const supplierMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Tedarikçi analizi başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/supplier/optimize-shares', {});
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setSuppliers(data.suppliers || []);
        setRecommendations(data.recommendations || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total_suppliers || 0} tedarikçi başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
        await fetchUser();
      } else {
        setError(data.error || 'Tedarikçi analizi başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Tedarikçi analizi hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Tedarikçi Analizi
  const asyncSupplierMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/supplier/batch/async', {});
      return res.data;
    },
    onSuccess: (data) => {
      setActiveAsyncTask(data.task_id);
      setSnackbar({
        open: true,
        message: `✅ Rapor talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0,8)}
📋 ASYNC Görevler sayfasından ilerlemenizi takip edebilirsiniz.`,
        severity: 'success',
      });
      setProgress(10);
      setProgressLabel('İşlem kuyruğa alındı.');
      
      const intervalId = setInterval(() => {
        checkAsyncProgress(data.task_id);
      }, 3000);
      
      setTimeout(() => {
        clearInterval(intervalId);
        if (isProcessing) {
          setIsProcessing(false);
          setActiveAsyncTask(null);
          setError('Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.');
        }
      }, 300000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
    },
  });

  // 📌 Async İlerleme Kontrol
  const checkAsyncProgress = async (taskId: string) => {
    if (!taskId) return;
    try {
      const res = await api.get(`/api/forecast/async/status/${taskId}`);
      const status = res.data;
      
      setProgress(status.progress || 50);
      setProgressLabel(status.message || 'İşleniyor...');
      
      if (status.status === 'completed') {
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(100);
        setProgressLabel('Tamamlandı!');
        
        const resultsRes = await api.get(`/api/forecast/async/result/${taskId}`);
        if (resultsRes.data.success) {
          setSuppliers(resultsRes.data.suppliers || []);
          setRecommendations(resultsRes.data.recommendations || []);
          setPage(0);
          setSuccess(`${resultsRes.data.total_suppliers || 0} tedarikçi başarıyla analiz edildi.`);
          setTimeout(() => setSuccess(null), 5000);
          await fetchUser();
        }
        return;
      }
      
      if (status.status === 'failed' || status.status === 'error') {
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(0);
        setProgressLabel('Hata!');
        setError(status.message || 'Async analiz başarısız oldu');
        return;
      }
    } catch (error) {
      console.error('Async durum kontrol hatası:', error);
      setIsProcessing(false);
      setActiveAsyncTask(null);
      setError('Async durum kontrolü başarısız');
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'supplier_batch', limit: 100 }
      });
      
      if (res.data.success) {
        const rawResults = res.data.results || [];
        const groupedMap = new Map();
        
        rawResults.forEach((item: any) => {
          const date = item.created_at ? new Date(item.created_at) : new Date();
          const key = date.toISOString().slice(0, 16);
          
          if (!groupedMap.has(key)) {
            groupedMap.set(key, {
              id: item.id,
              created_at: item.created_at,
              items: []
            });
          }
          groupedMap.get(key).items.push(item);
        });
        
        const groupedResults = Array.from(groupedMap.values()).map(group => {
          const firstItem = group.items[0] || {};
          const resultData = firstItem.data || firstItem.result_data || {};
          
          const allResults = group.items
            .map((item: any) => {
              const data = item.data || item.result_data || {};
              if (data.suppliers && Array.isArray(data.suppliers)) {
                return data.suppliers;
              }
              return [];
            })
            .flat();
          
          return {
            id: group.id,
            created_at: group.created_at,
            data: {
              total: allResults.length,
              suppliers: allResults,
              recommendations: resultData.recommendations || []
            }
          };
        });
        
        setHistoryData(groupedResults);
        setHistoryDialogOpen(true);
        setError(null);
      } else {
        setError('Geçmiş sonuçlar yüklenemedi');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Geçmiş sonuçlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleViewHistory = (item: HistoryItem) => {
    const historySuppliers = item.data?.suppliers || [];
    if (historySuppliers.length > 0) {
      setSuppliers(historySuppliers);
      setRecommendations(item.data?.recommendations || []);
      setPage(0);
      setHistoryDialogOpen(false);
      setSuccess(`${historySuppliers.length} tedarikçi geçmiş sonuçları yüklendi.`);
      setTimeout(() => setSuccess(null), 3000);
    } else {
      setError('Bu kayıtta görüntülenecek sonuç yok');
    }
  };

  const handleExport = async () => {
    if (suppliers.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }
    try {
      const response = await api.post('/api/export/supplier-results', {
        suppliers: suppliers,
        recommendations: recommendations
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tedarikci_${new Date().toISOString().slice(0,10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Excel dosyası başarıyla indirildi.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Excel dosyası oluşturulamadı');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => setPage(newPage);
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const paginatedSuppliers = suppliers.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getRiskColor = (riskLevel: string) => {
    switch(riskLevel) {
      case 'DÜŞÜK': return 'success';
      case 'ORTA': return 'warning';
      case 'YÜKSEK': return 'error';
      default: return 'default';
    }
  };

  const getPerformanceColor = (perfLevel: string) => {
    switch(perfLevel) {
      case 'İYİ': return 'success';
      case 'ORTA': return 'warning';
      case 'KÖTÜ': return 'error';
      default: return 'default';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch(riskLevel) {
      case 'DÜŞÜK': return <CheckCircle fontSize="small" />;
      case 'ORTA': return <Warning fontSize="small" />;
      case 'YÜKSEK': return <Error fontSize="small" />;
      default: return <Info fontSize="small" />;
    }
  };

  return (
    <Box>
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={8000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          sx={{ whiteSpace: 'pre-line' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            🏭 Tedarikçi Analizi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Tedarikçi performansını ve risklerini analiz eder.
            <Chip 
              label={`${costData?.cost || 8} Kredi`} 
              size="small" 
              color="warning" 
              sx={{ ml: 1 }} 
            />
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<History />} onClick={fetchHistory} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Geçmiş'}
          </Button>
          <Button
            variant="contained"
            startIcon={supplierMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => supplierMutation.mutate()}
            disabled={supplierMutation.isPending || !hasSupplierData}
          >
            {supplierMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={asyncSupplierMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => asyncSupplierMutation.mutate()}
            disabled={asyncSupplierMutation.isPending || !hasSupplierData || isProcessing}
          >
            {asyncSupplierMutation.isPending ? 'Başlatılıyor...' : 'ASYNC Analiz'}
          </Button>
        </Box>
      </Box>

      {/* Alert'ler */}
      {error && (
        <Alert 
          severity={error.includes('Tedarikçi') ? 'warning' : 'error'} 
          sx={{ mb: 3 }} 
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      {/* Veri kontrol durumu */}
      {isCheckingData && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          icon={<CircularProgress size={20} />}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            🔍 Tedarikçi verisi kontrol ediliyor...
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Lütfen birkaç saniye bekleyin. Tedarikçi verileri tespit edildiğinde analiz yapabilirsiniz.
          </Typography>
        </Alert>
      )}

      {!isCheckingData && hasSupplierData && suppliers.length === 0 && !error && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            ✅ Tedarikçi verileri tespit edildi! Analiz yapabilirsiniz.
          </Typography>
        </Alert>
      )}

      {/* Bilgilendirme Kartı */}
      <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              📊 Tedarikçi Analizi Metrikleri
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Risk Skoru" size="small" color="error" />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                0-1 arası, 1 en riskli
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Performans Skoru" size="small" color="success" />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                0-1 arası, 1 en iyi
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Zamanında Teslimat" size="small" color="primary" />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                Yüzde olarak teslimat başarısı
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Lead Time" size="small" color="warning" />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                Ortalama teslimat süresi (gün)
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Kredi Bakiyesi */}
      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Kredi Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına {costData?.cost || 8} kredi harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {/* İlerleme Durumu */}
      {isProcessing && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, justifyContent: 'center' }}>
            <CircularProgress variant="determinate" value={progress} size={40} />
            <Typography variant="body2" color="text.secondary">{progressLabel}</Typography>
            {activeAsyncTask && (
              <Typography variant="caption" color="text.secondary">
                (ID: {activeAsyncTask.slice(0,8)})
              </Typography>
            )}
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ mt: 1, maxWidth: 400, mx: 'auto', height: 6, borderRadius: 3 }}
          />
        </Box>
      )}

      {/* Tavsiyeler */}
      {recommendations.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'success.light' }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
              💡 Tavsiyeler
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {recommendations.map((rec, idx) => (
                <li key={idx}>
                  <Typography variant="body2">{rec}</Typography>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Sonuçlar */}
      {suppliers.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Tedarikçiler ({suppliers.length})
              </Typography>
              <Button variant="outlined" startIcon={<Download />} onClick={handleExport} size="small">
                Excel'e Aktar
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Tedarikçi</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Risk</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Performans</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Zamanında %</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">LT (gün)</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Pay %</TableCell>
                    <TableCell sx={{ color: 'white' }}>Tavsiye</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedSuppliers.map((supplier) => (
                    <TableRow key={supplier.supplier_id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {supplier.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {supplier.supplier_id}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={`Risk Skoru: ${supplier.risk_score}`} arrow>
                          <Chip
                            icon={getRiskIcon(supplier.risk_level)}
                            label={supplier.risk_level}
                            size="small"
                            color={getRiskColor(supplier.risk_level)}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={`Performans Skoru: ${supplier.performance_score}`} arrow>
                          <Chip
                            label={supplier.performance_level}
                            size="small"
                            color={getPerformanceColor(supplier.performance_level)}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        {supplier.ontime_rate}%
                      </TableCell>
                      <TableCell align="center">
                        {supplier.lt_mean} ± {supplier.lt_std}
                      </TableCell>
                      <TableCell align="center">
                        {(supplier.total_share * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <Tooltip title={supplier.recommendation} arrow>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              cursor: 'pointer',
                              display: 'block',
                              maxWidth: 250,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {supplier.recommendation}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[25, 50, 100, 200]}
                component="div"
                count={suppliers.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                labelRowsPerPage="Sayfa başına satır:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
              />
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Boş Durum */}
      {!isProcessing && suppliers.length === 0 && !error && hasSupplierData && !isCheckingData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <LocalShipping sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">Henüz analiz yapılmadı</Typography>
            <Typography variant="body2" color="text.secondary">"Analiz Et" butonuna tıklayarak tedarikçi analizini başlatın.</Typography>
          </CardContent>
        </Card>
      )}

      {/* Geçmiş Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📋 Geçmiş Tedarikçi Analiz Sonuçları</Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)}><Close /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {historyData.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              Henüz geçmiş analiz kaydı yok.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Tarih</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Tedarikçi Sayısı</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Durum</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">İşlem</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {historyData.map((item) => {
                    const total = item.data?.total || 0;
                    const date = item.created_at ? new Date(item.created_at) : new Date();
                    return (
                      <TableRow key={item.id}>
                        <TableCell>
                          {date.toLocaleDateString('tr-TR')} {date.toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'})}
                        </TableCell>
                        <TableCell align="center"><Chip label={`${total}`} size="small" color="primary" /></TableCell>
                        <TableCell align="center"><Chip label="Başarılı" size="small" color="success" /></TableCell>
                        <TableCell align="center">
                          <Button size="small" variant="outlined" startIcon={<Visibility />} onClick={() => handleViewHistory(item)}>Görüntüle</Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setHistoryDialogOpen(false)}>Kapat</Button></DialogActions>
      </Dialog>
    </Box>
  );
}