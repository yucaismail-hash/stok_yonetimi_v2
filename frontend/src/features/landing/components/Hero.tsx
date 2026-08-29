// src/features/landing/components/Hero.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Chip,
  Paper,
  Button,
  Stack,
  Divider,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  ArrowForward as ArrowForwardIcon,
  School as SchoolIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Storage as StorageIcon,
  Loop as LoopIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { PUBLIC_ANALYTICS_EVENTS, trackPublicEvent } from '../../../shared/analytics/ga';

export function Hero() {
  const navigate = useNavigate();

  const handleFreeStart = () => {
    trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.LANDING_FREE_START_CLICK, { placement: 'hero', destination: '/register' });
    navigate('/register');
  };

  const handleAcademyClick = () => {
    trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.LANDING_ACADEMY_CTA_CLICK, { placement: 'hero', destination: '/akademi' });
    navigate('/akademi');
  };

  return (
    <Box
      sx={{
        minHeight: { xs: 'auto', md: 'calc(100vh - 80px)' },
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        bgcolor: (theme) => theme.palette.background.default,
        py: { xs: 6, md: 0 },
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: { xs: 400, md: 800 },
          height: { xs: 400, md: 800 },
          background: (theme) =>
            `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.06)} 0%, transparent 70%)`,
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: { xs: 4, md: 8 },
            alignItems: 'center',
          }}
        >
          <Box>
            <Stack spacing={3}>
              <Chip
                label="Geliştirme Aşamasında"
                sx={{
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                  color: (theme) => theme.palette.primary.main,
                  fontWeight: 500,
                  fontSize: '0.75rem',
                  alignSelf: 'flex-start',
                  borderRadius: (theme) => theme.shape.borderRadius,
                  '& .MuiChip-label': {
                    px: 2,
                  },
                }}
              />

              <Typography
                variant="h1"
                component="h1"
                sx={{
                  fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4.2rem' },
                  fontWeight: 700,
                  lineHeight: 1.1,
                  letterSpacing: '-0.02em',
                  color: (theme) => theme.palette.text.primary,
                }}
              >
                İşletmeler stok değil,
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
                  belirsizlik yönetiyor.
                </Box>
              </Typography>

              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '1rem', md: '1.125rem' },
                  color: (theme) => theme.palette.text.secondary,
                  maxWidth: 560,
                  lineHeight: 1.7,
                }}
              >
                Stokonomi; tahminden simülasyona, doğrulamadan karar
                desteğine uzanan stok kararlarını birlikte değerlendirmek
                için geliştirilen bir karar sistemi yaklaşımıdır.
              </Typography>

              <Typography
                variant="body2"
                sx={{
                  color: (theme) => theme.palette.text.secondary,
                  maxWidth: 480,
                  lineHeight: 1.6,
                  opacity: 0.8,
                  fontSize: '0.875rem',
                  borderLeft: (theme) =>
                    `3px solid ${theme.palette.primary.main}`,
                  pl: 2,
                }}
              >
                Veriyi analiz etmeye, tahminleri sınamaya ve belirsizliği
                daha görünür hale getirmeye odaklanır. Karar vericinin
                yerini almaz; değerlendirmeyi daha güçlü kanıtlarla destekler.
              </Typography>

              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{ mt: 1 }}
              >
                <Button
                  variant="contained"
                  size="large"
                  endIcon={<ArrowForwardIcon />}
                  onClick={handleFreeStart}
                  sx={{
                    px: 4,
                    py: 1.5,
                    borderRadius: (theme) => theme.shape.borderRadius,
                    fontSize: '1rem',
                    fontWeight: 600,
                    textTransform: 'none',
                  }}
                >
                  Ücretsiz Başla
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<SchoolIcon />}
                  onClick={handleAcademyClick}
                  sx={{
                    px: 4,
                    py: 1.5,
                    borderRadius: (theme) => theme.shape.borderRadius,
                    fontSize: '1rem',
                    fontWeight: 600,
                    textTransform: 'none',
                    borderColor: (theme) => theme.palette.divider,
                    color: (theme) => theme.palette.text.primary,
                    '&:hover': {
                      borderColor: (theme) => theme.palette.primary.main,
                      bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
                    },
                  }}
                >
                  Akademiyi Keşfet
                </Button>
              </Stack>
            </Stack>
          </Box>

          <Box>
            <Paper
              elevation={0}
              sx={{
                overflow: 'hidden',
                border: (theme) => `1px solid ${theme.palette.divider}`,
                bgcolor: (theme) => theme.palette.background.paper,
                p: { xs: 2, sm: 3, md: 4 },
                position: 'relative',
              }}
            >
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  width: 120,
                  height: 120,
                  background: (theme) =>
                    `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.04)} 0%, transparent 70%)`,
                  borderRadius: '0 0 0 100%',
                  pointerEvents: 'none',
                }}
              />

              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  color: (theme) => theme.palette.text.primary,
                  mb: { xs: 0.5, sm: 0.5, md: 0.5 },
                  fontSize: { xs: '0.9rem', sm: '1rem', md: '1rem' },
                  letterSpacing: '-0.01em',
                }}
              >
                Karar Desteği Akışı
              </Typography>

              <Typography
                variant="caption"
                sx={{
                  color: (theme) => theme.palette.text.secondary,
                  display: 'block',
                  mb: { xs: 2, sm: 3, md: 3 },
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.7rem' },
                }}
              >
                Veriden karara giden yol
              </Typography>

              <Divider sx={{ mb: { xs: 2, sm: 3, md: 3 } }} />

              <Stack spacing={{ xs: 1.5, sm: 2, md: 2 }}>
                {[
                  { icon: <StorageIcon />, label: 'Veri', desc: 'Veriyi hazırlar' },
                  { icon: <AnalyticsIcon />, label: 'Analiz', desc: 'Davranışı analiz eder' },
                  { icon: <TimelineIcon />, label: 'Tahmin', desc: 'Olası talebi tahmin eder' },
                  { icon: <LoopIcon />, label: 'Simülasyon', desc: 'Senaryoları sınar' },
                  { icon: <PsychologyIcon />, label: 'Doğrulama', desc: 'Sonuçları test eder' },
                  { icon: <CheckCircleIcon />, label: 'Karar Desteği', desc: 'Kararı destekler' },
                ].map((item, index) => (
                  <Box
                    key={item.label}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: { xs: 1.5, sm: 2, md: 2 },
                      opacity: 1 - index * 0.06,
                      transition: 'opacity 0.2s',
                      '&:hover': {
                        opacity: 1,
                      },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: { xs: 32, sm: 40, md: 40 },
                        height: { xs: 32, sm: 40, md: 40 },
                        borderRadius: (theme) => theme.shape.borderRadius,
                        bgcolor: (theme) =>
                          index === 5
                            ? alpha(theme.palette.primary.main, 0.12)
                            : alpha(theme.palette.primary.main, 0.06),
                        color: (theme) =>
                          index === 5
                            ? theme.palette.primary.main
                            : theme.palette.text.secondary,
                        flexShrink: 0,
                      }}
                    >
                      {React.cloneElement(item.icon as React.ReactElement, {
                        sx: { fontSize: { xs: 16, sm: 20, md: 20 } },
                      })}
                    </Box>
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: index === 5 ? 600 : 500,
                          color: (theme) =>
                            index === 5
                              ? theme.palette.primary.main
                              : theme.palette.text.primary,
                          fontSize: { xs: '0.8rem', sm: '0.875rem', md: '0.875rem' },
                        }}
                      >
                        {item.label}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          color: (theme) => theme.palette.text.secondary,
                          fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.75rem' },
                          display: { xs: 'none', sm: 'block' },
                        }}
                      >
                        {item.desc}
                      </Typography>
                    </Box>
                    {index < 5 && (
                      <Box
                        sx={{
                          ml: 'auto',
                          color: (theme) => theme.palette.divider,
                          fontSize: { xs: 16, sm: 20, md: 20 },
                          fontWeight: 300,
                          lineHeight: 1,
                        }}
                      >
                        ↓
                      </Box>
                    )}
                  </Box>
                ))}
              </Stack>

              <Box
                sx={{
                  mt: { xs: 2, sm: 3, md: 3 },
                  pt: { xs: 1.5, sm: 2, md: 2 },
                  borderTop: (theme) => `1px solid ${theme.palette.divider}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    fontSize: { xs: '0.6rem', sm: '0.7rem', md: '0.7rem' },
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  Stokonomi · Karar Desteği
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    gap: 0.5,
                  }}
                >
                  {[1, 2, 3].map((i) => (
                    <Box
                      key={i}
                      sx={{
                        width: { xs: 5, sm: 6, md: 6 },
                        height: { xs: 5, sm: 6, md: 6 },
                        borderRadius: '50%',
                        bgcolor: (theme) =>
                          i === 3 ? theme.palette.primary.main : theme.palette.divider,
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </Paper>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default Hero;
