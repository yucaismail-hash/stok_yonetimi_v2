// src/features/landing/components/AcademySection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Chip,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  School as SchoolIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

const topics = [
  {
    icon: SchoolIcon,
    category: 'Temel Kavramlar',
    title: 'Stok Yönetimi Nedir?',
    description:
      'Stok yönetiminin temel amaçlarını, maliyet ve hizmet seviyesi dengesiyle birlikte ele alın.',
  },
  {
    icon: SecurityIcon,
    category: 'Emniyet Stoku',
    title: 'Emniyet Stoku Nedir?',
    description:
      'Talep ve tedarik belirsizliğine karşı emniyet stokunun neden gerekli olduğunu öğrenin.',
  },
  {
    icon: TimelineIcon,
    category: 'Operasyon',
    title: 'Yeniden Sipariş Noktası (ROP)',
    description:
      'Ne zaman sipariş verilmesi gerektiğini belirleyen temel yaklaşımı örneklerle inceleyin.',
  },
  {
    icon: AnalyticsIcon,
    category: 'Tahmin',
    title: 'Talep Tahmini Nedir?',
    description:
      'Geçmiş veriden gelecekteki talebi tahmin etmenin temel mantığını ve sınırlarını keşfedin.',
  },
];

export function AcademySection() {
  return (
    <Box
      id="akademi"
      sx={{
        py: { xs: 8, md: 10 },
        bgcolor: (theme) => theme.palette.background.default,
      }}
    >
      <Container maxWidth="xl">
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 760,
            mx: 'auto',
            mb: { xs: 6, md: 6 },
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
            STOKONOMİ AKADEMİ
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
            Stok yönetimini
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
              daha anlaşılır
            </Box>
            <br />
            hale getiriyoruz.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              maxWidth: 660,
              mx: 'auto',
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Stokonomi Akademi; stok yönetimi, talep tahmini,
            emniyet stoku ve karar destek süreçlerini
            açık, uygulanabilir ve örneklerle anlatan bilgi merkezidir.
          </Typography>

          <Box
            sx={{
              mt: 3,
              pt: 3,
              borderTop: (theme) => `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                color: (theme) => theme.palette.text.primary,
                fontSize: '1rem',
                mb: 0.5,
              }}
            >
              Bilgi, daha iyi kararların başlangıcıdır.
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: '0.875rem',
                lineHeight: 1.6,
                maxWidth: 580,
                mx: 'auto',
              }}
            >
              Temel kavramlardan ileri analiz yöntemlerine kadar,
              stok yönetimini sahadaki gerçek sorular üzerinden ele alıyoruz.
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {topics.map((topic, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 6, lg: 3 }} key={index}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, md: 3.5 },
                  height: '100%',
                  minHeight: 210,
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
                <Chip
                  label={topic.category}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    mb: 2,
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
                    color: (theme) => theme.palette.primary.main,
                    fontWeight: 500,
                    fontSize: '0.65rem',
                    borderRadius: 2,
                    height: 24,
                    '& .MuiChip-label': {
                      px: 1.5,
                    },
                  }}
                />

                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    mb: 1.5,
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 36,
                      height: 36,
                      borderRadius: 2,
                      bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
                      color: (theme) => theme.palette.primary.main,
                      flexShrink: 0,
                    }}
                  >
                    <topic.icon sx={{ fontSize: 20 }} />
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '0.95rem',
                      lineHeight: 1.3,
                    }}
                  >
                    {topic.title}
                  </Typography>
                </Box>

                <Typography
                  variant="body2"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    lineHeight: 1.7,
                    fontSize: '0.875rem',
                    flex: 1,
                  }}
                >
                  {topic.description}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box
          sx={{
            mt: { xs: 6, md: 6 },
            textAlign: 'center',
          }}
        >
          <Chip
            label="İlk içerikler hazırlanıyor"
            sx={{
              bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
              color: (theme) => theme.palette.text.secondary,
              fontWeight: 500,
              fontSize: '0.8rem',
              borderRadius: (theme) => theme.shape.borderRadius,
              height: 36,
              '& .MuiChip-label': {
                px: 2.5,
              },
            }}
          />
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 1.5,
              color: (theme) => theme.palette.text.secondary,
              fontSize: '0.75rem',
              opacity: 0.6,
            }}
          >
            Akademi içerikleri yakında yayında
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default AcademySection;