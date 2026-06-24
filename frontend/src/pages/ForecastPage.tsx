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
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Slider,
  TextField,
} from '@mui/material';
import {
  ShowChart,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Info,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface ForecastResult {
  material_code: string;
  group: string;
  horizon: number;
  selected_model: string;
  best_model_label: string;
  model_description: string;
  selection_reason: string;
  forecast: number[];
  lower_80: number[];
  upper_80: number[];
  lower_95: number[];
  upper_95: number[];
  trend_direction: string;
  trend_percent: number;
  model_rmse: number | null;
  model_comparison: Record<string, any>;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function ForecastPage() {
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [results, setResults] = useState<ForecastResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [horizon, setHorizon] = useState(4);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState<ForecastResult | null>(null);

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

  const forecastMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/forecast/batch', {
        horizon: horizon,
        model_type: selectedModel
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
      console.error('❌ Forecast hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'forecast_batch' }
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
      const response = await api.post('/api/export/forecast-results', {
        results: results,
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const modelColors: Record<string, string> = {
    holt_winters: '#9c27b0',
    arima: '#1976d2',
    simple: '#2e7d32',
    auto: '#ed6c02'
  };

  const modelLabels: Record<string, string> = {
    holt_winters: 'Holt-Winters',
    arima: 'ARIMA',
    simple: 'Basit MA',
    auto: 'Otomatik'
  };

  const handleCompare = (result: ForecastResult) => {
    setSelectedMaterial(result);
    setShowComparison(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            📈 Talep Tahmini (Forecast)
          </Typography>
          <Typography variant="body1" color="text.secondary">
            4 farklı model ile talep tahmini yapar.
            <Chip label="8 Token" size="small" color="warning" sx={{ ml: 1 }} />
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
            startIcon={forecastMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => forecastMutation.mutate()}
            disabled={forecastMutation.isPending || !hasUploadedData}
          >
            {forecastMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.</Alert>
      )}

      {/* 📌 Parametre Kartı */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Model Seçimi</InputLabel>
                <Select
                  value={selectedModel}
                  label="Model Seçimi"
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="auto">🔄 Otomatik Seçim (Önerilen)</MenuItem>
                  <MenuItem value="holt_winters">📊 Holt-Winters (Mevsimsel)</MenuItem>
                  <MenuItem value="arima">📈 ARIMA (Otoregresif)</MenuItem>
                  <MenuItem value="simple">📉 Basit (MA+Trend)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="body2" gutterBottom>
                Tahmin Ufku: {horizon} Hafta
              </Typography>
              <Slider
                value={horizon}
                onChange={(_, val) => setHorizon(val as number)}
                min={4}
                max={52}
                step={1}
                marks={[
                  { value: 4, label: '4' },
                  { value: 12, label: '12' },
                  { value: 26, label: '26' },
                  { value: 52, label: '52' },
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="caption" color="text.secondary">
                {selectedModel === 'auto' && 'Veriye göre en uygun modeli otomatik seçer.'}
                {selectedModel === 'holt_winters' && 'Mevsimsel desenler için, 52+ hafta veri önerilir.'}
                {selectedModel === 'arima' && 'Trend ve otokorelasyon için, 26+ hafta veri önerilir.'}
                {selectedModel === 'simple' && 'Hızlı ve basit, az veri için idealdir.'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Model Bilgilendirme Kartı */}
      <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              📊 Tahmin Modelleri
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Holt-Winters" size="small" sx={{ bgcolor: '#9c27b0', color: 'white' }} />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>Mevsimsel talep için</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="ARIMA" size="small" sx={{ bgcolor: '#1976d2', color: 'white' }} />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>Otoregresif, 26+ hafta</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Basit MA" size="small" sx={{ bgcolor: '#2e7d32', color: 'white' }} />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>Hızlı, son 4 hafta</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Chip label="Otomatik" size="small" sx={{ bgcolor: '#ed6c02', color: 'white' }} />
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>En uygun modeli seçer</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına 8 token harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {forecastMutation.isPending && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {horizon} haftalık tahmin yapılıyor...
          </Typography>
        </Box>
      )}

      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Sonuçlar ({results.length} malzeme)
              </Typography>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Malzeme Kodu</TableCell>
                    <TableCell sx={{ color: 'white' }}>Grup</TableCell>
                    <TableCell sx={{ color: 'white' }}>Seçilen Model</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Trend</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">H1</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">H{Math.min(horizon, 4)}</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Karşılaştır</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>{result.material_code}</TableCell>
                      <TableCell>{result.group}</TableCell>
                      <TableCell>
                        <Tooltip title={`RMSE: ${result.model_rmse?.toFixed(2) || '-'}`} arrow>
                          <Chip 
                            label={result.best_model_label}
                            size="small"
                            sx={{ 
                              bgcolor: modelColors[result.selected_model] || '#1976d2',
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          icon={result.trend_direction === 'Artış' ? <TrendingUp /> : <TrendingDown />}
                          label={`${result.trend_percent > 0 ? '+' : ''}${result.trend_percent}%`}
                          size="small"
                          color={result.trend_direction === 'Artış' ? 'error' : 'success'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center" sx={{ fontWeight: 'bold' }}>
                        {result.forecast[0]?.toFixed(0) || '-'}
                      </TableCell>
                      <TableCell align="center" sx={{ fontWeight: 'bold' }}>
                        {result.forecast[Math.min(horizon, 4) - 1]?.toFixed(0) || '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleCompare(result)}
                        >
                          Karşılaştır
                        </Button>
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

            {/* Özet */}
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="caption" color="text.secondary">En Çok Seçilen</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(() => {
                        const counts: Record<string, number> = {};
                        results.forEach(r => {
                          counts[r.selected_model] = (counts[r.selected_model] || 0) + 1;
                        });
                        const entries = Object.entries(counts);
                        if (entries.length === 0) return '-';
                        return modelLabels[entries.sort((a, b) => b[1] - a[1])[0][0]] || '-';
                      })()}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama RMSE</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + (r.model_rmse || 0), 0) / results.length).toFixed(2)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                    <Typography variant="caption" color="text.secondary">Artış Trendi</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {results.filter(r => r.trend_direction === 'Artış').length}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                    <Typography variant="caption" color="text.secondary">Azalış Trendi</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {results.filter(r => r.trend_direction === 'Azalış').length}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* 📊 Model Karşılaştırma Dialog */}
      <Dialog open={showComparison} onClose={() => setShowComparison(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📊 Model Karşılaştırması</Typography>
            <IconButton onClick={() => setShowComparison(false)}><Close /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedMaterial && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 2 }}>
                Malzeme: {selectedMaterial.material_code} - {selectedMaterial.group}
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white' }}>Model</TableCell>
                      <TableCell sx={{ color: 'white' }} align="right">RMSE (MAPE)</TableCell>
                      <TableCell sx={{ color: 'white' }} align="center">1.Hafta</TableCell>
                      <TableCell sx={{ color: 'white' }} align="center">Son Hafta</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(selectedMaterial.model_comparison || {}).map(([modelName, data]: [string, any]) => (
                      <TableRow key={modelName} sx={{ bgcolor: modelName === selectedMaterial.selected_model ? 'success.light' : 'inherit' }}>
                        <TableCell>
                          {modelLabels[modelName] || modelName}
                          {modelName === selectedMaterial.selected_model && (
                            <Chip label="Seçili" size="small" color="success" sx={{ ml: 1 }} />
                          )}
                        </TableCell>
                        <TableCell align="right">{data.rmse?.toFixed(2) || '-'}</TableCell>
                        <TableCell align="center">{data.forecast?.[0]?.toFixed(0) || '-'}</TableCell>
                        <TableCell align="center">{data.forecast?.[data.forecast.length - 1]?.toFixed(0) || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="body2" color="info.dark">
                  <strong>📌 Seçim Nedeni:</strong> {selectedMaterial.selection_reason}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowComparison(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>

      {!forecastMutation.isPending && results.length === 0 && !error && hasUploadedData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <ShowChart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">Henüz analiz yapılmadı</Typography>
            <Typography variant="body2" color="text.secondary">"Analiz Et" butonuna tıklayarak tahmin analizini başlatın.</Typography>
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