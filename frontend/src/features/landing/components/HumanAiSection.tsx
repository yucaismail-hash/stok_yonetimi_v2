// src/features/landing/components/HumanAiSection.tsx
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
  Analytics as AnalyticsIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Visibility as VisibilityIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';

const aiCapabilities = [
  { icon: AnalyticsIcon, label: 'Veriyi işler' },
  { icon: TimelineIcon, label: 'Örüntüleri analiz eder' },
  { icon: PsychologyIcon, label: 'Tahminleri ve senaryoları sınar' },
  { icon: VisibilityIcon, label: 'Riskleri görünür hale getirir' },
  { icon: AssessmentIcon, label: 'Bulguları açıklanabilir hale getirir' },
];

const humanCapabilities = [
  { icon: PersonIcon, label: 'İş bağlamını değerlendirir' },
  { icon: LightbulbIcon, label: 'Operasyonel öncelikleri dikkate alır' },
  { icon: AssessmentIcon, label: 'Ticari ve stratejik koşulları yorumlar' },
  { icon: CheckCircleIcon, label: 'Nihai kararı verir' },
];

const explainabilityItems = [
  'Talep davranışı',
  'Tedarik belirsizliği',
  'Simülasyon sonucu',
  'Geçmiş doğrulama',
];

export function HumanAiSection() {
  return (
    <Box
      id="human-ai"
      sx={{
        py: { xs: 8, md: 12 },
        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
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
            İNSAN İÇİN AI
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
            İnsan yerine değil,
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
              insan için
            </Box>
            <br />
            yapay zekâ.
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
            Stokonomi'nin amacı karar vericinin yerini almak değil;
            karmaşık veriyi daha anlaşılır hale getirerek
            daha güçlü kararlar alınmasına yardımcı olmaktır.
          </Typography>
        </Box>

        {/* Main Content: AI + Decision Support + Human */}
        <Grid container spacing={{ xs: 3, md: 4 }}>
          {/* STOKONOMI AI */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                borderRadius: (theme) => theme.shape.borderRadius,
                border: (theme) => `1px solid ${theme.palette.divider}`,
                bgcolor: (theme) => theme.palette.background.paper,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {/* Header - centered */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: 3,
                  minHeight: 72,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 44,
                    height: 44,
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                    color: (theme) => theme.palette.primary.main,
                    mb: 1,
                  }}
                >
                  <AnalyticsIcon />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: '1.1rem',
                    textAlign: 'center',
                  }}
                >
                  STOKONOMİ AI
                </Typography>
              </Box>

              {/* Capabilities - Grid layout */}
              <Box
                sx={{
                  flex: 1,
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr 1fr', md: '1fr 1fr 1fr' },
                  gap: 2,
                }}
              >
                {aiCapabilities.map((item) => (
                  <Box
                    key={item.label}
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      minHeight: 90,
                      p: 1,
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
                        color: (theme) => theme.palette.primary.main,
                        mb: 1,
                        flexShrink: 0,
                      }}
                    >
                      <item.icon sx={{ fontSize: 18 }} />
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: (theme) => theme.palette.text.primary,
                        fontWeight: 500,
                        fontSize: '0.75rem',
                        lineHeight: 1.4,
                      }}
                    >
                      {item.label}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Karar Desteği - Center Connector */}
          <Grid
            size={{ xs: 12, md: 2 }}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'row', md: 'column' },
                alignItems: 'center',
                justifyContent: 'center',
                gap: { xs: 1.5, md: 1.5 },
                py: { xs: 2, md: 0 },
                px: { xs: 0, md: 1 },
                width: '100%',
              }}
            >
              <Box
                sx={{
                  width: { xs: '80px', md: '2px' },
                  height: { xs: '2px', md: '60px' },
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.15),
                }}
              />
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                  border: (theme) =>
                    `2px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                  color: (theme) => theme.palette.primary.main,
                  flexShrink: 0,
                }}
              >
                <PsychologyIcon />
              </Box>
              <Typography
                variant="caption"
                sx={{
                  color: (theme) => theme.palette.primary.main,
                  fontWeight: 600,
                  fontSize: '0.7rem',
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                }}
              >
                Karar
                <br />
                Desteği
              </Typography>
              <Box
                sx={{
                  width: { xs: '80px', md: '2px' },
                  height: { xs: '2px', md: '60px' },
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.15),
                }}
              />
            </Box>
          </Grid>

          {/* KARAR VERİCİ */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, md: 4 },
                height: '100%',
                borderRadius: (theme) => theme.shape.borderRadius,
                border: (theme) => `1px solid ${theme.palette.divider}`,
                bgcolor: (theme) => theme.palette.background.paper,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {/* Header - centered */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: 3,
                  minHeight: 72,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 44,
                    height: 44,
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.success.main, 0.08),
                    color: (theme) => theme.palette.success.main,
                    mb: 1,
                  }}
                >
                  <PersonIcon />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: '1.1rem',
                    textAlign: 'center',
                  }}
                >
                  KARAR VERİCİ
                </Typography>
              </Box>

              {/* Capabilities - Grid layout */}
              <Box
                sx={{
                  flex: 1,
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr 1fr', md: '1fr 1fr' },
                  gap: 2,
                }}
              >
                {humanCapabilities.map((item) => (
                  <Box
                    key={item.label}
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      minHeight: 90,
                      p: 1,
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        bgcolor: (theme) => alpha(theme.palette.success.main, 0.06),
                        color: (theme) => theme.palette.success.main,
                        mb: 1,
                        flexShrink: 0,
                      }}
                    >
                      <item.icon sx={{ fontSize: 18 }} />
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: (theme) => theme.palette.text.primary,
                        fontWeight: 500,
                        fontSize: '0.75rem',
                        lineHeight: 1.4,
                      }}
                    >
                      {item.label}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Core Statement */}
        <Box
          sx={{
            mt: { xs: 6, md: 8 },
            textAlign: 'center',
            maxWidth: 680,
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
            AI önerir. İnsan değerlendirir.
            <br />
            Karar birlikte güçlenir.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Stokonomi kara kutu bir otomasyon sistemi değil,
            kararın nedenlerini görünür kılmayı hedefleyen
            bir karar destek platformudur.
          </Typography>
        </Box>

        {/* Explainability Section */}
        <Box
          sx={{
            mt: { xs: 5, md: 6 },
            maxWidth: 680,
            mx: 'auto',
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, md: 4 },
              borderRadius: (theme) => theme.shape.borderRadius,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              bgcolor: (theme) => alpha(theme.palette.background.paper, 0.6),
            }}
          >
            <Box sx={{ textAlign: 'center', mb: 2.5 }}>
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  color: (theme) => theme.palette.text.primary,
                  fontSize: '1rem',
                }}
              >
                AI neden bu kararı önerdi?
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: (theme) => theme.palette.text.secondary,
                  fontSize: '0.85rem',
                  mt: 0.5,
                }}
              >
                Stokonomi sonuçların arkasındaki temel etkenleri,
                riskleri ve kullanılan kanıtları anlaşılır biçimde
                gösterir.
              </Typography>
            </Box>

            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: 1.5,
              }}
            >
              {explainabilityItems.map((item) => (
                <Box
                  key={item}
                  sx={{
                    px: 2,
                    py: 1,
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
                    border: (theme) =>
                      `1px solid ${alpha(theme.palette.primary.main, 0.06)}`,
                    color: (theme) => theme.palette.text.secondary,
                    fontSize: '0.8rem',
                    fontWeight: 500,
                  }}
                >
                  {item}
                </Box>
              ))}
            </Box>
          </Paper>
        </Box>
      </Container>
    </Box>
  );
}

export default HumanAiSection;