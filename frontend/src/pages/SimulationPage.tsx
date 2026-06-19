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
  Switch,
  FormControlLabel,
  Stack,
  Divider,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Tune,
  Send,
  CheckCircle,
  Warning,
  Timeline,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

interface SimulationResult {
  service_level: number;
  cvar_95: number;
  avg_stock: number[];
  stockout_probability: number[];
  expected_shortage: number[];
  regime_used: boolean;
  copula_used: boolean;
  adaptive_ss_used: boolean;
}

export default function SimulationPage() {
  const [params, setParams] = useState({
    initial_stock: 500,
    lead_time_mean: 14,
    lead_time_std: 3,
    demand_mean: 100,
    demand_std: 30,
    eoq: 400,
    rop: 350,
    weeks: 26,
    n_simulations: 500,
    use_regime: false,
    use_copula: false,
    use_adaptive_ss: false,
  });
  const [result, setResult] = useState<SimulationResult | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: typeof params) => {
      const res = await api.post('/api/simulate', data);
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = () => {
    mutation.mutate(params);
  };

  const handleClear = () => {
    setResult(null);
  };

  const handleChange = (field: string, value: any) => {
    setParams({ ...params, [field]: value });
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        🎲 Monte Carlo Simülasyonu
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Binlerce senaryo ile stok performansınızı simüle edin.
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                Parametreler
              </Typography>

              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Başlangıç Stoku"
                    value={params.initial_stock}
                    onChange={(e) => handleChange('initial_stock', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="EOQ"
                    value={params.eoq}
                    onChange={(e) => handleChange('eoq', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="ROP"
                    value={params.rop}
                    onChange={(e) => handleChange('rop', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Lead Time (Gün)"
                    value={params.lead_time_mean}
                    onChange={(e) => handleChange('lead_time_mean', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Talep (Ortalama)"
                    value={params.demand_mean}
                    onChange={(e) => handleChange('demand_mean', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Talep (Std)"
                    value={params.demand_std}
                    onChange={(e) => handleChange('demand_std', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Simülasyon Sayısı"
                    value={params.n_simulations}
                    onChange={(e) => handleChange('n_simulations', Number(e.target.value))}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Hafta Sayısı"
                    value={params.weeks}
                    onChange={(e) => handleChange('weeks', Number(e.target.value))}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Gelişmiş Modeller
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={params.use_regime}
                    onChange={(e) => handleChange('use_regime', e.target.checked)}
                  />
                }
                label="Rejim Modeli"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={params.use_copula}
                    onChange={(e) => handleChange('use_copula', e.target.checked)}
                  />
                }
                label="Copula (Talep-LT Bağımlılığı)"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={params.use_adaptive_ss}
                    onChange={(e) => handleChange('use_adaptive_ss', e.target.checked)}
                  />
                }
                label="Adaptive SS"
              />

              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmit}
                  disabled={mutation.isPending}
                  fullWidth
                >
                  {mutation.isPending ? 'Simüle Ediliyor...' : 'Simülasyonu Başlat'}
                </Button>
                <Button variant="outlined" onClick={handleClear}>
                  Temizle
                </Button>
              </Stack>

              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    {params.n_simulations} senaryo simüle ediliyor...
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
                  Simülasyon Sonuçları
                </Typography>

                <Grid container spacing={1} sx={{ mb: 3 }}>
                  <Grid size={{ xs: 6, sm: 2.4 }}>
                    <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'success.light' }}>
                      <Typography variant="caption" color="text.secondary">Servis</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
                        {(result.service_level * 100).toFixed(1)}%
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 2.4 }}>
                    <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'warning.light' }}>
                      <Typography variant="caption" color="text.secondary">CVaR95</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
                        {result.cvar_95.toFixed(1)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 2.4 }}>
                    <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: params.use_regime ? 'success.light' : 'grey.200' }}>
                      <Typography variant="caption" color="text.secondary">Rejim</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem', color: params.use_regime ? 'success.main' : 'text.secondary' }}>
                        {params.use_regime ? '✅' : '❌'}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 2.4 }}>
                    <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: params.use_copula ? 'success.light' : 'grey.200' }}>
                      <Typography variant="caption" color="text.secondary">Copula</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem', color: params.use_copula ? 'success.main' : 'text.secondary' }}>
                        {params.use_copula ? '✅' : '❌'}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 2.4 }}>
                    <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: params.use_adaptive_ss ? 'success.light' : 'grey.200' }}>
                      <Typography variant="caption" color="text.secondary">Adaptive</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem', color: params.use_adaptive_ss ? 'success.main' : 'text.secondary' }}>
                        {params.use_adaptive_ss ? '✅' : '❌'}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Divider sx={{ mb: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Haftalık Stok Tükenme Olasılığı (ilk 13 hafta)
                </Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 200 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Hafta</TableCell>
                        <TableCell align="right">Olasılık</TableCell>
                        <TableCell align="right">Beklenen Açık</TableCell>
                        <TableCell align="right">Ort. Stok</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.stockout_probability.slice(0, 13).map((prob, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{idx + 1}</TableCell>
                          <TableCell align="right">{(prob * 100).toFixed(1)}%</TableCell>
                          <TableCell align="right">{result.expected_shortage[idx]?.toFixed(1) || 0}</TableCell>
                          <TableCell align="right">{result.avg_stock[idx]?.toFixed(1) || 0}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Box sx={{ mt: 3, p: 2, bgcolor: result.service_level >= 0.95 ? 'success.light' : 'warning.light', borderRadius: 1 }}>
                  <Typography variant="body2">
                    <strong>📌 Değerlendirme:</strong>{' '}
                    {result.service_level >= 0.95
                      ? 'Servis seviyesi hedefin üzerinde. Stok politikası başarılı.'
                      : result.service_level >= 0.90
                      ? 'Servis seviyesi hedefe yakın. İyileştirme önerilir.'
                      : 'Servis seviyesi düşük. Stok politikası gözden geçirilmeli.'}
                    {' '}
                    {result.cvar_95 > 100
                      ? 'CVaR95 yüksek, aşırı stok tükenme riski var.'
                      : 'CVaR95 kabul edilebilir seviyede.'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Tune sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz simülasyon yapılmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki parametreleri girin ve "Simülasyonu Başlat" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}