// frontend/src/components/common/PageLayout.tsx
// Stokonomi Design System - Sayfa Layout (Tüm modüller için ortak)

import { Box, Container, SxProps, Theme, Typography } from '@mui/material';
import { ReactNode } from 'react';

interface PageLayoutProps {
  /** Sayfa içeriği */
  children: ReactNode;
  /** Hero bileşeni (opsiyonel) */
  hero?: ReactNode;
  /** Sayfa başlığı (hero yoksa kullanılır) */
  title?: string;
  /** Maksimum genişlik */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  /** Arka plan rengi */
  bgcolor?: string;
  /** Padding */
  padding?: number | string;
  /** Ek CSS */
  sx?: SxProps<Theme>;
}

export default function PageLayout({
  children,
  hero,
  title,
  maxWidth = 'xl',
  bgcolor = '#f5f8fc',
  padding = 3,
  sx,
}: PageLayoutProps) {
  return (
    <Box
      sx={{
        bgcolor: bgcolor,
        minHeight: '100vh',
        p: padding,
        mx: -3,
        mt: -3,
        ...sx,
      }}
    >
      <Container maxWidth={maxWidth} sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
        {/* Hero Alanı */}
        {hero && (
          <Box sx={{ mb: 2 }}>
            {hero}
          </Box>
        )}

        {/* Başlık (hero yoksa) */}
        {!hero && title && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#1f4e79' }}>
              {title}
            </Typography>
          </Box>
        )}

        {/* İçerik */}
        <Box>
          {children}
        </Box>
      </Container>
    </Box>
  );
}