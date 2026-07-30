// frontend/src/components/common/ExecutiveSummaryCard.tsx
// Yönetici Özeti (eski AI Executive Summary)

import { Box, Typography, Paper, Chip, Grid, Avatar, Divider } from '@mui/material';
import { Psychology, TrendingUp, TrendingDown, CheckCircle, Warning, AutoAwesome } from '@mui/icons-material';

export interface ExecutiveSummaryData {
  totalProducts: number;
  increaseCount: number;
  decreaseCount: number;
  maintainCount: number;
  topMethod: string;
  topRisk: string;
  estimatedImpact: string;
  confidence: number;
}

export interface ExecutiveSummaryCardProps {
  data?: ExecutiveSummaryData;
  loading?: boolean;
  compact?: boolean;
}

export default function ExecutiveSummaryCard({
  data,
  loading = false,
  compact = false,
}: ExecutiveSummaryCardProps) {
  if (loading) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#f8faff', minHeight: 100 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ bgcolor: '#1f4e79', width: 32, height: 32 }}>
            <Psychology sx={{ fontSize: 16, color: 'white' }} />
          </Avatar>
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
            Yönetici Özeti yükleniyor...
          </Typography>
        </Box>
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px dashed #d0d0d0', bgcolor: '#fafafa', minHeight: 80 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar sx={{ bgcolor: '#e0e0e0', width: 32, height: 32 }}>
            <Psychology sx={{ fontSize: 16, color: '#9e9e9e' }} />
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.75rem' }}>
              Yönetici Özeti
            </Typography>
            <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
              Analiz tamamlandığında özet burada görünecek.
            </Typography>
          </Box>
        </Box>
      </Paper>
    );
  }

  const {
    totalProducts,
    increaseCount,
    decreaseCount,
    maintainCount,
    topMethod,
    topRisk,
    estimatedImpact,
    confidence,
  } = data;

  return (
    <Paper
      sx={{
        p: compact ? 1.5 : 2,
        borderRadius: 2,
        border: '1px solid #d0e0ff',
        bgcolor: '#f0f7ff',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Üst çizgi */}
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: '#1f4e79' }} />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <Avatar sx={{ bgcolor: '#1f4e79', width: 36, height: 36 }}>
          <Psychology sx={{ fontSize: 18, color: 'white' }} />
        </Avatar>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 0.5 }}>
            {/* ✅ DEĞİŞTİ: AI Executive Summary → Yönetici Özeti */}
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1rem' }}>
              📊 Yönetici Özeti
            </Typography>
            <Chip
              label={`%${Math.round(confidence * 100)} Güven`}
              size="small"
              sx={{ height: 18, fontSize: '0.6rem', bgcolor: '#e8f0fe', color: '#1f4e79' }}
            />
          </Box>

          {/* Özet Metrikleri */}
          <Grid container spacing={1} sx={{ mt: 0.5 }}>
            <Grid size={{ xs: 6, sm: 2.4 }}>
              <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#6b7280' }}>📦 Ürün</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8rem', color: '#1f4e79' }}>
                  {totalProducts}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, sm: 2.4 }}>
              <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#6b7280' }}>📈 Artır</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8rem', color: '#d32f2f' }}>
                  {increaseCount}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, sm: 2.4 }}>
              <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#6b7280' }}>📉 Azalt</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8rem', color: '#2e7d32' }}>
                  {decreaseCount}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, sm: 2.4 }}>
              <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#6b7280' }}>✅ Koru</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8rem', color: '#1976d2' }}>
                  {maintainCount}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, sm: 2.4 }}>
              <Box sx={{ textAlign: 'center', p: 0.5, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#6b7280' }}>⭐ En İyi Metot</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.7rem', color: '#1f4e79' }}>
                  {topMethod}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Divider sx={{ my: 0.75 }} />

          {/* Risk ve Etki */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Warning sx={{ fontSize: 14, color: '#ed6c02' }} />
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#374151' }}>
                <strong>En önemli risk:</strong> {topRisk}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <AutoAwesome sx={{ fontSize: 14, color: '#1f4e79' }} />
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#374151' }}>
                <strong>Tahmini etki:</strong> {estimatedImpact}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}