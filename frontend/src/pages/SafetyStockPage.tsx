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
import { useMutation } from '@tanstack/react-query';
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
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [results, setResults] = useState<SafetyStockResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<HistoryItem | null>(null);
  const [asyncLoading, setAsyncLoading] = useState(false);

  // ✅ Snackbar state
  const [snackbar, setSnackbar] = useState<{ 
    open: boolean; 
    message: string; 
    severity: 'success' | 'error' | 'info' 
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  useEffect(() => {
    checkUploadedData();
  }, []);

  const checkUploadedData = async () => {
    try {
      const res = await api.get('/api/upload/status');
      setHasUploadedData(res.data.has_data);
    } catch {
      setHasUploadedData(false);
    }
  };

  // 📌 SENKRON Safety Stock
  const ssMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/safety-stock/batch', {
        materials: [],
        service_level: 0.95,
        save_results: true
      });
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.error || 'Analiz başarısız');
      }
    },
    onError: (err: any) => {
      console.error('❌ Safety Stock hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
    },
  });

  // 📌 ASYNC Safety Stock
  const asyncSsMutation = useMutation({
    mutationFn: async () => {
      setAsyncLoading(true);
      const res = await api.post('/api/safety-stock/batch/async', {
        service_level: 0.95
      });
      return res.data;
    },
    onSuccess: (data) => {
      setAsyncLoading(false);
      setSnackbar({
        open: true,
        message: `✅ Safety Stock analizi talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0,8)}
        
📋 ASYNC Görevler sayfasından ilerlemenizi takip edebilirsiniz.`,
        severity: 'success',
      });
    },
    onError: (err: any) => {
      setAsyncLoading(false);
      setError(err.response?.data?.detail || 'Async safety stock analizi başlatılamadı');
    },
  });

  // ✅ Geçmiş sonuçları getir
  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'safety_stock_batch' }
      });
      console.log('📋 Geçmiş cevabı:', res.data);
      
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
              total: 0,
              items: []
            });
          }
          
          const group = groupedMap.get(key);
          group.total += 1;
          group.items.push(item);
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
      console.error('❌ Geçmiş hatası:', err);
      setError(err.response?.data?.detail || 'Geçmiş sonuçlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  // ✅ Geçmiş sonucu görüntüle
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

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            🛡️ Emniyet Stoğu (Safety Stock) Analizi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            6 farklı SS metodu ve talep pattern analizi ile optimum emniyet stok seviyelerini belirler.
            <Chip label="10 Token" size="small" color="warning" sx={{ ml: 1 }} />
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
            disabled={asyncSsMutation.isPending || !hasUploadedData || asyncLoading}
          >
            {asyncSsMutation.isPending ? 'Başlatılıyor...' : 'ASYNC Analiz'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.</Alert>
      )}

      {/* ✅ Güncellenmiş bilgilendirme kartı - 6 metot + pattern eşleşmeleri */}
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

      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına 10 token harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {ssMutation.isPending && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Pattern analizi + 6 SS metodu hesaplanıyor...</Typography>
        </Box>
      )}

      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Sonuçlar ({results.length} malzeme)
              </Typography>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={handleExport}
                size="small"
              >
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

      {!ssMutation.isPending && results.length === 0 && !error && hasUploadedData && (
        <Card><CardContent sx={{ textAlign: 'center', py: 6 }}>
          <Security sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">Henüz analiz yapılmadı</Typography>
          <Typography variant="body2" color="text.secondary">"Analiz Et" butonuna tıklayarak safety stock analizini başlatın.</Typography>
        </CardContent></Card>
      )}

      {/* 📋 Geçmiş Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📋 Geçmiş Analiz Sonuçları</Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)}><Close /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {historyData.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>Henüz geçmiş analiz kaydı yok.</Typography>
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