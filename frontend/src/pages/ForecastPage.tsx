import { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Paper,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  Divider,
} from '@mui/material';
import {
  ShowChart,
  Send,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

interface ForecastResult {
  mean: number[];
  lower_80: number[];
  upper_80: number[];
  lower_95: number[];
  upper_95: number[];
}

export default function ForecastPage() {
  const [historicalData, setHistoricalData] = useState<string>(
    '100,110,105,120,115,130,125,140,135,150,145,160,155,170,165,180'
  );
  const [horizon, setHorizon] = useState<number>(8);
  const [modelType, setModelType] = useState<string>('auto');
  const [result, setResult] = useState<ForecastResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: { historical_data: number[]; horizon: number; model_type: string }) => {
      const res = await api.post('/api/forecast', data);
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = () => {
    const data = historicalData.split(',').map((v) => parseFloat(v.trim()));
    if (data.some(isNaN)) {
      alert('Lütfen geçerli sayılar girin!');
      return;
    }
    mutation.mutate({
      historical_data: data,
      horizon: horizon,
      model_type: modelType,
    });
  };

  const handleClear = () => {
    setHistoricalData('');
    setResult(null);
  };

  const modelLabels: Record<string, string> = {
    auto: 'Otomatik Seçim (Önerilen)',
    holt_winters: 'Holt-Winters (Mevsimsel)',
    arima: 'ARIMA',
    simple: 'Basit (Hareketli Ortalama)',
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        📈 Talep Tahmini (Forecast)
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Geçmiş verilerinize göre gelecek dönem talep tahmini yapın.
      </Typography>

      <Grid container spacing={3}>
        {/* Giriş Alanı */}
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                Parametreler
              </Typography>

              <TextField
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                label="Geçmiş Veriler"
                placeholder="100,110,105,120,115,130,125,140,135,150,145,160"
                value={historicalData}
                onChange={(e) => setHistoricalData(e.target.value)}
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Model Tipi</InputLabel>
                <Select
                  value={modelType}
                  label="Model Tipi"
                  onChange={(e) => setModelType(e.target.value)}
                >
                  <MenuItem value="auto">Otomatik Seçim (Önerilen)</MenuItem>
                  <MenuItem value="holt_winters">Holt-Winters (Mevsimsel)</MenuItem>
                  <MenuItem value="arima">ARIMA</MenuItem>
                  <MenuItem value="simple">Basit (Hareketli Ortalama)</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                type="number"
                variant="outlined"
                label="Tahmin Ufku (Hafta)"
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                slotProps={{
                  htmlInput: { min: 1, max: 52 }
                }}
                sx={{ mb: 2 }}
              />

              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmit}
                  disabled={mutation.isPending}
                  fullWidth
                >
                  {mutation.isPending ? 'Tahmin Ediliyor...' : 'Tahmin Et'}
                </Button>
                <Button variant="outlined" onClick={handleClear}>
                  Temizle
                </Button>
              </Stack>

              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Model çalıştırılıyor...
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sonuç Alanı */}
        <Grid size={{ xs: 12, lg: 7 }}>
          {result ? (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                  Tahmin Sonuçları
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  Model: {modelLabels[modelType] || modelType}
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'primary.main' }}>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Hafta</TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          Tahmin (Ortalama)
                        </TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          %80 Alt
                        </TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          %80 Üst
                        </TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          %95 Alt
                        </TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          %95 Üst
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.mean.map((value, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                            {value.toFixed(2)}
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'info.main' }}>
                            {result.lower_80[index].toFixed(2)}
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'info.main' }}>
                            {result.upper_80[index].toFixed(2)}
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'warning.main' }}>
                            {result.lower_95[index].toFixed(2)}
                          </TableCell>
                          <TableCell align="right" sx={{ color: 'warning.main' }}>
                            {result.upper_95[index].toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Özet Bilgi */}
                <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="body2" color="info.dark">
                    <strong>📌 Yorum:</strong>{' '}
                    {result.mean[result.mean.length - 1] > result.mean[0]
                      ? 'Talep trendi artış yönünde. Stok seviyeleri artırılmalı.'
                      : result.mean[result.mean.length - 1] < result.mean[0]
                      ? 'Talep trendi azalış yönünde. Stok seviyeleri gözden geçirilmeli.'
                      : 'Talep trendi stabil. Mevcut politika devam edebilir.'}
                  </Typography>
                </Box>

                {/* Güven Aralığı Açıklaması */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary" component="div">
                    📊 <strong>%80 Güven Aralığı:</strong> Tahminlerin %80'i bu aralıkta olacaktır.
                    <br />
                    📊 <strong>%95 Güven Aralığı:</strong> Tahminlerin %95'i bu aralıkta olacaktır.
                    <br />
                    💡 Daha geniş aralık = daha yüksek belirsizlik.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <ShowChart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz tahmin yapılmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki alana verilerinizi girin ve "Tahmin Et" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}