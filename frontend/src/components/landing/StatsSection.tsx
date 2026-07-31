// src/components/landing/StatsSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Paper,
  Stack,
} from '@mui/material';
import {
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../ui';

const stats = [
  {
    icon: TrendingDownIcon,
    value: 40,
    label: 'Fazla Stok Azalışı',
    suffix: '%',
    color: '#22C55E',
  },
  {
    icon: TrendingUpIcon,
    value: 94,
    label: 'Servis Seviyesi',
    suffix: '%',
    color: '#0B5ED7',
  },
  {
    icon: PsychologyIcon,
    value: 100,
    label: 'AI Destekli Analiz',
    suffix: '%',
    color: '#2F80ED',
  },
  {
    icon: SpeedIcon,
    value: 82,
    label: 'Karar Süresi Azalışı',
    suffix: '%',
    color: '#F59E0B',
  },
];

export function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={10}>
      <Grid container spacing={4} ref={ref}>
        {stats.map((stat, index) => (
          <Grid size={{ xs: 6, md: 3 }} key={index}>
            <motion.div
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
                  variant="h2"
                  sx={{
                    fontSize: { xs: '2rem', md: '2.5rem' },
                    fontWeight: 700,
                    color: '#0F172A',
                    mb: 0.5,
                  }}
                >
                  {stat.value}{stat.suffix}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B' }}>
                  {stat.label}
                </Typography>
              </Paper>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </SectionContainer>
  );
}

export default StatsSection;