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
} from '@mui/material';
import {
  Backpack,
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

interface BacktestResult {
  material_code: string;
  group: string;
  best_strategy: string;
  service_level: number;
  total_cost: number;
  holding_cost: number;
  shortage_cost: number;
  stockout_probability: number;
  tail_risk: number;
  tail_risk_level: string;
  total_shortage: number;
  strategies_tested: number;
  strategy_details: any;
  recommendation: string;
  current_rop: number;
  recommended_rop: number;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function BacktestPage() {
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
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

  // 📌 SENKRON Backtest
  const backtestMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/backtest/batch', {});
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla test edildi.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.error || 'Backtest başarısız');
      }
    },
    onError: (err: any) => {
      console.error('❌ Backtest hatası:', err);
      setError(err.response?.data?.detail || 'Backtest sırasında hata oluştu');
    },
  });

  // 📌 ASYNC Backtest
  const asyncBacktestMutation = useMutation({
    mutationFn: async () => {
      setAsyncLoading(true);
      const res = await api.post('/api/backtest/batch/async', {});
      return res.data;
    },
    onSuccess: (data) => {
      setAsyncLoading(false);
      setSnackbar({
        open: true,
        message: `✅ Backtest talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0,8)}
        
📋 ASYNC Görevler sayfasından ilerlemenizi takip edebilirsiniz.`,
        severity: 'success',
      });
    },
    onError: (err: any) => {
      setAsyncLoading(false);
      setError(err.response?.data?.detail || 'Async backtest başlatılamadı');
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'backtest_batch' }
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
      const response = await api.post('/api/export/backtest-results', {
        results: results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backtest_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const strategyColors: Record<string, string> = {
    'ai': '#9c27b0',
    'classic': '#1976d2',
    'croston': '#2e7d32',
    'syntetos_boylan': '#ed6c02',
    'ml': '#d32f2f',
    'hybrid': '#1f4e79',
    'simple_moving_avg': '#00897b',
    'last_value': '#6d4c41'
  };

  const strategyLabels: Record<string, string> = {
    ai: 'AI',
    classic: 'Classic',
    croston: 'Croston',
    syntetos_boylan: 'SB',
    ml: 'ML',
    hybrid: 'Hybrid',
    simple_moving_avg: 'Simple MA',
    last_value: 'Last Value'
  };

  const strategyDescriptions: Record<string, string> = {
    ai: 'Pattern multiplier + hibrit',
    classic: 'Normal dağılım varsayımı',
    croston: 'Aralıklı talep için',
    syntetos_boylan: 'Croston bias düzeltmeli',
    ml: 'CV, zero_ratio, trend',
    hybrid: 'Tüm metodların ortalaması',
    simple_moving_avg: 'Son 4 hafta ortalaması',
    last_value: 'Son değer (naif)'
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
            🎒 Backtest
          </Typography>
          <Typography variant="body1" color="text.secondary">
            8 farklı stratejiyi geçmiş veri üzerinde test eder.
            <Chip label="15 Token" size="small" color="warning" sx={{ ml: 1 }} />
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<History />} onClick={fetchHistory} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Geçmiş'}
          </Button>
          <Button
            variant="contained"
            startIcon={backtestMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => backtestMutation.mutate()}
            disabled={backtestMutation.isPending || !hasUploadedData}
          >
            {backtestMutation.isPending ? 'Test Ediliyor...' : 'Testi Başlat'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={asyncBacktestMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => asyncBacktestMutation.mutate()}
            disabled={asyncBacktestMutation.isPending || !hasUploadedData || asyncLoading}
          >
            {asyncBacktestMutation.isPending ? 'Başlatılıyor...' : 'ASYNC Test'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.</Alert>
      )}

      {/* Strateji Bilgilendirme Kartı */}
      <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              📊 Backtest Stratejileri
            </Typography>
          </Box>
          <Grid container spacing={2}>
            {Object.entries(strategyLabels).map(([key, label]) => (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={key}>
                <Chip 
                  label={label} 
                  size="small" 
                  sx={{ bgcolor: strategyColors[key] || '#1976d2', color: 'white', fontWeight: 'bold' }} 
                />
                <Typography variant="body2" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
                  {strategyDescriptions[key] || ''}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına 15 token harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {backtestMutation.isPending && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>8 strateji test ediliyor...</Typography>
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
              >
                Excel'e Aktar
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>
                      Malzeme Kodu
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>
                      Grup
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>
                      En İyi Strateji
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Servis %
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Tail Risk
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Maliyet (TL)
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>
                      Tavsiye
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {result.material_code}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={result.group} 
                          size="small" 
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={strategyLabels[result.best_strategy] || result.best_strategy} 
                          size="small" 
                          sx={{ 
                            bgcolor: strategyColors[result.best_strategy] || '#1976d2',
                            color: 'white',
                            fontWeight: 'bold'
                          }} 
                        />
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                        {(result.service_level * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={result.tail_risk?.toFixed(2) || '-'}
                          size="small"
                          color={
                            result.tail_risk > 0.5 ? 'error' :
                            result.tail_risk > 0.3 ? 'warning' : 'success'
                          }
                          sx={{ minWidth: 50 }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {result.total_cost?.toFixed(0) || '-'}
                      </TableCell>
                      <TableCell>
                        <Tooltip title={result.recommendation || ''} arrow>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              cursor: 'pointer',
                              display: 'block',
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {result.recommendation?.split(' | ')[0] || '-'}
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

            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama Servis</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + (r.service_level || 0), 0) / results.length * 100).toFixed(1)}%
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama Tail Risk</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + (r.tail_risk || 0), 0) / results.length).toFixed(2)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama Maliyet</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + (r.total_cost || 0), 0) / results.length).toFixed(0)} TL
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                    <Typography variant="caption" color="text.secondary">En Çok Strateji</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(() => {
                        const counts: Record<string, number> = {};
                        results.forEach(r => {
                          counts[r.best_strategy] = (counts[r.best_strategy] || 0) + 1;
                        });
                        const entries = Object.entries(counts);
                        if (entries.length === 0) return '-';
                        const sorted = entries.sort((a, b) => b[1] - a[1]);
                        return strategyLabels[sorted[0][0]] || sorted[0][0];
                      })()}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </CardContent>
        </Card>
      )}

      {!backtestMutation.isPending && results.length === 0 && !error && hasUploadedData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Backpack sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">Henüz backtest yapılmadı</Typography>
            <Typography variant="body2" color="text.secondary">"Testi Başlat" butonuna tıklayın.</Typography>
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
                        <TableCell align="center">
                          <Chip label={`${total}`} size="small" color="primary" />
                        </TableCell>
                        <TableCell align="center">
                          <Chip label="Başarılı" size="small" color="success" />
                        </TableCell>
                        <TableCell align="center">
                          <Button size="small" variant="outlined" startIcon={<Visibility />} onClick={() => handleViewHistory(item)}>
                            Görüntüle
                          </Button>
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