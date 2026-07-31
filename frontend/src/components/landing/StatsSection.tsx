// src/components/landing/StatsSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  History as HistoryIcon,
  Psychology as PsychologyIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../ui';

const stats = [
  {
    icon: AnalyticsIcon,
    value: '6+',
    label: 'Analiz Modülü',
    description: 'Emniyet Stoku, Talep Tahmini, Simülasyon ve daha fazlası.',
    color: '#0B5ED7',
  },
  {
    icon: HistoryIcon,
    value: '8',
    label: 'Backtest Stratejisi',
    description: 'Geçmiş veriler üzerinde farklı yöntemleri karşılaştırın.',
    color: '#2F80ED',
  },
  {
    icon: PsychologyIcon,
    value: 'AI',
    label: 'Destekli Karar Önerileri',
    description: 'AI destekli yorumlar ve öneriler.',
    color: '#22C55E',
  },
  {
    icon: DownloadIcon,
    value: 'Tek Tık',
    label: 'Excel Çıktı',
    description: 'Tüm önerileri Excel olarak dışa aktarın.',
    color: '#F59E0B',
  },
];

export function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={8}>
      <Box
        ref={ref}
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(4, 1fr)' },
          gap: 3,
        }}
      >
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: index * 0.1, duration: 0.5 }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 3,
                textAlign: 'center',
                borderRadius: '20px',
                border: '1px solid #E2E8F0',
                height: '100%',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  boxShadow: '0 8px 32px rgba(0,0,0,0.06)',
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  bgcolor: `${stat.color}10`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <stat.icon sx={{ color: stat.color, fontSize: 24 }} />
              </Box>
              <Typography
                variant="h3"
                sx={{
                  fontSize: { xs: '1.5rem', md: '2rem' },
                  fontWeight: 700,
                  color: '#0F172A',
                  mb: 0.5,
                }}
              >
                {stat.value}
              </Typography>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 600,
                  color: '#0F172A',
                  mb: 0.5,
                  fontSize: '0.875rem',
                }}
              >
                {stat.label}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                {stat.description}
              </Typography>
            </Paper>
          </motion.div>
        ))}
      </Box>
    </SectionContainer>
  );
}

export default StatsSection;