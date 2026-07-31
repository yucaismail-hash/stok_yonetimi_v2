// src/components/landing/FeaturesSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,        // ✅ EKLENDI
  Avatar,      // ✅ EKLENDI
} from '@mui/material';
import {
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Science as ScienceIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, AppCard } from '../ui';

// ✅ SIRA DEĞİŞTİ - Önce Ürün Özellikleri
const features = [
  {
    icon: SecurityIcon,
    title: 'Emniyet Stoku',
    description: '6 farklı metot ile optimum emniyet stoğu seviyesini belirleyin.',
    color: '#0B5ED7',
  },
  {
    icon: TrendingUpIcon,
    title: 'Talep Tahmini',
    description: 'Mevsimsellik, trend ve anomalileri tespit ederek geleceği öngörün.',
    color: '#2F80ED',
  },
  {
    icon: ScienceIcon,
    title: 'Monte Carlo Simülasyonu',
    description: 'Farklı stok senaryolarını test edin ve riskleri önceden görün.',
    color: '#22C55E',
  },
  {
    icon: HistoryIcon,
    title: 'Backtest',
    description: 'Geçmiş verilerle modellerinizi test edin ve performansı ölçün.',
    color: '#F59E0B',
  },
  {
    icon: AssessmentIcon,
    title: 'Executive Summary',
    description: 'Her analiz sonunda yönetici özeti oluşturun.',
    color: '#EF4444',
  },
  {
    icon: DownloadIcon,
    title: 'Excel Raporları',
    description: 'Analiz sonuçlarını Excel olarak dışa aktarın.',
    color: '#8B5CF6',
  },
];

export function FeaturesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#F8FAFC" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Özellikler
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Analiz Araçları <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Tek Platformda</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          Stok yönetiminin tüm ihtiyaçlarına yönelik araçlar tek bir platformda.
        </Typography>
      </Box>

      {/* ✅ Grid doğru kullanıldı */}
      <Grid container spacing={3} ref={ref}>
        {features.map((feature, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.05, duration: 0.4 }}
            >
              <AppCard sx={{ p: 3, height: '100%', textAlign: 'center' }}>
                {/* ✅ Avatar doğru kullanıldı */}
                <Avatar
                  sx={{
                    width: 48,
                    height: 48,
                    bgcolor: `${feature.color}10`,
                    color: feature.color,
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <feature.icon />
                </Avatar>
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 600, color: '#0F172A', mb: 1 }}
                >
                  {feature.title}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B' }}>
                  {feature.description}
                </Typography>
              </AppCard>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </SectionContainer>
  );
}

export default FeaturesSection;