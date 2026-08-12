// src/features/landing/components/ApproachSection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Stack,
  Divider,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  Storage as StorageIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  Loop as LoopIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

const steps = [
  {
    number: '01',
    icon: StorageIcon,
    title: 'Veri',
    description: 'Mevcut işletme verilerini analize hazırlar.',
  },
  {
    number: '02',
    icon: AnalyticsIcon,
    title: 'Analiz',
    description: 'Talep ve stok davranışındaki örüntüleri inceler.',
  },
  {
    number: '03',
    icon: TimelineIcon,
    title: 'Tahmin',
    description: 'Gelecekteki olası talebi yöntemlerle tahmin eder.',
  },
  {
    number: '04',
    icon: LoopIcon,
    title: 'Simülasyon',
    description: 'Farklı koşul ve senaryoların etkisini sınar.',
  },
  {
    number: '05',
    icon: PsychologyIcon,
    title: 'Doğrulama',
    description: 'Tahmin ve kararların geçmiş veride nasıl sonuç verdiğini test eder.',
  },
  {
    number: '06',
    icon: CheckCircleIcon,
    title: 'Karar Desteği',
    description: 'Elde edilen kanıtları karar verici için anlaşılır hale getirir.',
  },
];

export function ApproachSection() {
  return (
    <Box
      id="yaklasim"
      sx={{
        py: { xs: 8, md: 12 },
        bgcolor: (theme) => theme.palette.background.paper,
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
            STOKONOMİ YAKLAŞIMI
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
            Belirsizliği
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
              karar desteğine
            </Box>
            <br />
            dönüştürüyoruz.
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
            Stokonomi tek bir hesaplama ya da tahmin üretmek yerine,
            veriyi analizden doğrulamaya uzanan bütünsel bir süreç içinde ele alır.
          </Typography>
        </Box>

        {/* Steps - Desktop: Horizontal Timeline */}
        <Box sx={{ display: { xs: 'none', md: 'block' } }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(6, 1fr)',
              gap: 2,
              position: 'relative',
            }}
          >
            {/* Connector Line - centered on icons */}
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '8.33%',
                right: '8.33%',
                height: 2,
                transform: 'translateY(-50%)',
                bgcolor: (theme) => theme.palette.divider,
                zIndex: 0,
              }}
            />

            {steps.map((step) => (
              <Box
                key={step.number}
                sx={{
                  position: 'relative',
                  zIndex: 1,
                  textAlign: 'center',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 56,
                    height: 56,
                    borderRadius: '50%',
                    mx: 'auto',
                    mb: 2,
                    bgcolor: (theme) => theme.palette.background.paper,
                    color: (theme) => theme.palette.primary.main,
                    border: (theme) =>
                      `2px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                    position: 'relative',
                    zIndex: 2,
                  }}
                >
                  <step.icon sx={{ fontSize: 24 }} />
                </Box>
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    color: (theme) => theme.palette.primary.main,
                    fontWeight: 600,
                    fontSize: '0.65rem',
                    letterSpacing: '0.5px',
                    mb: 0.5,
                  }}
                >
                  {step.number}
                </Typography>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: '0.875rem',
                    mb: 0.5,
                  }}
                >
                  {step.title}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    fontSize: '0.7rem',
                    lineHeight: 1.5,
                    display: 'block',
                    maxWidth: 140,
                    mx: 'auto',
                  }}
                >
                  {step.description}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Steps - Tablet: 3+2+1 or 3+3 */}
        <Box sx={{ display: { xs: 'none', sm: 'block', md: 'none' } }}>
          <Grid container spacing={4}>
            {steps.map((step, index) => (
              <Grid size={{ xs: 6 }} key={step.number}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      mb: 1.5,
                      bgcolor: (theme) =>
                        index % 2 === 0
                          ? alpha(theme.palette.primary.main, 0.08)
                          : alpha(theme.palette.primary.main, 0.04),
                      color: (theme) => theme.palette.primary.main,
                      border: (theme) =>
                        `2px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                    }}
                  >
                    <step.icon sx={{ fontSize: 22 }} />
                  </Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: (theme) => theme.palette.primary.main,
                      fontWeight: 600,
                      fontSize: '0.6rem',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {step.number}
                  </Typography>
                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '0.875rem',
                      mt: 0.5,
                    }}
                  >
                    {step.title}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: (theme) => theme.palette.text.secondary,
                      fontSize: '0.7rem',
                      lineHeight: 1.5,
                      maxWidth: 180,
                    }}
                  >
                    {step.description}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Steps - Mobile: Vertical */}
        <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
          <Stack spacing={3}>
            {steps.map((step, index) => (
              <Box
                key={step.number}
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 2,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 44,
                      height: 44,
                      borderRadius: '50%',
                      bgcolor: (theme) =>
                        index % 2 === 0
                          ? alpha(theme.palette.primary.main, 0.08)
                          : alpha(theme.palette.primary.main, 0.04),
                      color: (theme) => theme.palette.primary.main,
                      border: (theme) =>
                        `2px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                    }}
                  >
                    <step.icon sx={{ fontSize: 20 }} />
                  </Box>
                  {index < steps.length - 1 && (
                    <Box
                      sx={{
                        width: 2,
                        height: 24,
                        bgcolor: (theme) => theme.palette.divider,
                        mt: 1,
                      }}
                    />
                  )}
                </Box>
                <Box sx={{ pt: 0.5 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: (theme) => theme.palette.primary.main,
                      fontWeight: 600,
                      fontSize: '0.6rem',
                      letterSpacing: '0.5px',
                      display: 'block',
                    }}
                  >
                    {step.number}
                  </Typography>
                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 600,
                      color: (theme) => theme.palette.text.primary,
                      fontSize: '0.95rem',
                      mt: 0.25,
                    }}
                  >
                    {step.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      color: (theme) => theme.palette.text.secondary,
                      fontSize: '0.8rem',
                      lineHeight: 1.6,
                      maxWidth: 300,
                    }}
                  >
                    {step.description}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        </Box>

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
            Tek bir sonuç değil, doğrulanan bir karar süreci.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Tahmin tek başına karar değildir.
            <br />
            Simülasyon ve doğrulama, kararın dayanıklılığını görmeye yardımcı olur.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default ApproachSection;