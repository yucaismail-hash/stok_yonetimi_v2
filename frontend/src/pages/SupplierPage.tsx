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
  LinearProgress,
} from '@mui/material';
import {
  LocalShipping,
  Send,
  CheckCircle,
  Warning,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../services/api';

interface SupplierData {
  supplier_id: string;
  name: string;
  risk_score: number;
  performance_score: number;
  risk_level: string;
  performance_level: string;
  factor: number;
}

export default function SupplierPage() {
  const [supplierId, setSupplierId] = useState<string>('SUP001');
  const [result, setResult] = useState<SupplierData | null>(null);

  // Tedarikçi risk skoru sorgulama
  const mutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.get(`/api/supplier/${id}/risk`);
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = () => {
    if (!supplierId.trim()) {
      alert('Lütfen bir tedarikçi kodu girin!');
      return;
    }
    mutation.mutate(supplierId);
  };

  const getRiskColor = (risk: number) => {
    if (risk > 0.7) return 'error';
    if (risk > 0.4) return 'warning';
    return 'success';
  };

  const getPerformanceColor = (perf: number) => {
    if (perf > 0.7) return 'success';
    if (perf > 0.4) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        🚚 Tedarikçi Yönetimi
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Tedarikçi risk ve performans analizi, pay optimizasyonu.
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                Tedarikçi Sorgula
              </Typography>

              <TextField
                fullWidth
                variant="outlined"
                label="Tedarikçi Kodu"
                placeholder="SUP001"
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
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
                  {mutation.isPending ? 'Sorgulanıyor...' : 'Sorgula'}
                </Button>
              </Stack>

              {mutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Tedarikçi bilgileri alınıyor...
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
                  Tedarikçi Detay
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {result.supplier_id}
                  </Typography>
                  <Chip
                    label={result.supplier_id === 'SUP001' ? '✅ Ana Tedarikçi' : 'Alternatif'}
                    color="primary"
                  />
                </Box>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 6 }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Risk Skoru</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                        <Typography variant="h5" sx={{ fontWeight: 'bold', color: result.risk_score > 0.7 ? 'error.main' : result.risk_score > 0.4 ? 'warning.main' : 'success.main' }}>
                          {(result.risk_score * 100).toFixed(0)}%
                        </Typography>
                        <Chip
                          label={result.risk_level}
                          size="small"
                          color={getRiskColor(result.risk_score)}
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={result.risk_score * 100}
                        color={getRiskColor(result.risk_score)}
                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                      />
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Performans Skoru</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                        <Typography variant="h5" sx={{ fontWeight: 'bold', color: result.performance_score > 0.7 ? 'success.main' : result.performance_score > 0.4 ? 'warning.main' : 'error.main' }}>
                          {(result.performance_score * 100).toFixed(0)}%
                        </Typography>
                        <Chip
                          label={result.performance_level}
                          size="small"
                          color={getPerformanceColor(result.performance_score)}
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={result.performance_score * 100}
                        color={getPerformanceColor(result.performance_score)}
                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                      />
                    </Paper>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="body2" color="info.dark">
                    <strong>📌 Değerlendirme:</strong>{' '}
                    {result.risk_score < 0.4 && result.performance_score > 0.7
                      ? 'Bu tedarikçi düşük riskli ve yüksek performanslı. Tercih edilmeli.'
                      : result.risk_score > 0.7
                      ? 'Bu tedarikçi yüksek riskli. Alternatif tedarikçi düşünülmeli.'
                      : result.performance_score < 0.4
                      ? 'Bu tedarikçi düşük performanslı. İyileştirme planı gerekiyor.'
                      : 'Bu tedarikçi orta seviyede. Düzenli takip edilmeli.'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <LocalShipping sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Henüz tedarikçi sorgulanmadı
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sol taraftaki alana tedarikçi kodunu girin ve "Sorgula" butonuna tıklayın.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}