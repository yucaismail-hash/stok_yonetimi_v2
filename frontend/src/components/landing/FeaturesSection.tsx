// src/components/landing/FeaturesSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Stack,
  Chip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  AutoAwesome as AutoAwesomeIcon,
  Analytics as AnalyticsIcon,
  IntegrationInstructions as IntegrationIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../ui';

const features = [
  {
    icon: SpeedIcon,
    title: 'Hızlı Analiz',
    description: 'Excel yükleyin, 7 dakika içinde AI destekli rapor alın.',
  },
  {
    icon: SecurityIcon,
    title: 'Kurumsal Güvenlik',
    description: 'ISO 27001, GDPR ve KVKK uyumlu veri güvenliği.',
  },
  {
    icon: AutoAwesomeIcon,
    title: 'AI Karar Motoru',
    description: '6 farklı AI modeli ile akıllı karar destek sistemi.',
  },
  {
    icon: AnalyticsIcon,
    title: 'Gerçek Zamanlı',
    description: 'Canlı dashboard ve anlık veri analizi.',
  },
  {
    icon: IntegrationIcon,
    title: 'Kolay Entegrasyon',
    description: 'ERP, Excel ve diğer sistemlerle entegre çalışır.',
  },
  {
    icon: SecurityIcon,
    title: 'Rol Bazlı Yetki',
    description: 'Ekip üyelerine özel yetkilendirme ve erişim kontrolü.',
  },
];

export function FeaturesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Özellikler
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Neden <Box component="span" sx={{ color: '#0B5ED7' }}>Stokonomi?</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          AI destekli stok yönetiminin tüm avantajları tek platformda.
        </Typography>
      </Box>

      <Grid container spacing={3} ref={ref}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Stack spacing={3}>
            {features.slice(0, 3).map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -30 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: index * 0.1, duration: 0.4 }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: '16px',
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 3,
                    '&:hover': {
                      borderColor: '#0B5ED7',
                      boxShadow: '0 4px 16px rgba(11,94,215,0.08)',
                    },
                    transition: 'all 0.3s ease-in-out',
                  }}
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      bgcolor: 'rgba(11,94,215,0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <feature.icon sx={{ color: '#0B5ED7', fontSize: 24 }} />
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#0F172A', mb: 0.5 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      {feature.description}
                    </Typography>
                  </Box>
                </Paper>
              </motion.div>
            ))}
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Stack spacing={3}>
            {features.slice(3).map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 30 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: index * 0.1 + 0.2, duration: 0.4 }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: '16px',
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 3,
                    '&:hover': {
                      borderColor: '#0B5ED7',
                      boxShadow: '0 4px 16px rgba(11,94,215,0.08)',
                    },
                    transition: 'all 0.3s ease-in-out',
                  }}
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      bgcolor: 'rgba(11,94,215,0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <feature.icon sx={{ color: '#0B5ED7', fontSize: 24 }} />
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: '#0F172A', mb: 0.5 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      {feature.description}
                    </Typography>
                  </Box>
                </Paper>
              </motion.div>
            ))}
          </Stack>
        </Grid>
      </Grid>
    </SectionContainer>
  );
}

export default FeaturesSection;