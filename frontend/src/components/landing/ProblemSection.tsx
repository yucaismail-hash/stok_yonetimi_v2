// src/components/landing/ProblemSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Stack,
  Avatar,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, AppCard } from '../ui';

// ✅ Problemler - Gerçekçi ve tanıdık
const problems = [
  {
    icon: InventoryIcon,
    title: 'Fazla Stok Maliyeti',
    description: 'Gereksiz stok, sermayenizin bağlı kalmasına ve maliyetlerin artmasına neden olur.',
    color: '#EF4444',
  },
  {
    icon: WarningIcon,
    title: 'Stok Tükenmesi',
    description: 'Kritik ürünlerde stok bitmesi, müşteri kaybı ve satış fırsatlarının kaçması demektir.',
    color: '#F59E0B',
  },
  {
    icon: TimelineIcon,
    title: 'Tahmin Hataları',
    description: 'Geleceği öngörememek, yanlış sipariş miktarları ve gereksiz israfa yol açar.',
    color: '#0B5ED7',
  },
  {
    icon: SpeedIcon,
    title: 'Karar Gecikmesi',
    description: 'Manuel analizlerle vakit kaybı, rekabet avantajınızı kaybetmenize neden olur.',
    color: '#8B5CF6',
  },
];

export function ProblemSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#F8FAFC" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Problem
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Stok Yönetiminde <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Karşılaşılan Zorluklar</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          Geleneksel yöntemlerle stok optimizasyonu yapmak, hem zaman kaybı hem de maliyet demektir.
        </Typography>
      </Box>

      <Grid container spacing={3} ref={ref}>
        {problems.map((problem, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.1, duration: 0.5 }}
            >
              <AppCard sx={{ p: 3, textAlign: 'center', height: '100%' }}>
                <Avatar
                  sx={{
                    width: 56,
                    height: 56,
                    bgcolor: `${problem.color}10`,
                    color: problem.color,
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <problem.icon sx={{ fontSize: 28 }} />
                </Avatar>
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 600, color: '#0F172A', mb: 1 }}
                >
                  {problem.title}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B' }}>
                  {problem.description}
                </Typography>
              </AppCard>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </SectionContainer>
  );
}

export default ProblemSection;