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
} from '@mui/material';
import {
  Analytics,
  Send,
  Download,
  History,
  Close,
  Visibility,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface PatternResult {
  material_code: string;
  group: string;
  pattern: string;
  cv: number;
  zero_ratio: number;
  trend: number;
  mean: number;
  std: number;
  median: number;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function PatternPage() {
  const { user } = useAuth();
  const [hasUploadedData, setHasUploadedData] = useState(false);
  const [results, setResults] = useState<PatternResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 📌 Sayfalama state'leri
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  // ✅ Özet Dialog için state'ler
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<HistoryItem | null>(null);

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

  const patternMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/pattern/batch');
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setResults(data.results || []);
        setPage(0); // ✅ Yeni sonuçlarda ilk sayfaya dön
        setError(null);
        setSuccess(`${data.total || data.results?.length || 0} malzeme başarıyla analiz edildi.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.error || 'Analiz başarısız');
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
    },
  });

  // ✅ Geçmiş sonuçları getir (Özetlenmiş - Tek satır)
  // ✅ Geçmiş sonuçları getir (Tarih+Saat bazında 1 satır)
  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { result_type: 'pattern_batch' }
      });
      console.log('📋 Geçmiş cevabı:', res.data);
      
      if (res.data.success) {
        const rawResults = res.data.results || [];
        
        // 📌 Tarih+Saat bazında grupla (dakika hassasiyetinde)
        const groupedMap = new Map();
        
        rawResults.forEach((item: any) => {
          const date = item.created_at ? new Date(item.created_at) : new Date();
          // Tarih+Saat (dakika bazında) key oluştur
          const key = date.toISOString().slice(0, 16); // "2026-06-22T13:28"
          
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
        
        // ✅ Group'ları diziye çevir
        const groupedResults = Array.from(groupedMap.values()).map(group => {
          // İlk kaydın verilerini al (tüm kayıtlar aynı veriyi içerir)
          const firstItem = group.items[0];
          const resultData = firstItem.data || firstItem.result_data || {};
          let allResults = [];
          
          if (resultData.results && Array.isArray(resultData.results)) {
            allResults = resultData.results;
          } else if (resultData.material_code) {
            allResults = [resultData];
          }
          
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


  // ✅ Geçmiş sonucu görüntüle (Ana tabloya aktar)
  // ✅ Geçmiş sonucu görüntüle (Seçilen tarih/saatteki verileri ana tabloya aktar)
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

  // ✅ Sayfalama işlevleri
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // ✅ Mevcut sayfadaki veriler
  const paginatedResults = results.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const handleExport = async () => {
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }

    try {
      const response = await api.post('/api/export/pattern-results', {
        results: results,
      }, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `pattern_analiz_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const handleExportHistory = async () => {
    if (!selectedHistory) return;
    
    const results = selectedHistory.data?.results || [];
    if (results.length === 0) {
      setError('Aktarılacak sonuç yok!');
      return;
    }

    try {
      const response = await api.post('/api/export/pattern-results', {
        results: results,
      }, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `pattern_analiz_${new Date().toISOString().slice(0,10)}.xlsx`);
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

  const getPatternColor = (pattern: string) => {
    switch (pattern) {
      case 'DUZENLI_SABIT': return 'success';
      case 'DUZENLI_ARTS': return 'info';
      case 'DUZENLI_AZALIS': return 'warning';
      case 'DEGISKEN': return 'primary';
      case 'YUKSEK_DEGISKEN': return 'secondary';
      case 'ASIRI_DEGISKEN': return 'error';
      case 'SIFIR_TALEP': return 'error';
      case 'ARALIKLI_DUSUK': return 'info';
      case 'ARALIKLI_YUKSEK': return 'warning';
      default: return 'default';
    }
  };

  const getPatternLabel = (pattern: string) => {
    const labels: Record<string, string> = {
      'DUZENLI_SABIT': 'Düzenli Sabit',
      'DUZENLI_ARTS': 'Düzenli Artan',
      'DUZENLI_AZALIS': 'Düzenli Azalan',
      'DEGISKEN': 'Değişken',
      'YUKSEK_DEGISKEN': 'Yüksek Değişken',
      'ASIRI_DEGISKEN': 'Aşırı Değişken',
      'SIFIR_TALEP': 'Sıfır Talep',
      'ARALIKLI_DUSUK': 'Aralıklı Düşük',
      'ARALIKLI_YUKSEK': 'Aralıklı Yüksek',
    };
    return labels[pattern] || pattern;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            📊 Pattern Analizi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Yüklenen tüm malzemelerin talep pattern'lerini analiz eder.
            <Chip 
              label="5 Token" 
              size="small" 
              color="warning" 
              sx={{ ml: 1 }} 
            />
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<History />}
            onClick={fetchHistory}
            disabled={loading}
          >
            {loading ? 'Yükleniyor...' : 'Geçmiş'}
          </Button>
          {results.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExport}
            >
              Excel'e Aktar
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={patternMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => patternMutation.mutate()}
            disabled={patternMutation.isPending || !hasUploadedData}
          >
            {patternMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      
      {!hasUploadedData && !results.length && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Henüz Excel dosyası yüklenmemiş. Lütfen önce Dashboard'dan dosya yükleyin.
        </Alert>
      )}

      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">
              💰 Token Bakiyesi: <strong>{user?.token_balance || 0}</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Analiz başına 5 token harcanır
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {patternMutation.isPending && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Malzemeler analiz ediliyor...
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
                    <TableCell sx={{ color: 'white' }}>Pattern</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">CV</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Zero Ratio</TableCell>
                    <TableCell sx={{ color: 'white' }} align="right">Trend</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedResults.map((result, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{result.material_code}</TableCell>
                      <TableCell>{result.group}</TableCell>
                      <TableCell>
                        <Chip
                          label={getPatternLabel(result.pattern)}
                          size="small"
                          color={getPatternColor(result.pattern)}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">{result.cv.toFixed(4)}</TableCell>
                      <TableCell align="right">{result.zero_ratio.toFixed(4)}</TableCell>
                      <TableCell align="right" sx={{ color: result.trend >= 0 ? 'success.main' : 'error.main' }}>
                        {result.trend.toFixed(2)}%
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

      {!patternMutation.isPending && results.length === 0 && !error && hasUploadedData && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Henüz analiz yapılmadı
            </Typography>
            <Typography variant="body2" color="text.secondary">
              "Analiz Et" butonuna tıklayarak pattern analizini başlatın.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* 📋 Geçmiş Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📋 Geçmiş Analiz Sonuçları</Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)}>
              <Close />
            </IconButton>
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
                    const totalMaterials = item.data?.total || 0;
                    const createdAt = item.created_at ? new Date(item.created_at) : new Date();
                    
                    return (
                      <TableRow key={item.id}>
                        <TableCell>
                          {createdAt.toLocaleDateString('tr-TR')} {createdAt.toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'})}
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={`${totalMaterials}`} size="small" color="primary" />
                        </TableCell>
                        <TableCell align="center">
                          <Chip label="Başarılı" size="small" color="success" />
                        </TableCell>
                        <TableCell align="center">
                          <Button 
                            size="small" 
                            variant="outlined"
                            startIcon={<Visibility />}
                            onClick={() => handleViewHistory(item)}
                          >
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
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>

      {/* 📊 Geçmiş Özet Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">📊 Analiz Özeti</Typography>
            <IconButton onClick={() => setViewDialogOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedHistory ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                    <Typography variant="caption">Toplam Malzeme</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                      {selectedHistory.data?.total || 0}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                    <Typography variant="caption">Başarılı</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                      {selectedHistory.data?.results?.filter((r: any) => r.pattern !== 'SIFIR_TALEP').length || 0}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
                    <Typography variant="caption">Sıfır Talep</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                      {selectedHistory.data?.results?.filter((r: any) => r.pattern === 'SIFIR_TALEP').length || 0}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                    <Typography variant="caption">Tarih</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {selectedHistory.created_at ? new Date(selectedHistory.created_at).toLocaleDateString('tr-TR') : '-'}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              <Divider sx={{ mb: 2 }} />

              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                Pattern Dağılımı
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {selectedHistory.data?.results?.reduce((acc: any, r: any) => {
                  acc[r.pattern] = (acc[r.pattern] || 0) + 1;
                  return acc;
                }, {}) && Object.entries(
                  selectedHistory.data?.results?.reduce((acc: any, r: any) => {
                    acc[r.pattern] = (acc[r.pattern] || 0) + 1;
                    return acc;
                  }, {}) || {}
                ).map(([pattern, count]: [string, any]) => (
                  <Chip
                    key={pattern}
                    label={`${getPatternLabel(pattern)}: ${count}`}
                    size="small"
                    color={getPatternColor(pattern)}
                    variant="outlined"
                  />
                ))}
              </Box>

              <Divider sx={{ mb: 2 }} />

              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                Malzeme Listesi
              </Typography>
              <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.100' }}>
                      <TableCell>Malzeme Kodu</TableCell>
                      <TableCell>Pattern</TableCell>
                      <TableCell align="right">CV</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(selectedHistory.data?.results || []).map((result: any, idx: number) => (
                      <TableRow key={idx}>
                        <TableCell>{result.material_code}</TableCell>
                        <TableCell>
                          <Chip
                            label={getPatternLabel(result.pattern)}
                            size="small"
                            color={getPatternColor(result.pattern)}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">{result.cv?.toFixed(4) || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            variant="contained" 
            startIcon={<Download />}
            onClick={handleExportHistory}
          >
            Excel'e Aktar
          </Button>
          <Button onClick={() => setViewDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}