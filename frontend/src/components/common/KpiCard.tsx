// frontend/src/components/common/KpiCard.tsx
// Stokonomi Design System - KPI Card

import { Box, Typography, Paper, Tooltip } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

// ✅ interface'i export et
export interface KpiCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  color?: string;
  tooltip?: string;
  compact?: boolean;
}

export default function KpiCard({
  label,
  value,
  change,
  changeLabel,
  icon,
  color = '#1f4e79',
  tooltip,
  compact = false,
}: KpiCardProps) {
  const changeColor = change 
    ? change > 0 ? '#2e7d32' : change < 0 ? '#d32f2f' : '#9e9e9e'
    : '#9e9e9e';

  const ChangeIcon = change 
    ? change > 0 ? TrendingUp : change < 0 ? TrendingDown : Remove
    : Remove;

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
        '&:hover': {
          boxShadow: 2,
          borderColor: color,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 0.25 }}>
        {icon && <Box sx={{ color: color, display: 'flex', alignItems: 'center' }}>{icon}</Box>}
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
            <ChangeIcon sx={{ fontSize: 14, color: changeColor }} />
            <Typography
              variant="caption"
              sx={{
                fontSize: compact ? '0.55rem' : '0.6rem',
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
    </Paper>
  );

  if (tooltip) {
    return <Tooltip title={tooltip} arrow placement="top">
      <Box>{cardContent}</Box>
    </Tooltip>;
  }

  return cardContent;
}