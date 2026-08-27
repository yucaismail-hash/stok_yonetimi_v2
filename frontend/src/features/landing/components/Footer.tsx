// src/features/landing/components/Footer.tsx
import React from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Stack,
  Divider,
  Link,
} from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';
import { Logo } from '../../../shared/ui';

type FooterLink = { label: string; href?: string; to?: string };

const footerLinks: FooterLink[] = [
  { label: 'Yaklaşım', href: '#yaklasim' },
  { label: 'Akademi', to: '/akademi' },
  { label: 'Gelişmeleri Takip Et', href: '#gelismeler' },
];

const footerLinkSx = {
  color: (theme: Theme) => alpha(theme.palette.common.white, 0.7),
  fontSize: '0.875rem',
  fontWeight: 500,
  transition: 'color 0.2s',
  '&:hover': { color: (theme: Theme) => theme.palette.common.white },
};

export function Footer() {
  return (
    <Box
      sx={{
        bgcolor: '#0A0F1A',
        py: { xs: 6, md: 7 },
        borderTop: (theme) =>
          `1px solid ${alpha(theme.palette.common.white, 0.06)}`,
      }}
    >
      <Container maxWidth="xl">
        <Grid container spacing={{ xs: 4, md: 6 }}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Box
              sx={{
                width: { xs: 220, md: 260 },
                '& img': {
                  width: '100%',
                  height: 'auto',
                },
              }}
            >
              <Logo variant="light" size="large" />
            </Box>
            <Typography
              variant="body2"
              sx={{
                color: (theme) => alpha(theme.palette.common.white, 0.6),
                mt: 2,
                maxWidth: 360,
                lineHeight: 1.7,
              }}
            >
              Tahmin, doğrulama ve karar desteğini birlikte değerlendirmek
              için geliştirilen stok karar sistemi yaklaşımı.
            </Typography>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={1.5}>
              {footerLinks.map((item) => {
                return item.to ? (
                  <Link key={item.label} component={RouterLink} to={item.to} underline="none" sx={footerLinkSx}>{item.label}</Link>
                ) : (
                  <Link key={item.label} href={item.href} underline="none" sx={footerLinkSx}>{item.label}</Link>
                );
              })}
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, md: 3 }}>
            <Typography
              variant="caption"
              sx={{
                color: (theme) => alpha(theme.palette.common.white, 0.4),
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: 600,
                display: 'block',
                mb: 1.5,
              }}
            >
              Bizi Takip Edin
            </Typography>
            <Typography
              sx={{
                color: (theme) => alpha(theme.palette.common.white, 0.6),
                fontSize: '0.875rem',
                opacity: 0.5,
              }}
            >
              LinkedIn
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: (theme) => alpha(theme.palette.common.white, 0.3),
                display: 'block',
                mt: 0.5,
                fontSize: '0.65rem',
              }}
            >
              (Bağlantı yakında eklenecek)
            </Typography>
          </Grid>
        </Grid>

        <Divider
          sx={{
            bgcolor: (theme) => alpha(theme.palette.common.white, 0.06),
            my: { xs: 4, md: 5 },
          }}
        />

        <Typography
          variant="body2"
          sx={{
            color: (theme) => alpha(theme.palette.common.white, 0.3),
            textAlign: 'center',
            fontSize: '0.75rem',
          }}
        >
          © 2026 Stokonomi. Tüm hakları saklıdır.
        </Typography>
      </Container>
    </Box>
  );
}

export default Footer;
