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
  LinearProgress,
} from '@mui/material';
import {
  LocalShipping,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Warning,
  CheckCircle,
  Info,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
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
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [hasSuppliers, setHasSuppliers] = useState(false);
  const [results, setResults] = useState<SupplierResult[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    checkUploadedData();
    checkSupplierData();
  }, []);

  const checkUploadedData = async () => {
    try {
      const res = await api.get('/api/upload/status');
      setHasUploadedData(res.data.has_data);
    } catch {
      setHasUploadedData(false);
    }
  };

  const checkSupplierData = async () => {
    try {
      const res = await api.get('/api/supplier/check');
      setHasSuppliers(res.data.has_suppliers);
      if (!res.data.has_suppliers && hasUploadedData) {
        setError(res.data.message || 'Tedarikçi verisi bulunamadı.');
      }
    } catch {
      setHasSuppliers(false);
    }
  };

  const supplierMutation = useMutation({
    mutationFn: async () => {
      setProgress(10);
      setProgressLabel('Tedarikçi analizi başlatılıyor...');
      const res = await api.post('/api/supplier/batch');
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setResults(data.suppliers || []);
        setRecommendations(data.recommendations || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total_suppliers || data.suppliers?.length || 0} tedarikçi başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.error || 'Tedarikçi analizi başarısız');
        if (data.has_suppliers === false) {
          setHasSuppliers(false);
        }
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Tedarikçi analiz hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'supplier_batch' }
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
          const firstItem = group.items[0];
          const resultData = firstItem.data || firstItem.result_data || {};
          
          return {
            id: group.id,
            created_at: group.created_at,
            data: {
              total: resultData.suppliers?.length || 0,
              results: resultData.suppliers || [],
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
    const historyResults = item.data?.results || [];
    if (historyResults.length > 0) {
      setResults(historyResults);
      setRecommendations(item.data?.recommendations || []);
      setPage(0);
      setHistoryDialogOpen(false);
      setSuccess(`${historyResults.length} tedarikçi geçmiş sonuçları yüklendi.`);
      setTimeout(() => setSuccess(null), 3000);
    } else {
      setError('Bu kayıtta görüntülenecek sonuç yok');
    }
  };

  // ✅ Export işlemi - Doğru format
  const handleExport = async () => {
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }
    try {
      const response = await api.post('/api/export/supplier-results', {
        suppliers: results,        // ✅ Doğru: suppliers
        recommendations: recommendations  // ✅ Doğru: recommendations
      }, { 
        responseType: 'blob' 
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tedarikci_analiz_${new Date().toISOString().slice(0,10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Excel dosyası başarıyla indirildi.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Export hatası:', err);
      setError('Excel dosyası oluşturulamadı');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => setPage(newPage);
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const paginatedResults = results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const getRiskColor = (risk: number) => {
    if (risk > 0.4) return 'error';
    if (risk > 0.2) return 'warning';
    return 'success';
  };

  const getPerformanceColor = (perf: number) => {
    if (perf > 0.7) return 'success';
    if (perf > 0.4) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            🚚 Tedarikçi Yönetimi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Tedarikçi risk ve performans analizi, pay optimizasyonu.
            <Chip label="5 Token" size="small" color="warning" sx={{ ml: 1 }} />
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<History />} onClick={fetchHistory} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Geçmiş'}
          </Button>
          {results.length > 0 && (
            <Button variant="outlined" startIcon={<Download />} onClick={handleExport}>
              Excel'e Aktar
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={supplierMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => supplierMutation.mutate()}
            disabled={supplierMutation.isPending || !hasUploadedData}
          >
            {supplierMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.</Alert>
      )}
      
      {hasUploadedData && !hasSuppliers && !results.length && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          ⚠️ Tedarikçi verisi bulunamadı. Excel'de "Tedarikciler" ve "Malzeme_Tedarikciler" sheet'leri olmalıdır.
        </Alert>
      )}

      {recommendations.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Info color="info" />
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                📊 Tedarikçi Önerileri
              </Typography>
            </Box>
            {recommendations.map((rec, idx) => (
              <Typography key={idx} variant="body2" sx={{ fontSize: '0.9rem', mb: 0.5 }}>
                • {rec}
              </Typography>
            ))}
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına 5 token harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {supplierMutation.isPending && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress variant="determinate" value={progress} size={60} />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="caption" component="div" color="text.secondary">
                {progress}%
              </Typography>
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {progressLabel}
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ mt: 2, maxWidth: 400, mx: 'auto', height: 8, borderRadius: 4 }}
          />
        </Box>
      )}

      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Tedarikçiler ({results.length})</Typography>
            </Box>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Tedarikçi</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Risk</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Performans</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Zamanında</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">LT (Gün)</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Malzeme</TableCell>
                    <TableCell sx={{ color: 'white' }}>Tavsiye</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {result.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {result.supplier_id}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={`Risk Skoru: ${(result.risk_score * 100).toFixed(0)}%`} arrow>
                          <Chip
                            label={result.risk_level}
                            size="small"
                            color={getRiskColor(result.risk_score)}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={`Performans: ${(result.performance_score * 100).toFixed(0)}%`} arrow>
                          <Chip
                            label={result.performance_level}
                            size="small"
                            color={getPerformanceColor(result.performance_score)}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">{result.ontime_rate.toFixed(0)}%</TableCell>
                      <TableCell align="center">
                        {result.lt_mean.toFixed(0)} ± {result.lt_std.toFixed(0)}
                      </TableCell>
                      <TableCell align="center">{result.material_count}</TableCell>
                      <TableCell>
                        <Tooltip title={result.recommendation} arrow>
                          <Typography variant="caption" sx={{ cursor: 'pointer' }}>
                            {result.recommendation.substring(0, 30)}...
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

      {!supplierMutation.isPending && results.length === 0 && !error && hasUploadedData && hasSuppliers && (
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
                        <TableCell>{date.toLocaleDateString('tr-TR')} {date.toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'})}</TableCell>
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