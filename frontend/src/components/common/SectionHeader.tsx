// frontend/src/components/common/SectionHeader.tsx
// Stokonomi Design System - Bölüm Başlığı (Reusable)

import { Box, Typography, Chip, Stack, SxProps, Theme } from '@mui/material';
import { ReactNode } from 'react';

// ✅ interface'i export et
export interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  badge?: string;
  badgeColor?: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  icon?: ReactNode;
  compact?: boolean;
  sx?: SxProps<Theme>;
  id?: string;
}

export default function SectionHeader({
  title,
  subtitle,
  actions,
  badge,
  badgeColor = 'default',
  icon,
  compact = false,
  sx,
  id,
}: SectionHeaderProps) {
  return (
    <Box
      id={id}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 1,
        mb: compact ? 1.25 : 1.5,
        ...sx,
      }}
    >
      {/* Sol: Başlık */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
        {icon && (
          <Box sx={{ color: '#1f4e79', display: 'flex', alignItems: 'center' }}>
            {icon}
          </Box>
        )}
        
        <Box>
          <Typography
            variant={compact ? 'subtitle2' : 'h6'}
            sx={{
              fontWeight: 700,
              color: '#1f4e79',
              fontSize: compact ? '0.85rem' : '1rem',
              lineHeight: 1.2,
            }}
          >
            {title}
          </Typography>
          
          {subtitle && (
            <Typography
              variant="caption"
              sx={{
                color: '#6b7280',
                fontSize: '0.7rem',
                display: 'block',
                mt: 0.25,
              }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>

        {badge && (
          <Chip
            label={badge}
            size="small"
            color={badgeColor}
            sx={{
              height: 20,
              fontSize: '0.55rem',
              fontWeight: 600,
            }}
          />
        )}
      </Box>

      {/* Sağ: Aksiyonlar */}
      {actions && (
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', flexWrap: 'wrap' }}  // ✅ alignItems sx içine taşındı
        >
          {actions}
        </Stack>
      )}
    </Box>
  );
}