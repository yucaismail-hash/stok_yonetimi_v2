// src/components/landing/Footer.tsx
import React from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Stack,
  Divider,
} from '@mui/material';
import { Logo } from '../ui';

const footerSections = [
  {
    title: 'Ürün',
    items: ['Özellikler', 'Fiyatlandırma', 'Dökümantasyon', 'API'],
  },
  {
    title: 'Şirket',
    items: ['Hakkımızda', 'Blog', 'Kariyer', 'İletişim'],
  },
  {
    title: 'Kaynaklar',
    items: ['Yardım Merkezi', 'Şartlar', 'Gizlilik', 'KVKK'],
  },
];

export function Footer() {
  return (
    <Box sx={{ bgcolor: '#0F172A', py: 6 }}>
      <Container maxWidth="xl">
        <Grid container spacing={4}>
          {/* Logo ve Açıklama */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Logo variant="light" size="medium" />
            <Typography
              variant="body2"
              sx={{
                color: '#64748B',
                mt: 2,
                maxWidth: 300,
                lineHeight: 1.7,
              }}
            >
              AI destekli stok optimizasyon ve karar destek platformu.
            </Typography>
          </Grid>

          {/* Linkler */}
          {footerSections.map((section) => (
            <Grid size={{ xs: 6, md: 2 }} key={section.title}>
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  color: 'white',
                  mb: 2,
                }}
              >
                {section.title}
              </Typography>
              <Stack spacing={1}>
                {section.items.map((item) => (
                  <Typography
                    key={item}
                    variant="body2"
                    sx={{
                      color: '#64748B',
                      cursor: 'pointer',
                      '&:hover': { color: 'white' },
                      transition: 'color 0.2s',
                    }}
                  >
                    {item}
                  </Typography>
                ))}
              </Stack>
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ bgcolor: 'rgba(255,255,255,0.06)', my: 4 }} />

        <Typography
          variant="body2"
          sx={{
            color: '#475569',
            textAlign: 'center',
          }}
        >
          © 2026 Stokonomi. Tüm hakları saklıdır.
        </Typography>
      </Container>
    </Box>
  );
}

export default Footer;