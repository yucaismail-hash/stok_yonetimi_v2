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
  Alert,
} from '@mui/material';
import {
  Warning,
  Send,
  CheckCircle,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import api from '../../services/api';

interface TailRiskResult {
  tail_risk: number;
  service_level: number;
  interpretation: string;
}

interface CVaRResult {
  cvar_95: number;
}

interface ServiceGapResult {
  actual: number;
  target: number;
  gap: number;
  gap_percent: number;
  status: string;
}

export default function RiskPage() {
  const [shortageData, setShortageData] = useState<string>('10,20,30,40,50,5,15,25,35,45,0,10,20,30,40');
  const [serviceLevel, setServiceLevel] = useState<number>(0.95);
  const [actualService, setActualService] = useState<number>(0.85);
  const [targetService, setTargetService] = useState<number>(0.95);

  const [tailResult, setTailResult] = useState<TailRiskResult | null>(null);
  const [cvarResult, setCVaRResult] = useState<CVaRResult | null>(null);
  const [gapResult, setGapResult] = useState<ServiceGapResult | null>(null);

  const tailMutation = useMutation({
    mutationFn: async (data: { shortage_paths: number[][]; service_level: number }) => {
      const res = await api.post('/api/risk/tail-risk', data);
      return res.data;
    },
    onSuccess: (data) => setTailResult(data),
  });

  const cvarMutation = useMutation({
    mutationFn: async (data: { shortage_paths: number[][] }) => {
      const res = await api.post('/api/risk/cvar95', data);
      return res.data;
    },
    onSuccess: (data) => setCVaRResult(data),
  });

  const gapMutation = useMutation({
    mutationFn: async (data: { actual_service_level: number; target_service_level: number }) => {
      const res = await api.post('/api/risk/service-level-gap', data);
      return res.data;
    },
    onSuccess: (data) => setGapResult(data),
  });

  const handleTailRisk = () => {
    const data = shortageData.split(',').map((v) => parseFloat(v.trim()));
    if (data.some(isNaN)) {
      alert('Lütfen geçerli sayılar girin!');
      return;
    }
    // 2D array oluştur (örnek: 3 satır)
    const paths = [data.slice(0, 5), data.slice(5, 10), data.slice(10, 15)].filter(arr => arr.length > 0);
    tailMutation.mutate({ shortage_paths: paths, service_level: serviceLevel });
  };

  const handleCVaR = () => {
    const data = shortageData.split(',').map((v) => parseFloat(v.trim()));
    if (data.some(isNaN)) {
      alert('Lütfen geçerli sayılar girin!');
      return;
    }
    const paths = [data.slice(0, 5), data.slice(5, 10), data.slice(10, 15)].filter(arr => arr.length > 0);
    cvarMutation.mutate({ shortage_paths: paths });
  };

  const handleGap = () => {
    gapMutation.mutate({
      actual_service_level: actualService,
      target_service_level: targetService,
    });
  };

  const getTailRiskLabel = (risk: number) => {
    if (risk > 0.7) return { label: 'Yüksek Risk', color: 'error' };
    if (risk > 0.4) return { label: 'Orta Risk', color: 'warning' };
    return { label: 'Düşük Risk', color: 'success' };
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} gutterBottom>
        ⚠️ Risk Metrikleri
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Tail Risk, CVaR95 ve Servis Seviyesi Gap hesaplamaları.
      </Typography>

      <Grid container spacing={3}>
        {/* Tail Risk */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                🎯 Tail Risk
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Stok tükenme verilerinden kuyruk riski hesaplar.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                label="Stok Tükenme Verileri"
                value={shortageData}
                onChange={(e) => setShortageData(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                type="number"
                label="Servis Seviyesi"
                value={serviceLevel}
                onChange={(e) => setServiceLevel(Number(e.target.value))}
                slotProps={{ htmlInput: { min: 0.8, max: 0.99, step: 0.01 } }}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleTailRisk}
                disabled={tailMutation.isPending}
                fullWidth
              >
                {tailMutation.isPending ? 'Hesaplanıyor...' : 'Tail Risk Hesapla'}
              </Button>
              {tailMutation.isPending && <CircularProgress size={24} sx={{ mt: 2 }} />}
              {tailResult && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body2">
                    <strong>Tail Risk:</strong> {tailResult.tail_risk.toFixed(2)}
                  </Typography>
                  <Chip
                    label={getTailRiskLabel(tailResult.tail_risk).label}
                    color={getTailRiskLabel(tailResult.tail_risk).color as any}
                    sx={{ mt: 1 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* CVaR95 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                📊 CVaR95
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                En kötü %5 senaryoda ortalama stok tükenmesi.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                label="Stok Tükenme Verileri"
                value={shortageData}
                onChange={(e) => setShortageData(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleCVaR}
                disabled={cvarMutation.isPending}
                fullWidth
              >
                {cvarMutation.isPending ? 'Hesaplanıyor...' : 'CVaR95 Hesapla'}
              </Button>
              {cvarMutation.isPending && <CircularProgress size={24} sx={{ mt: 2 }} />}
              {cvarResult && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body2">
                    <strong>CVaR95:</strong> {cvarResult.cvar_95.toFixed(1)}
                  </Typography>
                  <Chip
                    label={cvarResult.cvar_95 > 50 ? '⚠️ Yüksek' : '✅ Düşük'}
                    color={cvarResult.cvar_95 > 50 ? 'warning' : 'success'}
                    sx={{ mt: 1 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Servis Seviyesi Gap */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
                📏 Servis Seviyesi Gap
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Gerçekleşen ile hedef servis seviyesi arasındaki fark.
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Gerçekleşen Servis"
                value={actualService}
                onChange={(e) => setActualService(Number(e.target.value))}
                slotProps={{ htmlInput: { min: 0, max: 1, step: 0.01 } }}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                type="number"
                label="Hedef Servis"
                value={targetService}
                onChange={(e) => setTargetService(Number(e.target.value))}
                slotProps={{ htmlInput: { min: 0.8, max: 0.99, step: 0.01 } }}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleGap}
                disabled={gapMutation.isPending}
                fullWidth
              >
                {gapMutation.isPending ? 'Hesaplanıyor...' : 'Gap Hesapla'}
              </Button>
              {gapMutation.isPending && <CircularProgress size={24} sx={{ mt: 2 }} />}
              {gapResult && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body2">
                    <strong>Gap:</strong> {(gapResult.gap * 100).toFixed(1)}%
                  </Typography>
                  <Chip
                    label={gapResult.status}
                    color={gapResult.gap >= 0 ? 'success' : 'error'}
                    sx={{ mt: 1 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}