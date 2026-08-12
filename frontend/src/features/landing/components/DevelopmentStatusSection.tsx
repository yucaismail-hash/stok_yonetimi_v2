// src/features/landing/components/DevelopmentStatusSection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Chip,
} from '@mui/material';
import { alpha, Theme } from '@mui/material/styles';
import {
  Construction as ConstructionIcon,
  Rocket as RocketIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

const phases = [
  {
    icon: ConstructionIcon,
    phase: 'ŞİMDİ',
    title: 'Geliştirme ve Doğrulama',
    description:
      'Analiz, tahmin, simülasyon ve karar destek altyapısını geliştiriyor; sonuçları test ediyoruz.',
    status: 'AKTİF',
    statusColor: 'primary' as const,
    fullWidth: true,
  },
  {
    icon: RocketIcon,
    phase: 'SONRAKİ',
    title: 'Beta',
    description:
      'Temel deneyim yeterli olgunluğa ulaştığında kontrollü beta kullanımına geçmeyi planlıyoruz.',
    status: 'PLANLANIYOR',
    statusColor: 'default' as const,
    fullWidth: false,
  },
  {
    icon: TrendingUpIcon,
    phase: 'ARDINDAN',
    title: 'Erken Erişim',
    description:
      'Gerçek kullanıcı geri bildirimleriyle platformu kademeli olarak geliştirmeye devam edeceğiz.',
    status: 'PLANLANIYOR',
    statusColor: 'default' as const,
    fullWidth: false,
  },
];

export function DevelopmentStatusSection() {
  return (
    <Box
      id="gelismeler"
      sx={{
        py: { xs: 8, md: 10 },
        bgcolor: (theme) => theme.palette.background.paper,
      }}
    >
      <Container maxWidth="xl">
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 760,
            mx: 'auto',
            mb: { xs: 6, md: 7 },
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
            GELİŞTİRME DURUMU
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
            Stokonomi
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
              geliştirme aşamasında.
            </Box>
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
            Stokonomi'yi gerçek stok yönetimi problemlerini
            çözebilecek güvenilir bir karar destek platformu
            haline getirmek için geliştiriyor ve doğruluyoruz.
          </Typography>
        </Box>

        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 640,
            mx: 'auto',
            mb: { xs: 5, sm: 5, md: 6 },
            p: { xs: 2.5, sm: 3, md: 3.5 },
            borderRadius: (theme) => theme.shape.borderRadius,
            border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: (theme) => theme.palette.text.primary,
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              mb: 1,
            }}
          >
            "Ürün hazırmış gibi davranmıyoruz."
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              fontSize: '0.9rem',
              lineHeight: 1.7,
              maxWidth: 540,
              mx: 'auto',
            }}
          >
            Analiz altyapısı, karar destek mekanizmaları ve kullanıcı
            deneyimi yeterli olgunluğa ulaşmadan Stokonomi'yi
            kullanıma açmayı planlamıyoruz.
          </Typography>
        </Box>

        {/* Desktop: 3 columns */}
        <Box sx={{ display: { xs: 'none', md: 'block' } }}>
          <Grid container spacing={3}>
            {phases.map((phase, index) => (
              <Grid size={{ xs: 12, md: 4 }} key={index}>
                <Paper
                  elevation={0}
                  sx={{
                    p: { xs: 3, md: 4 },
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: (theme) => theme.shape.borderRadius,
                    border: (theme) =>
                      phase.statusColor === 'primary'
                        ? `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                        : `1px solid ${theme.palette.divider}`,
                    bgcolor: (theme) =>
                      phase.statusColor === 'primary'
                        ? alpha(theme.palette.primary.main, 0.02)
                        : theme.palette.background.paper,
                    transition: 'all 0.25s ease-in-out',
                    '&:hover': {
                      borderColor: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
                      boxShadow: (theme) =>
                        `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
                      fontWeight: 600,
                      fontSize: '0.6rem',
                      letterSpacing: '0.8px',
                      textTransform: 'uppercase',
                      mb: 1.5,
                    }}
                  >
                    {phase.phase}
                  </Typography>

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
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        bgcolor: (theme) =>
                          phase.statusColor === 'primary'
                            ? alpha(theme.palette.primary.main, 0.08)
                            : alpha(theme.palette.text.secondary, 0.06),
                        color: (theme) =>
                          phase.statusColor === 'primary'
                            ? theme.palette.primary.main
                            : theme.palette.text.secondary,
                        flexShrink: 0,
                      }}
                    >
                      <phase.icon sx={{ fontSize: 22 }} />
                    </Box>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 600,
                        color: (theme) => theme.palette.text.primary,
                        fontSize: '1rem',
                        lineHeight: 1.3,
                      }}
                    >
                      {phase.title}
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
                    {phase.description}
                  </Typography>

                  <Chip
                    label={phase.status}
                    size="small"
                    sx={{
                      alignSelf: 'flex-start',
                      bgcolor: (theme) =>
                        phase.statusColor === 'primary'
                          ? alpha(theme.palette.primary.main, 0.08)
                          : alpha(theme.palette.text.secondary, 0.06),
                      color: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
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
        </Box>

        {/* Tablet: 2+1 layout */}
        <Box sx={{ display: { xs: 'none', sm: 'block', md: 'none' } }}>
          <Grid container spacing={3}>
            {/* First card - full width */}
            <Grid size={{ xs: 12 }}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, sm: 3 },
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': {
                    borderColor: (theme) => theme.palette.primary.main,
                    boxShadow: (theme) =>
                      `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.primary.main,
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    letterSpacing: '0.8px',
                    textTransform: 'uppercase',
                    mb: 1.5,
                  }}
                >
                  {phases[0].phase}
                </Typography>

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
                      width: 40,
                      height: 40,
                      borderRadius: 2,
                      bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                      color: (theme) => theme.palette.primary.main,
                      flexShrink: 0,
                    }}
                  >
                    <ConstructionIcon sx={{ fontSize: 22 }} />
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '1rem',
                      lineHeight: 1.3,
                    }}
                  >
                    {phases[0].title}
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
                  {phases[0].description}
                </Typography>

                <Chip
                  label={phases[0].status}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
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
              </Paper>
            </Grid>

            {/* Second and third cards - 2 columns */}
            <Grid size={{ xs: 6 }}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, sm: 3 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  border: (theme) => `1px solid ${theme.palette.divider}`,
                  bgcolor: (theme) => theme.palette.background.paper,
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': {
                    borderColor: (theme) => theme.palette.text.secondary,
                    boxShadow: (theme) =>
                      `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    letterSpacing: '0.8px',
                    textTransform: 'uppercase',
                    mb: 1.5,
                  }}
                >
                  {phases[1].phase}
                </Typography>

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
                      width: 40,
                      height: 40,
                      borderRadius: 2,
                      bgcolor: (theme) => alpha(theme.palette.text.secondary, 0.06),
                      color: (theme) => theme.palette.text.secondary,
                      flexShrink: 0,
                    }}
                  >
                    <RocketIcon sx={{ fontSize: 22 }} />
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '1rem',
                      lineHeight: 1.3,
                    }}
                  >
                    {phases[1].title}
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
                  {phases[1].description}
                </Typography>

                <Chip
                  label={phases[1].status}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: (theme) => alpha(theme.palette.text.secondary, 0.06),
                    color: (theme) => theme.palette.text.secondary,
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

            <Grid size={{ xs: 6 }}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, sm: 3 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  border: (theme) => `1px solid ${theme.palette.divider}`,
                  bgcolor: (theme) => theme.palette.background.paper,
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': {
                    borderColor: (theme) => theme.palette.text.secondary,
                    boxShadow: (theme) =>
                      `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    fontWeight: 600,
                    fontSize: '0.6rem',
                    letterSpacing: '0.8px',
                    textTransform: 'uppercase',
                    mb: 1.5,
                  }}
                >
                  {phases[2].phase}
                </Typography>

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
                      width: 40,
                      height: 40,
                      borderRadius: 2,
                      bgcolor: (theme) => alpha(theme.palette.text.secondary, 0.06),
                      color: (theme) => theme.palette.text.secondary,
                      flexShrink: 0,
                    }}
                  >
                    <TrendingUpIcon sx={{ fontSize: 22 }} />
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '1rem',
                      lineHeight: 1.3,
                    }}
                  >
                    {phases[2].title}
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
                  {phases[2].description}
                </Typography>

                <Chip
                  label={phases[2].status}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: (theme) => alpha(theme.palette.text.secondary, 0.06),
                    color: (theme) => theme.palette.text.secondary,
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
          </Grid>
        </Box>

        {/* Mobile: single column - keep as is */}
        <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
          <Grid container spacing={2.5}>
            {phases.map((phase, index) => (
              <Grid size={{ xs: 12 }} key={index}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2.5,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: (theme) => theme.shape.borderRadius,
                    border: (theme) =>
                      phase.statusColor === 'primary'
                        ? `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                        : `1px solid ${theme.palette.divider}`,
                    bgcolor: (theme) =>
                      phase.statusColor === 'primary'
                        ? alpha(theme.palette.primary.main, 0.02)
                        : theme.palette.background.paper,
                    transition: 'all 0.25s ease-in-out',
                    '&:hover': {
                      borderColor: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
                      boxShadow: (theme) =>
                        `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`,
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
                      fontWeight: 600,
                      fontSize: '0.6rem',
                      letterSpacing: '0.8px',
                      textTransform: 'uppercase',
                      mb: 1.5,
                    }}
                  >
                    {phase.phase}
                  </Typography>

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
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        bgcolor: (theme) =>
                          phase.statusColor === 'primary'
                            ? alpha(theme.palette.primary.main, 0.08)
                            : alpha(theme.palette.text.secondary, 0.06),
                        color: (theme) =>
                          phase.statusColor === 'primary'
                            ? theme.palette.primary.main
                            : theme.palette.text.secondary,
                        flexShrink: 0,
                      }}
                    >
                      <phase.icon sx={{ fontSize: 22 }} />
                    </Box>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 600,
                        color: (theme) => theme.palette.text.primary,
                        fontSize: '1rem',
                        lineHeight: 1.3,
                      }}
                    >
                      {phase.title}
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
                    {phase.description}
                  </Typography>

                  <Chip
                    label={phase.status}
                    size="small"
                    sx={{
                      alignSelf: 'flex-start',
                      bgcolor: (theme) =>
                        phase.statusColor === 'primary'
                          ? alpha(theme.palette.primary.main, 0.08)
                          : alpha(theme.palette.text.secondary, 0.06),
                      color: (theme) =>
                        phase.statusColor === 'primary'
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
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
        </Box>

        <Box
          sx={{
            mt: { xs: 6, md: 7 },
            textAlign: 'center',
            maxWidth: 640,
            mx: 'auto',
            pt: { xs: 4, md: 5 },
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: (theme) => theme.palette.text.primary,
              mb: 1,
              fontSize: { xs: '1.1rem', md: '1.25rem' },
            }}
          >
            Önceliğimiz hız değil, güvenilirlik.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Stokonomi'nin ürettiği sonuçların anlaşılabilir,
            sınanabilir ve karar verici için gerçekten faydalı
            olmasını hedefliyoruz.
          </Typography>

          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 3,
              color: (theme) => theme.palette.text.secondary,
              fontSize: '0.8rem',
              opacity: 0.6,
            }}
          >
            Gelişmeleri paylaşmaya devam edeceğiz.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default DevelopmentStatusSection;