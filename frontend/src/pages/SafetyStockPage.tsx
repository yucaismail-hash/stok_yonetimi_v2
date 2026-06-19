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
  Chip,
  CircularProgress,
  Slider,
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
  Security,
  Send,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

interface SafetyStockResult {
  classic_ss: number;
  croston_ss: number;
  syntetos_boylan_ss: number;
  bootstrapping_ss: number;
  ml_ss: number;
  hybrid_ss: number;
}

export default function SafetyStockPage() {
  const [weeklyData, setWeeklyData] = useState<string>('100,120,90,110,130,80,95,105');
  const [leadTime, setLeadTime] = useState<number>(14);
  const [serviceLevel, setServiceLevel] = useState<number>(0.95);
  const [result, setResult] = useState<SafetyStockResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: { weekly_data: number[]; lead_time_days: number; service_level: number }) => {
      const res = await api.post('/api/safety-stock', data);
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = () => {
    const data = weeklyData.split(',').map((v) => parseFloat(v.trim()));
    if (data.some(isNaN)) {
      alert('Lütfen geçerli sayılar girin!');
      return;
    }
    mutation.mutate({
      weekly_data: data,
      lead_time_days: leadTime,
      service_level: serviceLevel,
    });
  };

  const handleClear = () => {
    setWeeklyData('');
    setResult(null);
  };

  const methodLabels: Record<string, string> = {
    classic_ss: 'Klasik SS',
    croston_ss: 'Croston',
    syntetos_boylan_ss: 'Syntetos-Boylan',
    bootstrapping_ss: 'Bootstrapping',
    ml_ss: 'ML Tabanlı',
    hybrid_ss: 'Hibrit (Önerilen)',
  };

  const methodColors: Record<string, string> = {
    classic_ss: '#1976d2',
    croston_ss: '#2e7d32',
    syntetos_boylan_ss: '#ed6c02',
    bootstrapping_ss: '#9c27b0',
    ml_ss: '#d32f2f',
    hybrid_ss: '#1f4e79',
  };

  const getBestMethod = (result: SafetyStockResult) => {
    const entries = Object.entries(result);
    const min = Math.min(...entries.map(([_, v]) => v));
    return entries.find(([_, v]) => v === min)?.[0] || 'hybrid_ss';
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        🛡️ Emniyet Stoku Hesaplama
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        6 farklı metod ile emniyet stoğu hesaplayın ve karşılaştırın.
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
                rows={3}
                variant="outlined"
                label="Haftalık Veriler"
                placeholder="100,120,90,110,130,80,95,105"
                value={weeklyData}
                onChange={(e) => setWeeklyData(e.target.value)}
                sx={{ mb: 2 }}
              />

              <Typography variant="body2" gutterBottom>
                Lead Time (Gün): {leadTime}
              </Typography>
              <Slider
                value={leadTime}
                onChange={(_, val) => setLeadTime(val as number)}
                min={1}
                max={60}
                step={1}
                marks={[
                  { value: 7, label: '7' },
                  { value: 14, label: '14' },
                  { value: 30, label: '30' },
                  { value: 60, label: '60' },
                ]}
                valueLabelDisplay="auto"
                sx={{ mb: 3 }}
              />

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
                  { value: 0.90, label: '90%' },
                  { value: 0.95, label: '95%' },
                  { value: 0.99, label: '99%' },
                ]}
                valueLabelDisplay="auto"
                sx={{ mb: 3 }}
              />

              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmit}
                  disabled={mutation.isPending}
                  fullWidth
                >
                  {mutation.isPending ? 'Hesaplanıyor...' : 'Hesapla'}
                </Button>
                <Button variant="outlined" onClick={handleClear}>
                  Temizle
                </Button>
              </Stack>

              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    6 metod hesaplanıyor...
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
                  Hesaplama Sonuçları
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'primary.main' }}>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Metod</TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">
                          Emniyet Stoku
                        </TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">
                          Durum
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(result).map(([key, value]) => {
                        const isBest = key === getBestMethod(result);
                        return (
                          <TableRow
                            key={key}
                            sx={{
                              bgcolor: isBest ? 'success.light' : 'inherit',
                              '&:hover': { bgcolor: 'action.hover' },
                            }}
                          >
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box
                                  sx={{
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    bgcolor: methodColors[key] || '#ccc',
                                  }}
                                />
                                <Typography sx={{ fontWeight: isBest ? 'bold' : 'normal' }}>
                                  {methodLabels[key] || key}
                                </Typography>
                                {isBest && (
                                  <Chip
                                    label="✅ En İyi"
                                    size="small"
                                    color="success"
                                    sx={{ ml: 1 }}
                                  />
                                )}
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <Typography sx={{ fontWeight: isBest ? 'bold' : 'normal' }}>
                                {value.toFixed(2)}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={isBest ? 'Önerilen' : 'Alternatif'}
                                size="small"
                                color={isBest ? 'success' : 'default'}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Özet Bilgi */}
                <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="body2" color="info.dark">
                    <strong>📌 Öneri:</strong>{' '}
                    {getBestMethod(result) === 'hybrid_ss'
                      ? 'Hibrit metod, tüm yöntemlerin ağırlıklı ortalamasını alır. En dengeli sonucu verir.'
                      : `En düşük emniyet stoğu ${methodLabels[getBestMethod(result)]} metodu ile elde edilmiştir.`}
                  </Typography>
                </Box>

                {/* Metod Açıklamaları */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary" component="div">
                    💡 <strong>Klasik SS:</strong> Normal dağılım varsayımı ile
                    <br />
                    💡 <strong>Croston:</strong> Aralıklı talep için geliştirilmiş
                    <br />
                    💡 <strong>Syntetos-Boylan:</strong> Croston'ın bias düzeltilmiş hali
                    <br />
                    💡 <strong>Bootstrapping:</strong> Simülasyon tabanlı
                    <br />
                    💡 <strong>ML Tabanlı:</strong> Özellik ağırlıklı (CV, zero_ratio, trend)
                    <br />
                    💡 <strong>Hibrit:</strong> Tüm metodların ağırlıklı ortalaması (önerilen)
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Security sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz hesaplama yapılmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki alana verilerinizi girin ve "Hesapla" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}