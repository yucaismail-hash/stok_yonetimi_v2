// frontend/src/components/common/KpiCard.tsx
// Stokonomi Design System - KPI Card (Küçültülmüş Versiyon)

import { Box, Typography, Paper, Tooltip } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

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
        p: compact ? 0.75 : 1.5,
        bgcolor: '#fafcff',
        border: '1px solid #e8f0fe',
        borderRadius: 1.5,
        height: compact ? 52 : 88,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        transition: 'all 0.2s',
        overflow: 'hidden',
        '&:hover': {
          boxShadow: 1,
          borderColor: color,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0 }}>
        {icon && (
          <Box sx={{ 
            color: color, 
            display: 'flex', 
            alignItems: 'center',
            fontSize: compact ? 14 : 18,
          }}>
            {icon}
          </Box>
        )}
        <Typography
          variant="caption"
          sx={{
            fontSize: compact ? '0.45rem' : '0.6rem',
            color: '#6b7280',
            fontWeight: 500,
            letterSpacing: '0.2px',
            textTransform: 'uppercase',
            whiteSpace: 'nowrap',
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
          fontSize: compact ? '0.85rem' : '1.1rem',
          color: color,
          lineHeight: 1.1,
          whiteSpace: 'nowrap',
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