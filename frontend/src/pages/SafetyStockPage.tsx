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
  Divider,
  TablePagination,
  Snackbar,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  LinearProgress,
} from '@mui/material';
import {
  Security,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface SafetyStockResult {
  material_code: string;
  group: string;
  lead_time_days: number;
  pattern: string;
  pattern_label: string;
  pattern_color: string;
  cv: number;
  zero_ratio: number;
  trend: number;
  classic_ss: number;
  croston_ss: number;
  syntetos_boylan_ss: number;
  bootstrapping_ss: number;
  ml_ss: number;
  hybrid_ss: number;
  recommended_method: string;
  recommended_method_label: string;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function SafetyStockPage() {
  const { user, fetchUser } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);
  const [results, setResults] = useState<SafetyStockResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [asyncLoading, setAsyncLoading] = useState(false);

  // ✅ State'ler
  const [serviceLevel, setServiceLevel] = useState(0.95);
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
    queryKey: ['safety-stock-cost'],
    queryFn: async () => {
      try {
        const res = await api.get('/api/cost', {
          params: {
            endpoint: '/api/safety-stock',
            method: 'POST'
          }
        });
        return res.data;
      } catch (error) {
        console.error('❌ Kredi cost hatası:', error);
        return { cost: 3 };
      }
    },
    initialData: { cost: 3 },
    staleTime: 60000,
  });

  useEffect(() => {
    checkUploadedData();
  }, []);

  const checkUploadedData = async () => {
    setIsCheckingData(true);
    try {
      const res = await api.get('/api/upload/status');
      const hasData = res.data.has_data === true;
      setHasUploadedData(hasData);
      if (!hasData) {
        setError('Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard\'dan dosya yükleyin.');
      }
    } catch (error) {
      console.error('❌ Veri kontrolü hatası:', error);
      setHasUploadedData(false);
      setError('Veri kontrolü sırasında hata oluştu.');
    } finally {
      setIsCheckingData(false);
    }
  };

  // 📌 SENKRON Safety Stock
  const ssMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/safety-stock/batch', {
        service_level: serviceLevel,
      });
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: async (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
        await fetchUser();
      } else {
        setError(data.error || 'Analiz başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
        setIsProcessing(false);
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Safety Stock hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 ASYNC Safety Stock
  const asyncSsMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);
      const res = await api.post('/api/safety-stock/batch/async', {
        service_level: serviceLevel,
      });
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
      
      // Async kontrol için interval başlat
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
          setResults(resultsRes.data.results || []);
          setPage(0);
          setSuccess(`${resultsRes.data.total || 0} malzeme başarıyla analiz edildi.`);
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
        params: { result_type: 'safety_stock_batch', limit: 100 }
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
          const allResults = group.items
            .map((item: any) => {
              const resultData = item.data || item.result_data || {};
              if (resultData.results && Array.isArray(resultData.results)) {
                return resultData.results;
              }
              if (resultData.material_code) {
                return [resultData];
              }
              return [];
            })
            .flat();
          
          return {
            id: group.id,
            created_at: group.created_at,
            data: {
              total: allResults.length,
              results: allResults
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
    const historyResults = item.data?.results || [];
    if (historyResults.length > 0) {
      setResults(historyResults);
      setPage(0);
      setHistoryDialogOpen(false);
      setSuccess(`${historyResults.length} malzeme geçmiş sonuçları yüklendi.`);
      setTimeout(() => setSuccess(null), 3000);
    } else {
      setError('Bu kayıtta görüntülenecek sonuç yok');
    }
  };

  const handleExport = async () => {
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }
    try {
      const response = await api.post('/api/export/safety-stock-results', {
        results: results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `safety_stock_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const paginatedResults = results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getBestMethod = (result: SafetyStockResult) => {
    const methods = ['classic_ss', 'croston_ss', 'syntetos_boylan_ss', 'bootstrapping_ss', 'ml_ss', 'hybrid_ss'];
    const values = methods.map(m => result[m as keyof SafetyStockResult] as number);
    const min = Math.min(...values);
    return methods[values.indexOf(min)];
  };

  const methodLabels: Record<string, string> = {
    classic_ss: 'Klasik SS',
    croston_ss: 'Croston',
    syntetos_boylan_ss: 'Syntetos-Boylan',
    bootstrapping_ss: 'Bootstrapping',
    ml_ss: 'ML Tabanlı',
    hybrid_ss: 'Hibrit (Önerilen)',
  };

  const getPatternColor = (color: string) => {
    switch(color) {
      case 'success': return 'success';
      case 'info': return 'info';
      case 'warning': return 'warning';
      case 'error': return 'error';
      case 'primary': return 'primary';
      case 'secondary': return 'secondary';
      default: return 'default';
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
            🛡️ Emniyet Stoğu (Safety Stock) Analizi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            6 farklı SS metodu ve talep pattern analizi ile optimum emniyet stok seviyelerini belirler.
            <Chip 
              label={`${costData?.cost || 3} Kredi`} 
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
            startIcon={ssMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => ssMutation.mutate()}
            disabled={ssMutation.isPending || !hasUploadedData}
          >
            {ssMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={asyncSsMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => asyncSsMutation.mutate()}
            disabled={asyncSsMutation.isPending || !hasUploadedData || isProcessing}
          >
            {asyncSsMutation.isPending ? 'Başlatılıyor...' : 'ASYNC Analiz'}
          </Button>
        </Box>
      </Box>

      {/* Alert'ler */}
      {error && (
        <Alert 
          severity={error.includes('Excel') ? 'warning' : 'error'} 
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
            🔍 Veri kontrolü yapılıyor...
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Lütfen birkaç saniye bekleyin. Excel dosyası tespit edildiğinde analiz yapabilirsiniz.
          </Typography>
        </Alert>
      )}

      {!isCheckingData && hasUploadedData && results.length === 0 && !error && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            ✅ Veri tespit edildi! Analiz yapabilirsiniz.
          </Typography>
        </Alert>
      )}

      {/* 📌 Parametre Kartı */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="body2" gutterBottom>
                Servis Seviyesi: {(serviceLevel * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={serviceLevel}
                onChange={(_, val) => setServiceLevel(val as number)}
                min={0.80}
                max={0.99}
                step={0.01}
                marks={[
                  { value: 0.85, label: '85%' },
                  { value: 0.90, label: '90%' },
                  { value: 0.95, label: '95%' },
                  { value: 0.99, label: '99%' },
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="caption" color="text.secondary">
                📊 Daha yüksek servis seviyesi = daha yüksek emniyet stoğu
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Bilgilendirme Kartı */}
      <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              📊 6 Farklı SS Metodu ve Talep Patterni Eşleşmeleri
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Klasik SS" size="small" color="success" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Düzenli Sabit Talep
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Croston" size="small" color="warning" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Aralıklı Düşük Talep
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Syntetos-Boylan" size="small" color="warning" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Aralıklı Yüksek Talep
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Bootstrapping" size="small" color="error" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Aşırı Değişken Talep
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="ML Tabanlı" size="small" color="secondary" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Değişken / Yüksek Değişken
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Hibrit (Önerilen)" size="small" color="primary" />
                <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                  Düzenli Artan / Azalan
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Kredi Bakiyesi */}
      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Kredi Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına {costData?.cost || 3} kredi harcanır</Typography>
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

      {/* Sonuçlar */}
      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Sonuçlar ({results.length} malzeme)
              </Typography>
              <Button variant="outlined" startIcon={<Download />} onClick={handleExport} size="small">
                Excel'e Aktar
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Malzeme Kodu</TableCell>
                    <TableCell sx={{ color: 'white' }}>Grup</TableCell>
                    <TableCell sx={{ color: 'white' }}>Pattern</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">CV</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Klasik</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Croston</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">SB</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Bootstrap</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">ML</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Hibrit</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Önerilen</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => {
                    const best = getBestMethod(result);
                    return (
                      <TableRow key={idx}>
                        <TableCell>{result.material_code}</TableCell>
                        <TableCell>{result.group}</TableCell>
                        <TableCell>
                          <Tooltip title={`CV: ${result.cv}, Zero Ratio: ${result.zero_ratio}`} arrow>
                            <Chip
                              label={result.pattern_label}
                              size="small"
                              color={getPatternColor(result.pattern_color)}
                              variant="outlined"
                            />
                          </Tooltip>
                        </TableCell>
                        <TableCell align="right">{result.cv.toFixed(3)}</TableCell>
                        <TableCell align="right">{result.classic_ss?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="right">{result.croston_ss?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="right">{result.syntetos_boylan_ss?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="right">{result.bootstrapping_ss?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="right">{result.ml_ss?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {result.hybrid_ss?.toFixed(0) || '-'}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={result.recommended_method_label || methodLabels[best] || best}
                            size="small"
                            color={result.recommended_method === best ? 'success' : 'default'}
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[25, 50, 100, 200]}
                component="div"
                count={results.length}
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
      {!isProcessing && results.length === 0 && !error && hasUploadedData && !isCheckingData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Security sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">Henüz analiz yapılmadı</Typography>
            <Typography variant="body2" color="text.secondary">"Analiz Et" butonuna tıklayarak emniyet stoğu analizini başlatın.</Typography>
          </CardContent>
        </Card>
      )}

      {/* Geçmiş Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📋 Geçmiş Analiz Sonuçları</Typography>
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
                    <TableCell sx={{ color: 'white' }} align="center">Malzeme Sayısı</TableCell>
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