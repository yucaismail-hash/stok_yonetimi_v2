// frontend/src/components/common/AIRecommendationBadge.tsx
// Stokonomi Design System - AI Öneri Rozeti

import { Box, Chip, Tooltip, Typography, Paper, alpha } from '@mui/material';
import { 
  Psychology, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
  AutoAwesome
} from '@mui/icons-material';

export type AIRecommendationType = 
  | 'increase' 
  | 'decrease' 
  | 'maintain' 
  | 'investigate' 
  | 'urgent'
  | 'normal';

export interface AIRecommendationBadgeProps {
  /** Öneri tipi */
  type: AIRecommendationType;
  /** Güven skoru (0-1) */
  confidence?: number;
  /** Öneri metni */
  label?: string;
  /** Detaylı açıklama (tooltip için) */
  description?: string;
  /** Kompakt mod */
  compact?: boolean;
  /** Tıklama olayı */
  onClick?: () => void;
}

const typeConfig: Record<AIRecommendationType, {
  label: string;
  icon: React.ReactNode;
  color: 'success' | 'error' | 'warning' | 'info' | 'default';
  bgColor: string;
  textColor: string;
}> = {
  increase: {
    label: 'Artır',
    icon: <TrendingUp sx={{ fontSize: 14 }} />,
    color: 'error',
    bgColor: '#ffebee',
    textColor: '#d32f2f',
  },
  decrease: {
    label: 'Azalt',
    icon: <TrendingDown sx={{ fontSize: 14 }} />,
    color: 'success',
    bgColor: '#e8f5e9',
    textColor: '#2e7d32',
  },
  maintain: {
    label: 'Koru',
    icon: <CheckCircle sx={{ fontSize: 14 }} />,
    color: 'info',
    bgColor: '#e3f2fd',
    textColor: '#1976d2',
  },
  investigate: {
    label: 'İncele',
    icon: <Info sx={{ fontSize: 14 }} />,
    color: 'warning',
    bgColor: '#fff3e0',
    textColor: '#ed6c02',
  },
  urgent: {
    label: 'Acil',
    icon: <ErrorIcon sx={{ fontSize: 14 }} />,
    color: 'error',
    bgColor: '#ffebee',
    textColor: '#c62828',
  },
  normal: {
    label: 'Normal',
    icon: <CheckCircle sx={{ fontSize: 14 }} />,
    color: 'success',
    bgColor: '#e8f5e9',
    textColor: '#2e7d32',
  },
};

export default function AIRecommendationBadge({
  type,
  confidence = 0.5,
  label,
  description,
  compact = false,
  onClick,
}: AIRecommendationBadgeProps) {
  const config = typeConfig[type] || typeConfig.normal;
  const confidencePercent = Math.round(confidence * 100);

  const badgeContent = (
    <Chip
      icon={
        <Box sx={{ display: 'flex', alignItems: 'center', color: config.textColor }}>
          {config.icon}
        </Box>
      }
      label={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 600,
              fontSize: compact ? '0.55rem' : '0.6rem',
              color: config.textColor,
            }}
          >
            {label || config.label}
          </Typography>
          {!compact && (
            <Chip
              label={`%${confidencePercent}`}
              size="small"
              sx={{
                height: 14,
                fontSize: '0.4rem',
                fontWeight: 600,
                bgcolor: confidence > 0.7 ? '#e8f5e9' : confidence > 0.4 ? '#fff3e0' : '#ffebee',
                color: confidence > 0.7 ? '#2e7d32' : confidence > 0.4 ? '#ed6c02' : '#d32f2f',
                '& .MuiChip-label': { px: 0.5 },
              }}
            />
          )}
        </Box>
      }
      size="small"
      sx={{
        height: compact ? 22 : 26,
        bgcolor: config.bgColor,
        border: `1px solid ${alpha(config.textColor, 0.2)}`,
        borderRadius: 1.5,
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? {
          boxShadow: 1,
          transform: 'translateY(-1px)',
        } : {},
        transition: 'all 0.2s',
        '& .MuiChip-icon': {
          ml: 0.5,
          mr: 0,
          color: config.textColor,
        },
        '& .MuiChip-label': {
          px: compact ? 0.75 : 1,
        },
      }}
      onClick={onClick}
    />
  );

  if (description) {
    return (
      <Tooltip
        title={
          <Box sx={{ p: 1, maxWidth: 280 }}>
            <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79', display: 'block' }}>
              {label || config.label} Önerisi
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#374151', display: 'block', mt: 0.25 }}>
              {description}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block', mt: 0.25 }}>
              Güven: %{confidencePercent}
            </Typography>
          </Box>
        }
        arrow
        placement="top"
      >
        <Box>{badgeContent}</Box>
      </Tooltip>
    );
  }

  return badgeContent;
}