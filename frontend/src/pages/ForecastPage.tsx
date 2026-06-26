import { useState, useEffect, useRef } from 'react';
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
  LinearProgress,
  Snackbar,
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
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
} from 'recharts';

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
  model_params: Record<string, any>;
  outlier_info: { has_outliers: boolean; outlier_count: number; outliers: any[] };
  historical_data?: number[];
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
}

export default function ForecastPage() {
  const { user, fetchUser } = useAuth();
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

  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('Hazır');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeAsyncTask, setActiveAsyncTask] = useState<string | null>(null);
  
  // Snackbar için
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  
  // 📌 interval ID'sini saklamak için ref
  const intervalIdRef = useRef<number | null>(null);
  
  const queryClient = useQueryClient();
  
  // ✅ Token maliyetini veritabanından çek
  const { data: costData } = useQuery({
    queryKey: ['forecast-cost'],
    queryFn: async () => {
      const res = await api.get('/api/cost', {
        params: {
          endpoint: '/api/forecast/batch',
          method: 'POST'
        }
      });
      return res.data;
    },
    initialData: { cost: 8 }
  });

  // ✅ Sadece bir kere kontrol et (sonsuz döngüyü önle)
  useEffect(() => {
    checkUploadedData();
    
    // Component unmount olduğunda interval'i temizle
    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, []);

  const checkUploadedData = async () => {
    try {
      const res = await api.get('/api/upload/status');
      console.log('📦 Upload status:', res.data);
      setHasUploadedData(res.data.has_data === true);
    } catch (error) {
      console.error('❌ Veri kontrolü hatası:', error);
      setHasUploadedData(false);
    }
  };

  // 📌 Normal Forecast Mutation
  const forecastMutation = useMutation({
    mutationFn: async () => {
      setProgress(0);
      setProgressLabel('Analiz başlatılıyor...');
      setIsProcessing(true);

      const res = await api.post('/api/forecast/batch', {
        horizon: horizon,
        model_type: selectedModel,
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
      console.error('❌ Forecast hatası:', err);
      setError(err.response?.data?.detail || 'Analiz sırasında hata oluştu');
      setProgress(0);
      setProgressLabel('Hata!');
      setIsProcessing(false);
    },
  });

  // 📌 Async İlerleme Kontrol Fonksiyonu
  const checkAsyncProgress = async (taskId: string) => {
    if (!taskId) return;
    
    try {
      const res = await api.get(`/api/forecast/async/status/${taskId}`);
      const status = res.data;
      
      console.log(`📊 Async durum: ${status.status}, İlerleme: ${status.progress}%`);
      
      setProgress(status.progress || 50);
      setProgressLabel(status.message || 'İşleniyor...');
      
      if (status.status === 'completed') {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
        
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(100);
        setProgressLabel('Tamamlandı!');
        
        try {
          const resultsRes = await api.get(`/api/forecast/async/result/${taskId}`);
          if (resultsRes.data.success) {
            setResults(resultsRes.data.results || []);
            setPage(0);
            const count = resultsRes.data.total || resultsRes.data.results?.length || 0;
            setSuccess(`${count} malzeme başarıyla analiz edildi.`);
            setTimeout(() => setSuccess(null), 5000);
            await fetchUser();
          }
        } catch (err) {
          console.error('❌ Sonuç getirme hatası:', err);
          setError('Sonuçlar alınamadı');
        }
        return;
      }
      
      if (status.status === 'failed' || status.status === 'error') {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
        
        setIsProcessing(false);
        setActiveAsyncTask(null);
        setProgress(0);
        setProgressLabel('Hata!');
        setError(status.message || 'Async analiz başarısız oldu');
        return;
      }
      
    } catch (error) {
      console.error('Async durum kontrol hatası:', error);
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      setIsProcessing(false);
      setActiveAsyncTask(null);
      setError('Async durum kontrolü başarısız');
    }
  };

  // 📌 Async Batch Forecast Mutation
  const asyncForecastMutation = useMutation({
    mutationFn: async () => {
      setProgress(5);
      setProgressLabel('Async analiz başlatılıyor...');
      setIsProcessing(true);

      const res = await api.post('/api/forecast/batch/async', {
        horizon: horizon,
        model_type: selectedModel,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setActiveAsyncTask(data.task_id);
      
      // ✅ Snackbar mesajı göster
      setSnackbar({
        open: true,
        message: `✅ Rapor talebiniz başarıyla oluşturuldu. İşlem numarası: #${data.task_id.slice(0,8)}
📋 ASYNC Görevler sayfasından ilerlemenizi takip edebilirsiniz.`,
        severity: 'success',
      });
      
      setProgress(10);
      setProgressLabel('İşlem kuyruğa alındı.');
      
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      
      intervalIdRef.current = setInterval(() => {
        checkAsyncProgress(data.task_id);
      }, 3000);
      
      setTimeout(() => {
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
          if (isProcessing) {
            setIsProcessing(false);
            setActiveAsyncTask(null);
            setError('Analiz zaman aşımına uğradı. Lütfen tekrar deneyin.');
          }
        }
      }, 300000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Async analiz başlatılamadı');
      setIsProcessing(false);
      setProgress(0);
      setProgressLabel('Hata!');
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    },
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/upload/results', {
        params: { 
          result_type: 'forecast_batch',
          limit: 100
        },
      });

      if (res.data.success) {
        const rawResults = res.data.results || [];
        console.log(`📊 ${rawResults.length} sonuç bulundu`);
        
        const groupedMap = new Map();
        
        rawResults.forEach((item: any) => {
          const date = item.created_at ? new Date(item.created_at) : new Date();
          const key = date.toISOString().slice(0, 16);

          if (!groupedMap.has(key)) {
            groupedMap.set(key, {
              id: item.id,
              created_at: item.created_at,
              items: [],
            });
          }
          groupedMap.get(key).items.push(item);
        });

        const groupedResults = Array.from(groupedMap.values()).map((group) => {
          const allResults = group.items
            .map((item: any) => {
              const resultData = item.data || {};
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
              results: allResults,
            },
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
      link.setAttribute('download', `forecast_${new Date().toISOString().slice(0, 10)}.xlsx`);
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
    auto: '#ed6c02',
  };

  const modelLabels: Record<string, string> = {
    holt_winters: 'Holt-Winters',
    arima: 'ARIMA',
    simple: 'Basit MA',
    auto: 'Otomatik',
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

  const getMapeStatus = (mape: number) => {
    if (mape < 20) return { color: 'success', label: '✅ Mükemmel', description: 'Stok yönetimi için ideal' };
    if (mape < 30) return { color: 'info', label: '📈 İyi', description: 'Kabul edilebilir' };
    if (mape < 50) return { color: 'warning', label: '⚠️ Orta', description: 'İyileştirilmeli' };
    if (mape < 100) return { color: 'error', label: '🔴 Zayıf', description: 'Tahmin modeli gözden geçirilmeli' };
    return { color: 'error', label: '🚨 Çok Zayıf', description: 'Veri kalitesi veya model seçimi hatalı' };
  };

  const handleCompare = (result: ForecastResult) => {
    setSelectedMaterial(result);
    setShowComparison(true);
  };

  const prepareChartData = (result: ForecastResult) => {
    const historical = result.historical_data || [];
    const forecast = result.forecast || [];
    const lower_80 = result.lower_80 || [];
    const upper_80 = result.upper_80 || [];

    const data: any[] = [];

    historical.forEach((val, idx) => {
      data.push({
        week: idx + 1,
        historical: val,
        forecast: null,
        lower_80: null,
        upper_80: null,
      });
    });

    forecast.forEach((val, idx) => {
      const weekIndex = historical.length + idx + 1;
      data.push({
        week: weekIndex,
        historical: null,
        forecast: val,
        lower_80: lower_80[idx] || null,
        upper_80: upper_80[idx] || null,
      });
    });

    return data;
  };

  const ForecastChart = ({ result }: { result: ForecastResult }) => {
    const data: any[] = prepareChartData(result);

    return (
      <Box sx={{ width: '100%', height: 300, mt: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
          📈 Tahmin Grafiği
        </Typography>
        <ResponsiveContainer>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" label={{ value: 'Hafta', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Talep', angle: -90, position: 'insideLeft' }} />
            <RechartsTooltip />
            <Legend />

            <Area
              type="monotone"
              dataKey="upper_80"
              stroke="none"
              fill="#8884d8"
              fillOpacity={0.2}
              name="%80 Güven Aralığı"
            />
            <Area type="monotone" dataKey="lower_80" stroke="none" fill="#8884d8" fillOpacity={0.2} />

            <Line
              type="monotone"
              dataKey="historical"
              stroke="#1976d2"
              strokeWidth={2}
              dot={{ r: 3 }}
              name="Geçmiş Talep"
              connectNulls={false}
            />

            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#ed6c02"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4 }}
              name="Tahmin"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  // 📌 ModelParams Bileşeni - Pattern Bilgileriyle Zenginleştirilmiş
  const ModelParams = ({ result }: { result: ForecastResult }) => {
    const params = result.model_params;
    if (!params || Object.keys(params).length === 0) {
      return (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          <strong>Parametreler:</strong> Detay mevcut değil.
        </Typography>
      );
    }
    
    let paramText = '';
    let paramDetails: { key: string; value: any }[] = [];

    // ✅ Pattern bilgilerini ekle
    if (params.pattern) {
      paramDetails.push({
        key: '📊 Talep Patterni',
        value: (
          <Chip
            label={params.pattern_label || params.pattern}
            size="small"
            color={getPatternColor(params.pattern_color)}
            variant="outlined"
          />
        )
      });
      
      if (params.cv !== undefined) {
        paramDetails.push({ key: 'Değişkenlik (CV)', value: params.cv });
      }
      if (params.zero_ratio !== undefined) {
        paramDetails.push({ key: 'Sıfır Talep Oranı', value: params.zero_ratio });
      }
    }

    // Model bazında parametreler
    if (result.selected_model === 'holt_winters') {
      paramText = `Mevsimsellik: ${params.seasonal_periods || '52'} hafta`;
      paramDetails.push(
        { key: 'Mevsimsellik Periyodu', value: `${params.seasonal_periods || '52'} hafta` },
        { key: 'Trend', value: params.trend || 'Toplanabilir (add)' },
        { key: 'Mevsimsellik', value: params.seasonal || 'Toplanabilir (add)' }
      );
      if (params.damping_trend !== undefined) {
        paramDetails.push({ key: 'Trend Sönümleme', value: params.damping_trend ? 'Aktif' : 'Pasif' });
      }
    } else if (result.selected_model === 'arima') {
      const order = params.order || '(1,1,1)';
      paramText = `Order: ${order}`;
      paramDetails.push(
        { key: 'ARIMA Order (p,d,q)', value: order },
        { key: 'Mevsimsellik', value: params.seasonal_order ? `${params.seasonal_order}` : 'Yok' }
      );
      if (params.trend !== undefined) {
        paramDetails.push({ key: 'Trend', value: params.trend ? 'Evet' : 'Hayır' });
      }
    } else if (result.selected_model === 'simple') {
      paramText = `Pencere: ${params.window || 4} hafta`;
      paramDetails.push(
        { key: 'Hareketli Ortalama Penceresi', value: `${params.window || 4} hafta` },
        { key: 'Ağırlıklandırma', value: params.weighted ? 'Evet (Ağırlıklı)' : 'Hayır (Eşit)' }
      );
    } else if (result.selected_model === 'auto') {
      paramText = `Seçim Yöntemi: ${params.selection_method || 'MAPE'}`;
      paramDetails.push(
        { key: 'Seçim Kriteri', value: params.selection_method || 'MAPE' },
        { key: 'Test Edilen Model Sayısı', value: params.models_tested || 0 },
        { key: 'En İyi Model', value: params.best_model || 'Belirlenemedi' }
      );
      if (params.best_mape) {
        paramDetails.push({ key: 'En Düşük MAPE', value: `${params.best_mape}%` });
      }
    }

    // Seçim bilgisi
    if (params.selection_reason) {
      paramDetails.push({ key: 'Seçim Nedeni', value: params.selection_reason });
    }

    return (
      <Box sx={{ mt: 0.5, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: 'bold' }}>
          ⚙️ Model Parametreleri:
        </Typography>
        {paramDetails.length > 0 ? (
          <Table size="small" sx={{ '& .MuiTableCell-root': { border: 'none', py: 0.5, px: 1 } }}>
            <TableBody>
              {paramDetails.map((detail) => (
                <TableRow key={detail.key}>
                  <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '40%' }}>
                    {detail.key}
                  </TableCell>
                  <TableCell>{String(detail.value)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Typography variant="caption" color="text.secondary">
            {paramText || 'Parametre bilgisi bulunamadı.'}
          </Typography>
        )}
      </Box>
    );
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
            📈 Talep Tahmini (Forecast)
          </Typography>
          <Typography variant="body1" color="text.secondary">
            4 farklı model ile talep tahmini yapar. Pattern analizi ile zenginleştirilmiştir.
            <Chip 
              label={`${costData?.cost || 8} Token`} 
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
            startIcon={forecastMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => forecastMutation.mutate()}
            disabled={forecastMutation.isPending || !hasUploadedData}
          >
            {forecastMutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={asyncForecastMutation.isPending ? <CircularProgress size={20} /> : <Send />}
            onClick={() => asyncForecastMutation.mutate()}
            disabled={asyncForecastMutation.isPending || !hasUploadedData || isProcessing}
          >
            {asyncForecastMutation.isPending ? 'Başlatılıyor...' : 'ASYNC Analiz Et'}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>{success}</Alert>}
      
      {!hasUploadedData && !results.length && (
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

      {hasUploadedData && results.length === 0 && !error && (
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
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>📊 Tahmin Modelleri</Typography>
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

      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Sonuçlar ({results.length} malzeme)</Typography>
              <Button variant="contained" startIcon={<Download />} onClick={handleExport} size="small">
                Excel'e Aktar
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'primary.main' }}>
                    <TableCell sx={{ color: 'white' }}>Malzeme Kodu</TableCell>
                    <TableCell sx={{ color: 'white' }}>Grup</TableCell>
                    <TableCell sx={{ color: 'white' }}>Seçilen Model</TableCell>
                    <TableCell sx={{ color: 'white' }} align="center">Outlier</TableCell>
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
                              fontWeight: 'bold',
                            }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        {result.outlier_info?.has_outliers ? (
                          <Tooltip title={`${result.outlier_info.outlier_count} aykırı değer var`} arrow>
                            <Chip label="⚠️" size="small" color="warning" />
                          </Tooltip>
                        ) : (
                          <Chip label="✅" size="small" color="success" />
                        )}
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
                        <Button size="small" variant="outlined" onClick={() => handleCompare(result)}>
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
                        results.forEach((r) => {
                          const model = r.selected_model || 'unknown';
                          counts[model] = (counts[model] || 0) + 1;
                        });
                        const entries = Object.entries(counts);
                        if (entries.length === 0) return '-';
                        const sorted = entries.sort((a, b) => b[1] - a[1]);
                        return modelLabels[sorted[0][0]] || sorted[0][0];
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
                      {results.filter((r) => r.trend_direction === 'Artış').length}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                    <Typography variant="caption" color="text.secondary">Azalış Trendi</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {results.filter((r) => r.trend_direction === 'Azalış').length}
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
            <IconButton onClick={() => setShowComparison(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedMaterial && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 2 }}>
                Malzeme: {selectedMaterial.material_code} - {selectedMaterial.group}
              </Typography>

              {selectedMaterial.outlier_info?.has_outliers && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    ⚠️ Veride {selectedMaterial.outlier_info.outlier_count} aykırı değer tespit edildi!
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedMaterial.outlier_info.outliers.map((o: any) => `Hafta ${o.week}: ${o.value}`).join(' | ')}
                  </Typography>
                </Alert>
              )}

              <Card sx={{ mb: 2, bgcolor: 'grey.50' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      Model Başarısı (MAPE):
                    </Typography>
                    <Chip
                      label={getMapeStatus(selectedMaterial.model_rmse || 999).label}
                      color={getMapeStatus(selectedMaterial.model_rmse || 999).color as any}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {getMapeStatus(selectedMaterial.model_rmse || 999).description}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Değer: {selectedMaterial.model_rmse?.toFixed(1) || '?'}%
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

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
                      <TableRow
                        key={modelName}
                        sx={{ bgcolor: modelName === selectedMaterial.selected_model ? 'success.light' : 'inherit' }}
                      >
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

              <ModelParams result={selectedMaterial} />
              <ForecastChart result={selectedMaterial} />

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
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
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
                    const total = item.data?.total || 0;
                    const date = item.created_at ? new Date(item.created_at) : new Date();
                    return (
                      <TableRow key={item.id}>
                        <TableCell>
                          {date.toLocaleDateString('tr-TR')}{' '}
                          {date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={`${total}`} size="small" color="primary" />
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
    </Box>
  );
}