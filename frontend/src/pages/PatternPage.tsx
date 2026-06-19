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
  Stack,
  Divider,
} from '@mui/material';
import {
  Analytics,
  Send, 
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

interface PatternResult {
  pattern: string;
  cv: number;
  zero_ratio: number;
  trend: number;
  mean: number;
  std: number;
  median: number;
}

export default function PatternPage() {
  const [weeklyData, setWeeklyData] = useState<string>('100,120,90,110,130,80,95,105');
  const [result, setResult] = useState<PatternResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: number[]) => {
      const res = await api.post('/api/pattern', { weekly_data: data });
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
    mutation.mutate(data);
  };

  const handleClear = () => {
    setWeeklyData('');
    setResult(null);
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
    switch (pattern) {
      case 'DUZENLI_SABIT': return 'Düzenli Sabit Talep';
      case 'DUZENLI_ARTS': return 'Düzenli Artan Talep';
      case 'DUZENLI_AZALIS': return 'Düzenli Azalan Talep';
      case 'DEGISKEN': return 'Değişken Talep';
      case 'YUKSEK_DEGISKEN': return 'Yüksek Değişken Talep';
      case 'ASIRI_DEGISKEN': return 'Aşırı Değişken Talep';
      case 'SIFIR_TALEP': return 'Sıfır Talep';
      case 'ARALIKLI_DUSUK': return 'Aralıklı Düşük Talep';
      case 'ARALIKLI_YUKSEK': return 'Aralıklı Yüksek Talep';
      default: return pattern;
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        📊 Pattern Analizi
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Talep paterni analizi ile verilerinizin karakteristik özelliklerini keşfedin.
      </Typography>

      <Grid container spacing={3}>
        {/* Giriş Alanı */}
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                Veri Girişi
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Haftalık talep verilerinizi virgülle ayrılmış şekilde girin.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                label="Haftalık Veriler"
                placeholder="100,120,90,110,130,80,95,105"
                value={weeklyData}
                onChange={(e) => setWeeklyData(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmit}
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? 'Analiz Ediliyor...' : 'Analiz Et'}
                </Button>
                <Button variant="outlined" onClick={handleClear}>
                  Temizle
                </Button>
              </Stack>
              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Analiz yapılıyor...
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
                  Analiz Sonucu
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {/* Pattern */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                    Pattern:
                  </Typography>
                  <Chip
                    label={getPatternLabel(result.pattern)}
                    color={getPatternColor(result.pattern)}
                    icon={<Analytics />}
                  />
                </Box>

                {/* İstatistik Grid'i */}
                <Grid container spacing={2}>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        CV (Değişim Katsayısı)
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {result.cv.toFixed(4)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        Zero Ratio
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {result.zero_ratio.toFixed(4)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        Trend
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: result.trend >= 0 ? 'success.main' : 'error.main' }}>
                        {result.trend.toFixed(2)}%
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        Ortalama
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {result.mean.toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        Standart Sapma
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {result.std.toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4 }}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="caption" color="text.secondary">
                        Medyan
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {result.median.toFixed(2)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                {/* Yorum */}
                <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="body2" color="info.dark">
                    <strong>📌 Yorum:</strong>{' '}
                    {result.cv > 0.7
                      ? 'Talep yüksek değişkenlik gösteriyor. Emniyet stoğu artırılmalı.'
                      : result.cv > 0.4
                      ? 'Talep orta düzeyde değişken. Düzenli takip önerilir.'
                      : 'Talep düzenli ve öngörülebilir. Mevcut politika yeterli.'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz analiz yapılmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki alana verilerinizi girin ve "Analiz Et" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}