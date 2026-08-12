// src/features/landing/components/ProblemSection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  Timeline as TimelineIcon,
  LocalShipping as LocalShippingIcon,
} from '@mui/icons-material';

const problems = [
  {
    icon: InventoryIcon,
    title: 'Fazla Stok',
    description:
      'İhtiyacın üzerinde stok; sermayeyi bağlar, depolama maliyetini artırır ve eskime riskini büyütür.',
  },
  {
    icon: WarningIcon,
    title: 'Stok Yetersizliği',
    description:
      'Yetersiz stok; satış kaybına, üretim kesintisine ve hizmet seviyesinin düşmesine neden olabilir.',
  },
  {
    icon: TimelineIcon,
    title: 'Tahmin Belirsizliği',
    description:
      'Talep geçmişteki davranışı her zaman tekrar etmez. Trend, dönemsel hareketler ve beklenmeyen değişimler tahmini zorlaştırır.',
  },
  {
    icon: LocalShippingIcon,
    title: 'Tedarik Belirsizliği',
    description:
      'Termin süreleri ve tedarikçi performansı değiştikçe doğru zamanda doğru miktarı bulundurmak zorlaşır.',
  },
];

export function ProblemSection() {
  return (
    <Box
      id="problem"
      sx={{
        py: { xs: 8, md: 12 },
        bgcolor: (theme) => theme.palette.background.default,
      }}
    >
      <Container maxWidth="xl">
        {/* Section Header */}
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 720,
            mx: 'auto',
            mb: { xs: 6, md: 8 },
          }}
        >
          <Typography
            variant="overline"
            sx={{
              color: (theme) => theme.palette.primary.main,
              fontWeight: 600,
              letterSpacing: '0.5px',
              display: 'block',
              mb: 1,
            }}
          >
            PROBLEM
          </Typography>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              color: (theme) => theme.palette.text.primary,
              mb: 2,
              fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },
            }}
          >
            Stok probleminin merkezinde
            <br />
            <Box
              component="span"
              sx={{
                background: (theme) =>
                  `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              belirsizlik var.
            </Box>
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              maxWidth: 640,
              mx: 'auto',
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Talep, tedarik süresi ve operasyon koşulları sürekli değişirken,
            stok kararlarını yalnızca geçmiş ortalamalara göre vermek
            işletmeleri iki temel risk arasında bırakır:
            fazla stok ve stok yetersizliği.
          </Typography>
        </Box>

        {/* Problem Cards */}
        <Grid container spacing={3}>
          {problems.map((problem, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  height: '100%',
                  minHeight: 200,
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  border: (theme) => `1px solid ${theme.palette.divider}`,
                  bgcolor: (theme) => theme.palette.background.paper,
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': {
                    borderColor: (theme) => theme.palette.primary.main,
                    boxShadow: (theme) =>
                      `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                    color: (theme) => theme.palette.primary.main,
                    mb: 2,
                    flexShrink: 0,
                  }}
                >
                  <problem.icon sx={{ fontSize: 24 }} />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    mb: 1,
                    fontSize: '1rem',
                  }}
                >
                  {problem.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    lineHeight: 1.6,
                    fontSize: '0.875rem',
                    flex: 1,
                  }}
                >
                  {problem.description}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        {/* Bottom Message */}
        <Box
          sx={{
            mt: { xs: 6, md: 8 },
            textAlign: 'center',
            maxWidth: 640,
            mx: 'auto',
            pt: { xs: 4, md: 6 },
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            variant="h5"
            sx={{
              fontWeight: 600,
              color: (theme) => theme.palette.text.primary,
              mb: 1.5,
              fontSize: { xs: '1.25rem', md: '1.5rem' },
            }}
          >
            Bu nedenle stok yönetimi yalnızca bir hesaplama problemi değildir.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Belirsizliği ölçmek, senaryoları sınamak ve kararları
            veriye dayandırmak gerekir.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default ProblemSection;