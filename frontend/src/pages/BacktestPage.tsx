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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Backpack,
  Send,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

interface BacktestResult {
  metrics: Record<string, any>;
  summary: {
    test_weeks: number;
    total_demand: number;
    avg_weekly_demand: number;
    demand_volatility: number;
  };
  comparison: {
    service_level: Record<string, number>;
    total_cost: Record<string, number>;
    total_holding_cost: Record<string, number>;
    total_shortage_cost: Record<string, number>;
  };
  recommendation: {
    best_strategy: string;
    reason: string;
    ranking: Record<string, any>;
  };
}

export default function BacktestPage() {
  const [historicalData, setHistoricalData] = useState<string>(
    '100,110,105,120,115,130,125,140,135,150,145,160,155,170,165,180,175,190,185,200,195,210,205,220,215,230,225,240,235,250,245,260,255,270,265,280,275,290,285,300,295,310,305,320,315,330,325,340,335,350,345,360'
  );
  const [testWindow, setTestWindow] = useState<number>(12);
  const [result, setResult] = useState<BacktestResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: { historical_demand: number[]; test_window: number }) => {
      const res = await api.post('/api/backtest', data);
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
      historical_demand: data,
      test_window: testWindow,
    });
  };

  const handleClear = () => {
    setHistoricalData('');
    setResult(null);
  };

  const strategyLabels: Record<string, string> = {
    ai: 'AI (Hibrit)',
    classic: 'Klasik SS',
    croston: 'Croston',
    syntetos_boylan: 'Syntetos-Boylan',
    ml: 'ML Tabanlı',
    hybrid: 'Hibrit',
    simple_moving_avg: 'Basit MA',
    last_value: 'Son Değer',
  };

  const getBestStrategy = (comparison: BacktestResult['comparison']) => {
    const entries = Object.entries(comparison.total_cost);
    const min = Math.min(...entries.map(([_, v]) => v));
    return entries.find(([_, v]) => v === min)?.[0] || 'hybrid';
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        🎒 Backtest
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        8 farklı stratejiyi geçmiş veri üzerinde test edin ve karşılaştırın.
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                Parametreler
              </Typography>

              <TextField
                fullWidth
                multiline
                rows={6}
                variant="outlined"
                label="Geçmiş Talep Verileri"
                placeholder="100,110,105,120,..."
                value={historicalData}
                onChange={(e) => setHistoricalData(e.target.value)}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                type="number"
                variant="outlined"
                label="Test Penceresi (Hafta)"
                value={testWindow}
                onChange={(e) => setTestWindow(Number(e.target.value))}
                slotProps={{
                  htmlInput: { min: 4, max: 52 }
                }}
                sx={{ mb: 2 }}
              />

              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmit}
                  disabled={mutation.isPending}
                  fullWidth
                >
                  {mutation.isPending ? 'Test Ediliyor...' : 'Testi Başlat'}
                </Button>
                <Button variant="outlined" onClick={handleClear}>
                  Temizle
                </Button>
              </Stack>

              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    8 strateji test ediliyor...
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          {result ? (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                  Backtest Sonuçları
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  Test Dönemi: {result.summary.test_weeks} hafta | Toplam Talep: {result.summary.total_demand.toFixed(0)} birim
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'primary.main' }}>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }}>Strateji</TableCell>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }} align="right">Servis</TableCell>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }} align="right">Toplam Maliyet</TableCell>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }} align="right">Tutma</TableCell>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }} align="right">Stok Tükenme</TableCell>
                        <TableCell sx={{ color: 'white', sx: { fontWeight: 'bold' } }} align="center">Durum</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(result.comparison.service_level).map(([key, service]) => {
                        const totalCost = result.comparison.total_cost[key] || 0;
                        const holdingCost = result.comparison.total_holding_cost?.[key] || 0;
                        const shortageCost = result.comparison.total_shortage_cost?.[key] || 0;
                        const isBest = key === getBestStrategy(result.comparison);
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
                                <Typography sx={{ fontWeight: isBest ? 'bold' : 'normal' }}>
                                  {strategyLabels[key] || key}
                                </Typography>
                                {isBest && (
                                  <Chip label="🏆 En İyi" size="small" color="success" />
                                )}
                              </Box>
                            </TableCell>
                            <TableCell align="right">{(service * 100).toFixed(1)}%</TableCell>
                            <TableCell align="right" sx={{ fontWeight: isBest ? 'bold' : 'normal' }}>
                              {totalCost.toFixed(0)}
                            </TableCell>
                            <TableCell align="right">{holdingCost.toFixed(0)}</TableCell>
                            <TableCell align="right">{shortageCost.toFixed(0)}</TableCell>
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

                <Box sx={{ mt: 3, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    🏆 En İyi Strateji: {strategyLabels[result.recommendation.best_strategy] || result.recommendation.best_strategy}
                  </Typography>
                  <Typography variant="body2">
                    {result.recommendation.reason}
                  </Typography>
                </Box>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary" component="div">
                    💡 <strong>Strateji Açıklamaları:</strong>
                    <br />
                    • <strong>AI (Hibrit):</strong> Tüm metodların ağırlıklı ortalaması + pattern multiplier
                    <br />
                    • <strong>Klasik SS:</strong> Normal dağılım varsayımı ile
                    <br />
                    • <strong>Croston:</strong> Aralıklı talep için geliştirilmiş
                    <br />
                    • <strong>ML Tabanlı:</strong> CV, zero_ratio, trend özellikleri ile
                    <br />
                    • <strong>Basit MA:</strong> Son 4 haftanın ağırlıklı ortalaması
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Backpack sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz backtest yapılmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki alana verilerinizi girin ve "Testi Başlat" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}