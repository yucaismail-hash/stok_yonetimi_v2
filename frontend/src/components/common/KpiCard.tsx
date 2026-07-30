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
        p: 1,  // ✅ 1.5 → 1 (daha küçük)
        bgcolor: '#fafcff',
        border: '1px solid #e8f0fe',
        borderRadius: 1.5,
        height: 64,  // ✅ 88 → 64 (daha kısa)
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        transition: 'all 0.2s',
        overflow: 'hidden',  // ✅ Taşmayı önle
        '&:hover': {
          boxShadow: 1,
          borderColor: color,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0 }}>
        {icon && <Box sx={{ color: color, display: 'flex', alignItems: 'center' }}>{icon}</Box>}
        <Typography
          variant="caption"
          sx={{
            fontSize: '0.5rem',  // ✅ 0.6 → 0.5
            color: '#6b7280',
            fontWeight: 500,
            letterSpacing: '0.2px',
            textTransform: 'uppercase',
            whiteSpace: 'nowrap',  // ✅ Tek satır
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {label}
        </Typography>
      </Box>

      <Typography
        variant="h6"
        sx={{
          fontWeight: 700,
          fontSize: '0.95rem',  // ✅ 1.1 → 0.95
          color: color,
          lineHeight: 1.1,
          whiteSpace: 'nowrap',  // ✅ Tek satır
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {value}
      </Typography>
    </Paper>

  );

  if (tooltip) {
    return <Tooltip title={tooltip} arrow placement="top">
      <Box>{cardContent}</Box>
    </Tooltip>;
  }

  return cardContent;
}