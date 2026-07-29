// frontend/src/components/Dashboard/ExecutiveSummary.tsx
// AI Yönetici Özeti - Sayısal verilere dayanan yönetici özeti

import { Box, Typography, Paper, Chip, Avatar, Skeleton, Button, alpha } from '@mui/material';
import { Bot, TrendingUp, TrendingDown, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

interface ExecutiveSummaryData {
  summary: string;
  details: {
    total_products: number;
    critical_products: number;
    avg_risk_score: number;
    avg_service_level: number;
    riskiest_group: string;
    top_problem: string;
    top_recommendation: string;
  };
  confidence: number;
  last_analysis_date: string;
}

interface ExecutiveSummaryProps {
  data: ExecutiveSummaryData | null;
  loading: boolean;
  onReadMore: () => void;
}

const MetricCard = ({ label, value, color }: { label: string; value: string | number; color?: string }) => (
  <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
    <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#6b7280', display: 'block' }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: color || '#1f4e79' }}>
      {value}
    </Typography>
  </Box>
);

export default function ExecutiveSummary({ data, loading, onReadMore }: ExecutiveSummaryProps) {
  if (loading) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#f8faff' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Skeleton variant="circular" width={40} height={40} />
          <Box sx={{ flex: 1 }}>
            <Skeleton variant="text" width="40%" height={20} />
            <Skeleton variant="text" width="80%" height={14} />
            <Skeleton variant="text" width="60%" height={14} />
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Skeleton variant="rectangular" width={80} height={40} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={80} height={40} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={80} height={40} sx={{ borderRadius: 1 }} />
            </Box>
          </Box>
        </Box>
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#f8faff' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: '#1f4e79', width: 40, height: 40 }}>
            <Bot size={20} color="white" />
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
              Yönetici Özeti
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              Henüz analiz verisi yok. Analiz yaptıkça yönetici özeti burada görünecek.
            </Typography>
          </Box>
        </Box>
      </Paper>
    );
  }

  const { summary, details, confidence, last_analysis_date } = data;
  const { total_products, critical_products, avg_risk_score, avg_service_level, riskiest_group, top_problem, top_recommendation } = details;

  const getRiskColor = (score: number) => {
    if (score >= 0.7) return '#d32f2f';
    if (score >= 0.4) return '#ed6c02';
    return '#2e7d32';
  };

  const getServiceColor = (level: number) => {
    if (level >= 95) return '#2e7d32';
    if (level >= 90) return '#ed6c02';
    return '#d32f2f';
  };

  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid #d0e0ff',
        bgcolor: '#f0f7ff',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: '#1f4e79' }} />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <Avatar sx={{ bgcolor: '#1f4e79', width: 40, height: 40 }}>
          <Bot size={20} color="white" />
        </Avatar>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.8rem' }}>
              👔 Yönetici Özeti
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={`%${Math.round(confidence * 100)} Güven`}
                size="small"
                sx={{ height: 18, fontSize: '0.5rem', bgcolor: '#e8f0fe', color: '#1f4e79' }}
              />
              <Chip
                label={last_analysis_date}
                size="small"
                variant="outlined"
                sx={{ height: 18, fontSize: '0.45rem', borderColor: '#d0d0d0' }}
              />
            </Box>
          </Box>

          <Typography variant="body2" sx={{ color: '#1f4e79', fontWeight: 500, fontSize: '0.85rem', lineHeight: 1.5, mb: 1 }}>
            {summary}
          </Typography>

          {/* Metrik Kartları */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))', gap: 1, mb: 1 }}>
            <MetricCard label="Analiz Edilen Ürün" value={total_products} color="#1f4e79" />
            <MetricCard
              label="Kritik Ürün"
              value={critical_products}
              color={critical_products > 5 ? '#d32f2f' : '#2e7d32'}
            />
            <MetricCard
              label="Ortalama Risk"
              value={avg_risk_score.toFixed(2)}
              color={getRiskColor(avg_risk_score)}
            />
            <MetricCard
              label="Ortalama Servis"
              value={`%${avg_service_level.toFixed(0)}`}
              color={getServiceColor(avg_service_level)}
            />
            <MetricCard
              label="En Riskli Grup"
              value={riskiest_group || '-'}
              color="#d32f2f"
            />
          </Box>

          {/* En Önemli Problem ve Öneri */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, p: 1, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 1 }}>
            {top_problem && (
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#374151' }}>
                ⚠️ En önemli problem: <strong>{top_problem}</strong>
              </Typography>
            )}
            {top_recommendation && (
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#1f4e79' }}>
                💡 AI'nın ilk önerisi: <strong>{top_recommendation}</strong>
              </Typography>
            )}
          </Box>

          <Box sx={{ mt: 1 }}>
            <Button
              variant="text"
              size="small"
              onClick={onReadMore}
              sx={{
                color: '#1f4e79',
                fontWeight: 600,
                fontSize: '0.65rem',
                textTransform: 'none',
                p: 0,
                minWidth: 'auto',
                '&:hover': { bgcolor: 'transparent', textDecoration: 'underline' },
              }}
            >
              Detaylı Özeti Gör →
            </Button>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}