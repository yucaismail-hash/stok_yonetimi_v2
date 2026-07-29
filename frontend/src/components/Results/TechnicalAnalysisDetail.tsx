// frontend/src/components/Results/TechnicalAnalysisDetail.tsx
// Teknik Analiz Bölümü - CV, Pattern, ABC, XYZ, Forecast, Trend, Seasonality, Lead Time, Zero Ratio

import { Box, Typography, Paper, Chip, Divider, Grid, Tooltip, alpha } from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  Timeline,
  Category,
  CalendarToday,
  LocalShipping,
  Analytics,
  Warning,
  CheckCircle,
} from '@mui/icons-material';

interface TechnicalAnalysisDetailProps {
  data: {
    material_code: string;
    cv: number;
    pattern: string;
    pattern_label: string;
    pattern_color: string;
    abc: string;
    abc_label: string;
    xyz: string;
    xyz_label: string;
    forecast_model: string;
    forecast_model_label: string;
    seasonality: boolean;
    seasonality_label: string;
    seasonality_strength: number;
    trend_direction: string;
    trend_percent: number;
    lead_time_days: number;
    zero_ratio: number;
    risk_score: number;
    risk_level: string;
  };
}

const MetricRow = ({ label, value, icon, color }: { label: string; value: React.ReactNode; icon?: React.ReactNode; color?: string }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 0.5, borderRadius: 1 }}>
    {icon && <Box sx={{ color: color || '#6b7280' }}>{icon}</Box>}
    <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', minWidth: 60 }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: color || '#1f4e79' }}>
      {value}
    </Typography>
  </Box>
);

export default function TechnicalAnalysisDetail({ data }: TechnicalAnalysisDetailProps) {
  const {
    material_code,
    cv,
    pattern_label,
    pattern_color,
    abc,
    xyz,
    forecast_model_label,
    seasonality,
    seasonality_label,
    seasonality_strength,
    trend_direction,
    trend_percent,
    lead_time_days,
    zero_ratio,
    risk_score,
    risk_level,
  } = data;

  const getPatternColor = (color: string): string => {
    switch (color) {
      case 'success': return '#2e7d32';
      case 'warning': return '#ed6c02';
      case 'error': return '#d32f2f';
      case 'info': return '#1976d2';
      case 'primary': return '#1f4e79';
      case 'secondary': return '#9c27b0';
      default: return '#6b7280';
    }
  };

  const getRiskColor = (level: string): string => {
    switch (level) {
      case 'Yüksek': return '#d32f2f';
      case 'Orta': return '#ed6c02';
      default: return '#2e7d32';
    }
  };

  const getAbcColor = (abcLetter: string): string => {
    switch (abcLetter) {
      case 'A': return '#d32f2f';
      case 'B': return '#ed6c02';
      default: return '#2e7d32';
    }
  };

  const getXyzColor = (xyzLetter: string): string => {
    switch (xyzLetter) {
      case 'X': return '#2e7d32';
      case 'Y': return '#ed6c02';
      default: return '#d32f2f';
    }
  };

  const getCvColor = (cvValue: number): string => {
    if (cvValue < 0.3) return '#2e7d32';
    if (cvValue < 0.6) return '#ed6c02';
    return '#d32f2f';
  };

  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid #e8f0fe',
        bgcolor: '#fafcff',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.8rem' }}>
          📊 Teknik Analiz: {material_code}
        </Typography>
        <Chip
          label={`Risk: ${risk_level}`}
          size="small"
          sx={{
            height: 20,
            fontSize: '0.55rem',
            fontWeight: 600,
            bgcolor: alpha(getRiskColor(risk_level), 0.1),
            color: getRiskColor(risk_level),
            border: `1px solid ${alpha(getRiskColor(risk_level), 0.3)}`,
          }}
        />
      </Box>

      <Grid container spacing={1.5}>
        {/* Sol Sütun - Temel Metrikler */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{
              p: 1.5,
              bgcolor: '#f5f5f5',
              borderRadius: 1.5,
              border: '1px solid #e8f0fe',
            }}
          >
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block', mb: 1 }}>
              Temel Metrikler
            </Typography>

            <MetricRow
              label="CV"
              value={cv.toFixed(3)}
              icon={<ShowChart sx={{ fontSize: 14 }} />}
              color={getCvColor(cv)}
            />

            <MetricRow
              label="Pattern"
              value={
                <Chip
                  label={pattern_label}
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '0.5rem',
                    fontWeight: 600,
                    bgcolor: alpha(getPatternColor(pattern_color), 0.1),
                    color: getPatternColor(pattern_color),
                    border: `1px solid ${alpha(getPatternColor(pattern_color), 0.3)}`,
                  }}
                />
              }
              icon={<Category sx={{ fontSize: 14 }} />}
            />

            <MetricRow
              label="ABC"
              value={
                <Chip
                  label={abc}
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '0.5rem',
                    fontWeight: 700,
                    bgcolor: alpha(getAbcColor(abc), 0.1),
                    color: getAbcColor(abc),
                    border: `1px solid ${alpha(getAbcColor(abc), 0.3)}`,
                  }}
                />
              }
              icon={<Category sx={{ fontSize: 14 }} />}
            />

            <MetricRow
              label="XYZ"
              value={
                <Chip
                  label={xyz}
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '0.5rem',
                    fontWeight: 700,
                    bgcolor: alpha(getXyzColor(xyz), 0.1),
                    color: getXyzColor(xyz),
                    border: `1px solid ${alpha(getXyzColor(xyz), 0.3)}`,
                  }}
                />
              }
              icon={<Analytics sx={{ fontSize: 14 }} />}
            />

            <MetricRow
              label="Forecast"
              value={forecast_model_label}
              icon={<ShowChart sx={{ fontSize: 14 }} />}
              color="#1976d2"
            />
          </Box>
        </Grid>

        {/* Sağ Sütun - Zaman/Değişkenlik Metrikleri */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{
              p: 1.5,
              bgcolor: '#f5f5f5',
              borderRadius: 1.5,
              border: '1px solid #e8f0fe',
            }}
          >
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block', mb: 1 }}>
              Zaman & Değişkenlik
            </Typography>

            <MetricRow
              label="Trend"
              value={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {trend_direction === 'Artış' ? (
                    <TrendingUp sx={{ fontSize: 14, color: '#d32f2f' }} />
                  ) : (
                    <TrendingDown sx={{ fontSize: 14, color: '#2e7d32' }} />
                  )}
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: '#1f4e79' }}>
                    {trend_direction} ({trend_percent > 0 ? '+' : ''}{trend_percent.toFixed(1)}%)
                  </Typography>
                </Box>
              }
              icon={<Timeline sx={{ fontSize: 14 }} />}
            />

            <MetricRow
              label="Seasonality"
              value={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Chip
                    label={seasonality_label}
                    size="small"
                    color={seasonality ? 'info' : 'default'}
                    sx={{ height: 18, fontSize: '0.45rem' }}
                  />
                  {seasonality && (
                    <Chip
                      label={`%${Math.round(seasonality_strength * 100)}`}
                      size="small"
                      variant="outlined"
                      sx={{ height: 16, fontSize: '0.4rem' }}
                    />
                  )}
                </Box>
              }
              icon={<CalendarToday sx={{ fontSize: 14 }} />}
            />

            <MetricRow
              label="Lead Time"
              value={`${lead_time_days} gün`}
              icon={<LocalShipping sx={{ fontSize: 14 }} />}
              color={lead_time_days > 21 ? '#d32f2f' : '#2e7d32'}
            />

            <MetricRow
              label="Zero Ratio"
              value={`${(zero_ratio * 100).toFixed(1)}%`}
              icon={<Warning sx={{ fontSize: 14 }} />}
              color={zero_ratio > 0.3 ? '#d32f2f' : '#2e7d32'}
            />

            <MetricRow
              label="Risk Skoru"
              value={risk_score.toFixed(2)}
              icon={<Warning sx={{ fontSize: 14 }} />}
              color={getRiskColor(risk_level)}
            />
          </Box>
        </Grid>
      </Grid>

      {/* Özet Etiketler */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1.5, pt: 1, borderTop: '1px solid #e8f0fe' }}>
        <Chip
          icon={trend_direction === 'Artış' ? <TrendingUp sx={{ fontSize: 12 }} /> : <TrendingDown sx={{ fontSize: 12 }} />}
          label={`Trend: ${trend_direction}`}
          size="small"
          color={trend_direction === 'Artış' ? 'error' : 'success'}
          variant="outlined"
          sx={{ height: 18, fontSize: '0.5rem' }}
        />
        <Chip
          icon={seasonality ? <CheckCircle sx={{ fontSize: 12 }} /> : <Warning sx={{ fontSize: 12 }} />}
          label={`Mevsimsellik: ${seasonality ? 'Var' : 'Yok'}`}
          size="small"
          color={seasonality ? 'info' : 'default'}
          variant="outlined"
          sx={{ height: 18, fontSize: '0.5rem' }}
        />
        <Chip
          icon={zero_ratio > 0.3 ? <Warning sx={{ fontSize: 12 }} /> : <CheckCircle sx={{ fontSize: 12 }} />}
          label={`Sıfır Talep: ${(zero_ratio * 100).toFixed(0)}%`}
          size="small"
          color={zero_ratio > 0.3 ? 'warning' : 'success'}
          variant="outlined"
          sx={{ height: 18, fontSize: '0.5rem' }}
        />
        <Chip
          label={`Forecast: ${forecast_model_label}`}
          size="small"
          variant="outlined"
          sx={{ height: 18, fontSize: '0.5rem' }}
        />
        <Chip
          label={`ABC: ${abc} / XYZ: ${xyz}`}
          size="small"
          variant="outlined"
          sx={{ height: 18, fontSize: '0.5rem' }}
        />
      </Box>
    </Paper>
  );
}