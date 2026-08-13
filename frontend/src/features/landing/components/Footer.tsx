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
import { alpha } from '@mui/material/styles';
import { Logo } from '../../../shared/ui';

const footerLinks = [
  { label: 'Yaklaşım', href: '#yaklasim' },
  { label: 'Akademi', href: '#akademi' },
  { label: 'Gelişmeleri Takip Et', href: '#gelismeler' },
];

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
              Yapay zekâ destekli stok optimizasyonu, talep tahmini
              ve karar desteği platformu.
            </Typography>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={1.5}>
              {footerLinks.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  underline="none"
                  sx={{
                    color: (theme) => alpha(theme.palette.common.white, 0.7),
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    transition: 'color 0.2s',
                    '&:hover': {
                      color: (theme) => theme.palette.common.white,
                    },
                  }}
                >
                  {item.label}
                </Link>
              ))}
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
            <Link
              href="#"
              underline="none"
              sx={{
                color: (theme) => alpha(theme.palette.common.white, 0.6),
                fontSize: '0.875rem',
                transition: 'color 0.2s',
                pointerEvents: 'none',
                opacity: 0.5,
                '&:hover': {
                  color: (theme) => theme.palette.common.white,
                },
              }}
            >
              LinkedIn
            </Link>
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