// frontend/src/components/common/MetricCard.tsx
// Stokonomi Design System - Metric Card (Tek metrik gösterimi)

import { Box, Typography, Paper, Tooltip, Skeleton } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

export interface MetricCardProps {
  /** Metrik başlığı */
  label: string;
  /** Metrik değeri */
  value: string | number;
  /** Önceki değere göre değişim (yüzde veya sayı) */
  change?: number;
  /** Değişim etiketi (ör: 'TL', '%') */
  changeLabel?: string;
  /** Değişim açıklaması (tooltip için) */
  changeDescription?: string;
  /** İkon */
  icon?: React.ReactNode;
  /** Renk (hex veya tema rengi) */
  color?: string;
  /** Tooltip açıklaması */
  tooltip?: string;
  /** Yükleniyor durumu */
  loading?: boolean;
  /** Kompakt mod */
  compact?: boolean;
  /** Alt metin (küçük açıklama) */
  subtitle?: string;
  /** Tıklama olayı */
  onClick?: () => void;
}

export default function MetricCard({
  label,
  value,
  change,
  changeLabel = '',
  changeDescription,
  icon,
  color = '#1f4e79',
  tooltip,
  loading = false,
  compact = false,
  subtitle,
  onClick,
}: MetricCardProps) {
  // Değişim hesaplamaları
  const changeColor = change 
    ? change > 0 ? '#2e7d32' : change < 0 ? '#d32f2f' : '#9e9e9e'
    : '#9e9e9e';

  const ChangeIcon = change 
    ? change > 0 ? TrendingUp : change < 0 ? TrendingDown : Remove
    : Remove;

  const isPositive = change ? change > 0 : false;
  const isNegative = change ? change < 0 : false;

  // Tooltip içeriği
  const tooltipContent = tooltip || (changeDescription ? `${changeDescription}` : '');

  const cardContent = (
    <Paper
      sx={{
        p: compact ? 1.25 : 1.5,
        bgcolor: '#fafcff',
        border: '1px solid #e8f0fe',
        borderRadius: 2,
        height: compact ? 72 : 88,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        transition: 'all 0.2s',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? {
          boxShadow: 2,
          borderColor: color,
          transform: 'translateY(-1px)',
        } : {},
      }}
      onClick={onClick}
    >
      {loading ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Skeleton variant="text" width="60%" height={14} />
          <Skeleton variant="text" width="40%" height={24} />
        </Box>
      ) : (
        <>
          {/* Başlık */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 0.25 }}>
            {icon && (
              <Box sx={{ color: color, display: 'flex', alignItems: 'center' }}>
                {icon}
              </Box>
            )}
            <Typography
              variant="caption"
              sx={{
                fontSize: compact ? '0.55rem' : '0.6rem',
                color: '#6b7280',
                fontWeight: 500,
                letterSpacing: '0.3px',
                textTransform: 'uppercase',
              }}
            >
              {label}
            </Typography>
          </Box>

          {/* Değer ve Değişim */}
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                fontSize: compact ? '1.1rem' : '1.25rem',
                color: color,
                lineHeight: 1.2,
              }}
            >
              {value}
            </Typography>

            {change !== undefined && change !== 0 && (
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 0.25,
                  bgcolor: isPositive ? '#e8f5e9' : isNegative ? '#ffebee' : '#f5f5f5',
                  px: 0.5,
                  py: 0.25,
                  borderRadius: 1,
                }}
              >
                <ChangeIcon sx={{ fontSize: 12, color: changeColor }} />
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: compact ? '0.5rem' : '0.55rem',
                    fontWeight: 600,
                    color: changeColor,
                  }}
                >
                  {change > 0 ? '+' : ''}{change}
                  {changeLabel && ` ${changeLabel}`}
                </Typography>
              </Box>
            )}
          </Box>

          {/* Alt metin */}
          {subtitle && (
            <Typography
              variant="caption"
              sx={{
                fontSize: '0.5rem',
                color: '#9e9e9e',
                mt: 0.25,
                display: 'block',
              }}
            >
              {subtitle}
            </Typography>
          )}
        </>
      )}
    </Paper>
  );

  if (tooltipContent) {
    return (
      <Tooltip title={tooltipContent} arrow placement="top">
        <Box>{cardContent}</Box>
      </Tooltip>
    );
  }

  return cardContent;
}