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
  { icon: AnalyticsIcon, label: 'Veriyi analiz eder' },
  { icon: TimelineIcon, label: 'Yaklaşımları karşılaştırır' },
  { icon: PsychologyIcon, label: 'Tahminleri ve senaryoları sınar' },
  { icon: VisibilityIcon, label: 'Riskleri görünür hale getirmeyi amaçlar' },
  { icon: AssessmentIcon, label: 'Bulguları açıklamaya yardımcı olur' },
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
        py: { xs: 8, md: 10 },
        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
      }}
    >
      <Container maxWidth="xl">
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 720,
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

        <Grid container spacing={{ xs: 3, md: 4 }}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 2.5, sm: 3, md: 4 },
                height: '100%',
                borderRadius: (theme) => theme.shape.borderRadius,
                border: (theme) => `1px solid ${theme.palette.divider}`,
                bgcolor: (theme) => theme.palette.background.paper,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: { xs: 2, sm: 3, md: 3 },
                  minHeight: { xs: 60, sm: 72, md: 72 },
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: { xs: 36, sm: 44, md: 44 },
                    height: { xs: 36, sm: 44, md: 44 },
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                    color: (theme) => theme.palette.primary.main,
                    mb: 1,
                  }}
                >
                  <AnalyticsIcon sx={{ fontSize: { xs: 18, sm: 22, md: 22 } }} />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.1rem' },
                    textAlign: 'center',
                  }}
                >
                  STOKONOMİ AI
                </Typography>
              </Box>

              <Box
                sx={{
                  flex: 1,
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr 1fr',
                    sm: '1fr 1fr 1fr',
                    md: '1fr 1fr 1fr',
                  },
                  gap: { xs: 1.5, sm: 2, md: 2 },
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
                      minHeight: { xs: 75, sm: 90, md: 90 },
                      p: { xs: 1, sm: 1.5, md: 1.5 },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: { xs: 32, sm: 36, md: 36 },
                        height: { xs: 32, sm: 36, md: 36 },
                        borderRadius: '50%',
                        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
                        color: (theme) => theme.palette.primary.main,
                        mb: 1,
                        flexShrink: 0,
                      }}
                    >
                      <item.icon sx={{ fontSize: { xs: 16, sm: 18, md: 18 } }} />
                    </Box>
                    <Typography
                      variant="body2"
                      sx={{
                        color: (theme) => theme.palette.text.primary,
                        fontWeight: 500,
                        fontSize: { xs: '0.75rem', sm: '0.8rem', md: '0.8rem' },
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
                gap: { xs: 1, sm: 1, md: 1.5 },
                py: { xs: 1.5, sm: 1.5, md: 0 },
                px: { xs: 0, sm: 0, md: 1 },
                width: '100%',
              }}
            >
              <Box
                sx={{
                  width: { xs: '60px', sm: '60px', md: '2px' },
                  height: { xs: '2px', sm: '2px', md: '40px' },
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.15),
                }}
              />
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: { xs: 40, sm: 44, md: 48 },
                  height: { xs: 40, sm: 44, md: 48 },
                  borderRadius: '50%',
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08),
                  border: (theme) =>
                    `2px solid ${alpha(theme.palette.primary.main, 0.15)}`,
                  color: (theme) => theme.palette.primary.main,
                  flexShrink: 0,
                }}
              >
                <PsychologyIcon sx={{ fontSize: { xs: 20, sm: 22, md: 24 } }} />
              </Box>
              <Typography
                variant="caption"
                sx={{
                  color: (theme) => theme.palette.primary.main,
                  fontWeight: 600,
                  fontSize: { xs: '0.6rem', sm: '0.65rem', md: '0.7rem' },
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
                  width: { xs: '60px', sm: '60px', md: '2px' },
                  height: { xs: '2px', sm: '2px', md: '40px' },
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.15),
                }}
              />
            </Box>
          </Grid>

          <Grid size={{ xs: 12, md: 5 }}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 2.5, sm: 3, md: 4 },
                height: '100%',
                borderRadius: (theme) => theme.shape.borderRadius,
                border: (theme) => `1px solid ${theme.palette.divider}`,
                bgcolor: (theme) => theme.palette.background.paper,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: { xs: 2, sm: 3, md: 3 },
                  minHeight: { xs: 60, sm: 72, md: 72 },
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: { xs: 36, sm: 44, md: 44 },
                    height: { xs: 36, sm: 44, md: 44 },
                    borderRadius: 2,
                    bgcolor: (theme) => alpha(theme.palette.success.main, 0.08),
                    color: (theme) => theme.palette.success.main,
                    mb: 1,
                  }}
                >
                  <PersonIcon sx={{ fontSize: { xs: 18, sm: 22, md: 22 } }} />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.1rem' },
                    textAlign: 'center',
                  }}
                >
                  KARAR VERİCİ
                </Typography>
              </Box>

              <Box
                sx={{
                  flex: 1,
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr 1fr',
                    sm: '1fr 1fr',
                    md: '1fr 1fr',
                  },
                  gap: { xs: 1.5, sm: 2, md: 2 },
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
                      minHeight: { xs: 75, sm: 90, md: 90 },
                      p: { xs: 1, sm: 1.5, md: 1.5 },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: { xs: 32, sm: 36, md: 36 },
                        height: { xs: 32, sm: 36, md: 36 },
                        borderRadius: '50%',
                        bgcolor: (theme) => alpha(theme.palette.success.main, 0.06),
                        color: (theme) => theme.palette.success.main,
                        mb: 1,
                        flexShrink: 0,
                      }}
                    >
                      <item.icon sx={{ fontSize: { xs: 16, sm: 18, md: 18 } }} />
                    </Box>
                    <Typography
                      variant="body2"
                      sx={{
                        color: (theme) => theme.palette.text.primary,
                        fontWeight: 500,
                        fontSize: { xs: '0.75rem', sm: '0.8rem', md: '0.8rem' },
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

        <Box
          sx={{
            mt: { xs: 6, md: 6 },
            textAlign: 'center',
            maxWidth: 680,
            mx: 'auto',
            pt: { xs: 4, md: 5 },
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
            AI analiz eder. İnsan değerlendirir.
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
            Stokonomi kara kutu bir otomasyon sistemi değil; analizi,
            karşılaştırmayı, sınamayı ve açıklamayı karar vericinin
            değerlendirmesine sunmayı hedefleyen bir karar destek platformudur.
          </Typography>
        </Box>

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
