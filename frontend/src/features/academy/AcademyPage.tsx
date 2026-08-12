// src/features/academy/AcademyPage.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Chip,
  Button,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import {
  School as SchoolIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { Logo } from '../../shared/ui';

const topics = [
  {
    icon: SchoolIcon,
    category: 'Temel Kavramlar',
    title: 'Stok Yönetimi Nedir?',
    description:
      'Stok yönetiminin temel amaçlarını, maliyet ve hizmet seviyesi dengesiyle birlikte ele alan giriş içeriği.',
    status: 'Yayında',
    slug: 'stok-yonetimi-nedir',
    published: true,
  },
  {
    icon: SecurityIcon,
    category: 'Emniyet Stoku',
    title: 'Emniyet Stoku Nedir?',
    description:
      'Talep ve tedarik belirsizliğine karşı emniyet stokunun neden gerekli olduğunu açıklayan içerik.',
    status: 'Hazırlanıyor',
    slug: 'emniyet-stoku-nedir',
    published: false,
  },
  {
    icon: TimelineIcon,
    category: 'Operasyon',
    title: 'Yeniden Sipariş Noktası (ROP)',
    description:
      'Ne zaman sipariş verilmesi gerektiğini belirleyen temel yaklaşımı örneklerle inceleyen içerik.',
    status: 'Hazırlanıyor',
    slug: 'yeniden-siparis-noktasi-rop-nedir',
    published: false,
  },
  {
    icon: AnalyticsIcon,
    category: 'Tahmin',
    title: 'Talep Tahmini Nedir?',
    description:
      'Geçmiş veriden gelecekteki talebi tahmin etmenin temel mantığını ve sınırlarını keşfeden içerik.',
    status: 'Hazırlanıyor',
    slug: 'talep-tahmini-nedir',
    published: false,
  },
];

export default function AcademyPage() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: (theme) => theme.palette.background.default,
        py: { xs: 4, md: 6 },
      }}
    >
      <Container maxWidth="xl">
        {/* Navigation */}
        <Box sx={{ mb: 4 }}>
          <Button
            component={Link}
            to="/"
            startIcon={<ArrowBackIcon />}
            sx={{
              color: (theme) => theme.palette.text.secondary,
              fontWeight: 500,
              textTransform: 'none',
              '&:hover': {
                color: (theme) => theme.palette.text.primary,
                bgcolor: 'transparent',
              },
            }}
          >
            Ana Sayfa
          </Button>
        </Box>

        {/* Header */}
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 760,
            mx: 'auto',
            mb: { xs: 6, md: 8 },
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <Logo size="medium" />
          </Box>

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
            Stok yönetimi, talep tahmini, emniyet stoku ve karar destek
            süreçlerini açık, uygulanabilir ve örneklerle ele alan
            Stokonomi bilgi merkezi.
          </Typography>
        </Box>

        {/* Content Cards */}
        <Grid container spacing={3}>
          {topics.map((topic, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, md: 3.5 },
                  height: '100%',
                  minHeight: 220,
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  border: (theme) => `1px solid ${theme.palette.divider}`,
                  bgcolor: (theme) => theme.palette.background.paper,
                  transition: 'all 0.25s ease-in-out',
                  cursor: topic.published ? 'pointer' : 'default',
                  '&:hover': {
                    borderColor: topic.published
                      ? (theme) => theme.palette.primary.main
                      : (theme) => theme.palette.divider,
                    boxShadow: topic.published
                      ? (theme) =>
                          `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`
                      : 'none',
                    transform: topic.published ? 'translateY(-2px)' : 'none',
                  },
                }}
                onClick={() => {
                  if (topic.published && topic.slug) {
                    window.location.href = `/akademi/${topic.slug}`;
                  }
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
                    mb: 2,
                  }}
                >
                  {topic.description}
                </Typography>

                <Chip
                  label={topic.status}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: topic.published
                      ? (theme) => alpha(theme.palette.success.main, 0.08)
                      : (theme) => alpha(theme.palette.text.secondary, 0.06),
                    color: topic.published
                      ? (theme) => theme.palette.success.main
                      : (theme) => theme.palette.text.secondary,
                    fontWeight: 500,
                    fontSize: '0.65rem',
                    borderRadius: 2,
                    height: 24,
                    '& .MuiChip-label': {
                      px: 1.5,
                    },
                  }}
                />
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}