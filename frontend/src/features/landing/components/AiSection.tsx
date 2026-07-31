// src/components/landing/AiSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../../../shared/ui';

const features = [
  'AI destekli analiz yorumları',
  'Executive Summary oluşturma',
  'Şirket analiz geçmişi ile karşılaştırma',
  'Şirkete Özel Analiz Hafızası',
];

const featureDescriptions = [
  'Emniyet stoku, talep tahmini ve risk analizlerini birlikte değerlendirir.',
  'Her analiz sonunda yönetici özeti oluşturur.',
  'Önceki analizleri karşılaştırın ve zaman içindeki değişimi takip edin.',
  'Analiz geçmişinizi referans alarak kararlarınızı destekler.',
];

export function AiSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <Box
      sx={{
        py: 12,
        bgcolor: '#0F172A',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Glow Efekti */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 600,
          height: 600,
          background: 'radial-gradient(circle, rgba(11,94,215,0.15) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }} ref={ref}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 6,
            alignItems: 'center',
          }}
        >
          {/* Sol Taraf */}
          <Box>
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.6 }}
            >
              <Chip
                icon={<AutoAwesomeIcon sx={{ fontSize: 16 }} />}
                label="Yapay Zeka Motoru"
                sx={{
                  bgcolor: 'rgba(11,94,215,0.2)',
                  color: '#38BDF8',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  mb: 3,
                  '& .MuiChip-icon': { color: '#38BDF8' },
                }}
              />

              {/* ✅ Yeni Başlık: Stokonomi AI */}
              <Typography
                variant="h2"
                sx={{
                  fontSize: { xs: '2rem', md: '3rem' },
                  fontWeight: 700,
                  color: 'white',
                  mb: 1,
                }}
              >
                Stokonomi AI
              </Typography>

              {/* ✅ Yeni Alt Başlık */}
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                  fontWeight: 600,
                  color: 'rgba(255,255,255,0.8)',
                  mb: 3,
                }}
              >
                Sadece Hesap Yapmaz.
                <Box
                  component="span"
                  sx={{
                    background: 'linear-gradient(135deg, #38BDF8, #2F80ED)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  {' '}Karar Destek Sağlar.
                </Box>
              </Typography>

              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255,255,255,0.6)',
                  fontSize: '1.125rem',
                  lineHeight: 1.7,
                  mb: 4,
                  maxWidth: 520,
                }}
              >
                Stokonomi AI, analiz sonuçlarını yorumlayarak stok kararlarını destekleyen 
                açıklamalar üretir. Emniyet stoğu, talep tahmini ve risk analizlerini 
                birlikte değerlendirir.
              </Typography>

              {/* ✅ Feature List - Analiz Hafızası vurgusu */}
              <Stack spacing={2.5}>
                {features.map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{ delay: index * 0.1, duration: 0.4 }}
                  >
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                        <CheckCircleIcon sx={{ color: '#22C55E', fontSize: 20, mt: 0.3 }} />
                        <Box>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'white',
                              fontWeight: 600,
                              fontSize: '0.9rem',
                            }}
                          >
                            {item}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'rgba(255,255,255,0.4)',
                              display: 'block',
                              mt: 0.25,
                            }}
                          >
                            {featureDescriptions[index]}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </motion.div>
                ))}
              </Stack>
            </motion.div>
          </Box>

          {/* Sağ Taraf: AI Örnek Mesajı */}
          <Box>
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 4,
                  borderRadius: '24px',
                  border: '1px solid rgba(255,255,255,0.08)',
                  bgcolor: 'rgba(255,255,255,0.04)',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Avatar sx={{ bgcolor: 'rgba(11,94,215,0.2)', width: 48, height: 48 }}>
                    <PsychologyIcon sx={{ color: '#38BDF8' }} />
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'white' }}>
                      Stokonomi AI
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>
                      v1.0 • Aktif
                    </Typography>
                  </Box>
                  <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 8, height: 8, bgcolor: '#22C55E', borderRadius: '50%' }} />
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>
                      Canlı
                    </Typography>
                  </Box>
                </Box>

                {/* ✅ Yeni AI Mesajı - Gerçekçi */}
                <Box
                  sx={{
                    p: 3,
                    bgcolor: 'rgba(255,255,255,0.04)',
                    borderRadius: '16px',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: 'rgba(255,255,255,0.8)',
                      lineHeight: 1.8,
                      fontStyle: 'italic',
                    }}
                  >
                    "Analiz tamamlandı.
                    <br />
                    124 ürün incelendi.
                    <br />
                    18 üründe fazla stok riski tespit edildi.
                    <br />
                    7 ürün için emniyet stoğu artırılması öneriliyor.
                    <br />
                    <br />
                    En uygun tahmin yöntemi:
                    <br />
                    <Box component="span" sx={{ color: '#38BDF8', fontWeight: 600 }}>
                      Croston SBA
                    </Box>
                    "
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                    {['A', 'B', 'C'].map((letter) => (
                      <Avatar
                        key={letter}
                        sx={{
                          width: 24,
                          height: 24,
                          fontSize: '0.6rem',
                          bgcolor: 'rgba(11,94,215,0.2)',
                          color: '#38BDF8',
                          fontWeight: 600,
                        }}
                      >
                        {letter}
                      </Avatar>
                    ))}
                    <Typography
                      variant="caption"
                      sx={{ color: 'rgba(255,255,255,0.3)', ml: 1, alignSelf: 'center' }}
                    >
                      3 model tarafından doğrulandı
                    </Typography>
                  </Stack>
                </Box>
              </Paper>
            </motion.div>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default AiSection;