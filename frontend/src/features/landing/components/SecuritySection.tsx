// src/components/landing/SecuritySection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,        // ✅ EKLENDI
  Avatar,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Lock as LockIcon,
  Security as SecurityIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, AppCard } from '../../../shared/ui';

// ✅ 4 özellik - Sade ve güven verici
const securityItems = [
  {
    icon: ShieldIcon,
    title: 'SSL ile Güvenli Bağlantı',
    color: '#0B5ED7',
  },
  {
    icon: LockIcon,
    title: 'Şifrelenmiş Veri Aktarımı',
    color: '#2F80ED',
  },
  {
    icon: SecurityIcon,
    title: 'Güvenli Kullanıcı Doğrulama',
    color: '#22C55E',
  },
  {
    icon: VerifiedIcon,
    title: 'Güvenli Bulut Altyapısı',
    color: '#8B5CF6',
  },
];

export function SecuritySection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={8}>
      <Box sx={{ textAlign: 'center', maxWidth: 600, mx: 'auto', mb: 5 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Güvenlik
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>
          Verileriniz <Box component="span" sx={{ color: '#0B5ED7' }}>Güvende</Box>
        </Typography>
      </Box>

      <Box
        ref={ref}
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' },
          gap: 2,
        }}
      >
        {securityItems.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: index * 0.1, duration: 0.4 }}
          >
            {/* ✅ Paper import edildi ve doğru kullanıldı */}
            <Paper
              elevation={0}
              sx={{
                p: 2.5,
                textAlign: 'center',
                borderRadius: '16px',
                border: '1px solid #E2E8F0',
                height: '100%',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  borderColor: item.color,
                  boxShadow: `0 4px 16px ${item.color}15`,
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: `${item.color}10`,
                  color: item.color,
                  mx: 'auto',
                  mb: 1,
                }}
              >
                <item.icon sx={{ fontSize: 20 }} />
              </Avatar>
              <Typography
                variant="body2"
                sx={{ fontWeight: 500, color: '#0F172A', fontSize: '0.75rem' }}
              >
                {item.title}
              </Typography>
            </Paper>
          </motion.div>
        ))}
      </Box>
    </SectionContainer>
  );
}

export default SecuritySection;