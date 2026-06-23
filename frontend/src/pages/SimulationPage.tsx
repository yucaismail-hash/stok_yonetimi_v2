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
  Switch,
  FormControlLabel,
  TextField,
  Stack,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Timeline,
  Send,
  Download,
  History,
  Close,
  Visibility,
  Tune,
  Info,
  Speed,
  TrendingUp,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface SimulationResult {
  material_code: string;
  group: string;
  service_level: number;
  cvar_95: number;
  tail_risk: number;
  tail_risk_level: string;
  cvar_risk: string;
  service_gap: number;
  stockout_probability: number;
  avg_stock: number;
  regime_used: boolean;
  copula_used: boolean;
  adaptive_ss_used: boolean;
  recommendations: string[];
  current_rop: number;
  recommended_rop: number;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function SimulationPage() {
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isSimulating, setIsSimulating] = useState(false);

  const [config, setConfig] = useState({
    n_simulations: 500,
    weeks: 26,
    use_regime: false,
    use_copula: false,
    use_adaptive_ss: false,
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

  const simulationMutation = useMutation({
    mutationFn: async () => {
      setProgress(10);
      setProgressLabel('Simülasyon başlatılıyor...');
      const res = await api.post('/api/simulate/batch', config);
      setProgress(100);
      setProgressLabel('Tamamlandı!');
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0);
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla simüle edildi.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.error || 'Simülasyon başarısız');
      }
      setTimeout(() => {
        setProgress(0);
        setProgressLabel('Hazır');
      }, 2000);
    },
    onError: (err: any) => {
      console.error('❌ Simülasyon hatası:', err);
      setError(err.response?.data?.detail || 'Simülasyon sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'simulation_batch' }
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
      const response = await api.post('/api/export/simulation-results', {
        results: results,
        config: config
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `simulasyon_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const modelInfo = {
    use_regime: {
      label: 'Rejim Modeli',
      description: 'Talebi düşük/yüksek rejimlere ayırarak daha gerçekçi simülasyon sağlar. 24+ hafta veri gerektirir.',
      icon: <TrendingUp fontSize="small" />
    },
    use_copula: {
      label: 'Copula Modeli',
      description: 'Talep ile lead time arasında korelasyon kurar. Gerçek dünya bağımlılığını yansıtır.',
      icon: <AnalyticsIcon fontSize="small" />
    },
    use_adaptive_ss: {
      label: 'Adaptif SS',
      description: 'Simülasyon içinde ROP\'u hedef servis seviyesine göre dinamik olarak günceller.',
      icon: <Speed fontSize="small" />
    }
  };

  const getServiceLevelColor = (value: number) => {
    if (value >= 95) return 'success.main';
    if (value >= 90) return 'warning.main';
    return 'error.main';
  };

  const getRiskColor = (value: number) => {
    if (value <= 5) return 'success.main';
    if (value <= 10) return 'warning.main';
    return 'error.main';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            🎲 Monte Carlo Simülasyonu
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Binlerce senaryo ile stok performansınızı simüle edin.
            <Chip label="20 Token" size="small" color="warning" sx={{ ml: 1 }} />
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<History />} onClick={fetchHistory} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Geçmiş'}
          </Button>
          <Button
            variant="contained"
            startIcon={simulationMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => simulationMutation.mutate()}
            disabled={simulationMutation.isPending || !hasUploadedData}
          >
            {simulationMutation.isPending ? 'Simüle Ediliyor...' : 'Simülasyonu Başlat'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.</Alert>
      )}

      {/* Bilgilendirme Kartı */}
      <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Info color="info" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              💡 Simülasyon Kullanım İpuçları
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                ⚙️ Simülasyon Sayısı
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                500: Hızlı test <br />
                1000+: Detaylı analiz <br />
                <strong>Uyarı:</strong> Sayı arttıkça süre uzar!
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                📊 Rejim Modeli
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                Talebi düşük/yüksek rejimlere ayırır. <br />
                <strong>Gereksinim:</strong> 24+ hafta veri
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                🔗 Copula Modeli
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                Talep-Lead time korelasyonu. <br />
                <strong>Etki:</strong> Daha gerçekçi senaryolar
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                🔄 Adaptif SS
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                ROP'u hedef servise göre günceller. <br />
                <strong>Avantaj:</strong> Dinamik optimizasyon
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Parametreler Kartı */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Tune color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Simülasyon Parametreleri</Typography>
          </Box>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <TextField
                fullWidth
                type="number"
                label="Simülasyon Sayısı"
                value={config.n_simulations}
                onChange={(e) => setConfig({ ...config, n_simulations: Number(e.target.value) })}
                slotProps={{ 
                  htmlInput: { min: 100, max: 5000, step: 100 },
                  input: { endAdornment: <Typography variant="caption">(100-5000)</Typography> }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <TextField
                fullWidth
                type="number"
                label="Hafta Sayısı"
                value={config.weeks}
                onChange={(e) => setConfig({ ...config, weeks: Number(e.target.value) })}
                slotProps={{ 
                  htmlInput: { min: 4, max: 52, step: 1 },
                  input: { endAdornment: <Typography variant="caption">(4-52)</Typography> }
                }}
              />
            </Grid>
            
            {Object.entries(modelInfo).map(([key, info]) => (
              <Grid size={{ xs: 12, sm: 6, md: 2 }} key={key}>
                <Tooltip title={info.description} arrow placement="top">
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config[key as keyof typeof config] as boolean}
                        onChange={(e) => setConfig({ ...config, [key]: e.target.checked })}
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {info.icon}
                        <Typography variant="body2">{info.label}</Typography>
                        {key === 'use_regime' && (
                          <Chip label="24+" size="small" variant="outlined" sx={{ height: 16, fontSize: '0.6rem' }} />
                        )}
                      </Box>
                    }
                  />
                </Tooltip>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Token Bakiyesi */}
      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong></Typography>
            <Typography variant="caption" color="text.secondary">Analiz başına 20 token harcanır</Typography>
          </Box>
        </CardContent>
      </Card>

      {/* İlerleme Durumu */}
      {simulationMutation.isPending && (
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
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {config.n_simulations} senaryo simüle ediliyor...
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
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Servis %
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      CVaR95
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Tail Risk
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                      Stok Tük. %
                    </TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                      Modeller
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
                      <TableCell 
                        align="right" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: getServiceLevelColor(result.service_level)
                        }}
                      >
                        {result.service_level}%
                      </TableCell>
                      <TableCell align="right">
                        {result.cvar_95}
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
                      <TableCell 
                        align="right"
                        sx={{ 
                          color: getRiskColor(result.stockout_probability),
                          fontWeight: 'bold'
                        }}
                      >
                        {result.stockout_probability}%
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={0.5} sx={{ justifyContent: 'center' }}>
                          {result.regime_used && (
                            <Tooltip title="Rejim aktif">
                              <Chip label="R" size="small" color="info" sx={{ minWidth: 20, height: 20 }} />
                            </Tooltip>
                          )}
                          {result.copula_used && (
                            <Tooltip title="Copula aktif">
                              <Chip label="C" size="small" color="secondary" sx={{ minWidth: 20, height: 20 }} />
                            </Tooltip>
                          )}
                          {result.adaptive_ss_used && (
                            <Tooltip title="Adaptif SS aktif">
                              <Chip label="A" size="small" color="warning" sx={{ minWidth: 20, height: 20 }} />
                            </Tooltip>
                          )}
                          {!result.regime_used && !result.copula_used && !result.adaptive_ss_used && (
                            <Chip label="-" size="small" variant="outlined" sx={{ minWidth: 20, height: 20 }} />
                          )}
                        </Stack>
                      </TableCell>
                      <TableCell>
                        {result.recommendations && result.recommendations.length > 0 ? (
                          <Tooltip title={result.recommendations[0]} arrow>
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
                              {result.recommendations[0].substring(0, 40)}
                              {result.recommendations[0].length > 40 ? '...' : ''}
                            </Typography>
                          </Tooltip>
                        ) : '-'}
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
                      {(results.reduce((acc, r) => acc + r.service_level, 0) / results.length).toFixed(1)}%
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama CVaR95</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + r.cvar_95, 0) / results.length).toFixed(1)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="caption" color="text.secondary">Ortalama Tail Risk</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(results.reduce((acc, r) => acc + (r.tail_risk || 0), 0) / results.length).toFixed(2)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                    <Typography variant="caption" color="text.secondary">Aktif Model</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {(() => {
                        const parts = [];
                        if (results.filter(r => r.regime_used).length > 0) {
                          parts.push(`${results.filter(r => r.regime_used).length} R`);
                        }
                        if (results.filter(r => r.copula_used).length > 0) {
                          parts.push(`${results.filter(r => r.copula_used).length} C`);
                        }
                        if (results.filter(r => r.adaptive_ss_used).length > 0) {
                          parts.push(`${results.filter(r => r.adaptive_ss_used).length} A`);
                        }
                        return parts.length > 0 ? parts.join(' ') : '-';
                      })()}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </CardContent>
        </Card>
      )}

      {!simulationMutation.isPending && results.length === 0 && !error && hasUploadedData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">Henüz simülasyon yapılmadı</Typography>
            <Typography variant="body2" color="text.secondary">"Simülasyonu Başlat" butonuna tıklayın.</Typography>
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