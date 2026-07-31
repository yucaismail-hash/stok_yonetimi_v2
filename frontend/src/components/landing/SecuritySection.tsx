// src/components/landing/SecuritySection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Avatar,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Lock as LockIcon,
  Security as SecurityIcon,
  People as PeopleIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, AppCard } from '../ui';

const securityItems = [
  {
    icon: ShieldIcon,
    title: 'SSL Sertifikası',
    description: '256-bit SSL ile tüm veri iletimi şifrelenir.',
    color: '#0B5ED7',
  },
  {
    icon: LockIcon,
    title: 'KVKK Uyumlu',
    description: 'Kişisel verilerin korunması kanununa tam uyumludur.',
    color: '#2F80ED',
  },
  {
    icon: SecurityIcon,
    title: 'Uçtan Uca Şifreleme',
    description: 'Verileriniz şifrelenerek saklanır ve iletilir.',
    color: '#22C55E',
  },
  {
    icon: PeopleIcon,
    title: 'Rol Bazlı Yetki',
    description: 'Ekip üyelerine özel erişim seviyeleri tanımlayın.',
    color: '#F59E0B',
  },
  {
    icon: CloudIcon,
    title: 'Bulut Altyapı',
    description: 'AWS üzerinde yedekli ve güvenli altyapı.',
    color: '#8B5CF6',
  },
];

export function SecuritySection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#F8FAFC" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Güvenlik
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Verileriniz <Box component="span" sx={{ color: '#0B5ED7' }}>Güvende</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          Kurumsal standartlarda güvenlik önlemleri ile verileriniz korunur.
        </Typography>
      </Box>

      <Grid container spacing={3} ref={ref}>
        {securityItems.map((item, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
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
                    bgcolor: `${item.color}10`,
                    color: item.color,
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <item.icon sx={{ fontSize: 28 }} />
                </Avatar>
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 600, color: '#0F172A', mb: 1 }}
                >
                  {item.title}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B' }}>
                  {item.description}
                </Typography>
              </AppCard>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </SectionContainer>
  );
}

export default SecuritySection;