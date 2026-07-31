// src/components/landing/ModulesSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Button,
  Avatar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Science as ScienceIcon,
  History as HistoryIcon,
  LocalShipping as LocalShippingIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, AppCard } from '../../../shared/ui';

// ✅ Modüller - Gerçek ürün özellikleri
const modules = [
  {
    icon: DashboardIcon,
    title: 'Dashboard',
    description: 'Anlık veriler, AI asistanı ve executive summary ile işinizin nabzını tutun.',
    color: '#0B5ED7',
  },
  {
    icon: SecurityIcon,
    title: 'Emniyet Stoğu',
    description: '6 farklı metot + AI ile optimum emniyet stoğu seviyesini belirleyin.',
    color: '#2F80ED',
  },
  {
    icon: TrendingUpIcon,
    title: 'Talep Tahmini',
    description: 'Mevsimsellik, trend ve anomalileri tespit ederek geleceği öngörün.',
    color: '#22C55E',
  },
  {
    icon: ScienceIcon,
    title: 'Monte Carlo Simülasyonu',
    description: 'Farklı stok senaryolarını test edin ve riskleri önceden görün.',
    color: '#F59E0B',
  },
  {
    icon: HistoryIcon,
    title: 'Backtest',
    description: 'Geçmiş verilerle modellerinizi test edin ve performansı ölçün.',
    color: '#EF4444',
  },
  {
    icon: LocalShippingIcon,
    title: 'Tedarikçi Analizi',
    description: 'Tedarikçi performansı, risk skoru ve teslim sürelerini analiz edin.',
    color: '#8B5CF6',
  },
];

export function ModulesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#F8FAFC" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Ürün Modülleri
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Tek Platform, <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Sonsuz İmkan</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          Stok yönetiminin tüm ihtiyaçlarına yönelik modüller tek bir platformda.
        </Typography>
      </Box>

      <Grid container spacing={3} ref={ref}>
        {modules.map((module, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.05, duration: 0.4 }}
            >
              <AppCard sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Avatar
                  sx={{
                    width: 48,
                    height: 48,
                    bgcolor: `${module.color}10`,
                    color: module.color,
                    mb: 2,
                  }}
                >
                  <module.icon />
                </Avatar>
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 600, color: '#0F172A', mb: 1 }}
                >
                  {module.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: '#64748B', flex: 1, mb: 2 }}
                >
                  {module.description}
                </Typography>
                <Button
                  variant="text"
                  sx={{
                    color: module.color,
                    fontWeight: 600,
                    alignSelf: 'flex-start',
                    '&:hover': {
                      bgcolor: `${module.color}10`,
                    },
                  }}
                >
                  Detayları İncele →
                </Button>
              </AppCard>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </SectionContainer>
  );
}

export default ModulesSection;