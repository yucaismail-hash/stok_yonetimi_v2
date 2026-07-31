// src/components/landing/PricingSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer, PrimaryButton } from '../../../shared/ui';

const plans = [
  {
    name: 'Starter',
    price: '0',
    description: 'Küçük işletmeler için ideal',
    features: [
      '5 ürün analizi',
      'Temel talep tahmini',
      'Email desteği',
      '14 gün veri saklama',
    ],
    highlighted: false,
    buttonText: 'Ücretsiz Başla',
  },
  {
    name: 'Professional',
    price: '499',
    description: 'Büyüyen işletmeler için',
    features: [
      'Sınırsız ürün analizi',
      'AI destekli talep tahmini',
      'Öncelikli email + telefon desteği',
      '90 gün veri saklama',
      'Çoklu kullanıcı desteği',
      'Özel entegrasyonlar',
    ],
    highlighted: true,
    buttonText: 'Ücretsiz Deneyin',
  },
  {
    name: 'Enterprise',
    price: 'Özel',
    description: 'Kurumsal ihtiyaçlar için',
    features: [
      'Özel AI modelleri',
      'Öncelikli 7/24 destek',
      'Sınırsız veri saklama',
      'Özel SLA ve güvenlik',
      'Teknik müşteri yöneticisi',
      'Tedarikçi entegrasyonu',
    ],
    highlighted: false,
    buttonText: 'İletişime Geç',
  },
];

export function PricingSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Fiyatlandırma
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          İhtiyacınıza Uygun <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Planı Seçin</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          14 gün ücretsiz deneyin. Kredi kartı gerekmez.
        </Typography>
      </Box>

      {/* ✅ Grid kaldırıldı, Box ile grid sistemi oluşturuldu */}
      <Box
        ref={ref}
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: 4,
          alignItems: 'stretch',
        }}
      >
        {plans.map((plan, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: index * 0.1, duration: 0.5 }}
            style={{ display: 'flex' }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 4,
                borderRadius: '24px',
                border: plan.highlighted
                  ? '2px solid #0B5ED7'
                  : '1px solid #E2E8F0',
                width: '100%',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  boxShadow: '0 8px 40px rgba(0,0,0,0.06)',
                },
                transition: 'all 0.3s ease-in-out',
              }}
            >
              {plan.highlighted && (
                <Chip
                  label="Popüler"
                  sx={{
                    position: 'absolute',
                    top: -12,
                    right: 24,
                    bgcolor: '#0B5ED7',
                    color: 'white',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                  }}
                />
              )}

              <Typography
                variant="overline"
                sx={{ color: plan.highlighted ? '#0B5ED7' : '#64748B', fontWeight: 600 }}
              >
                {plan.name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mt: 1, mb: 1 }}>
                <Typography
                  variant="h2"
                  sx={{
                    fontSize: '2.5rem',
                    fontWeight: 700,
                    color: '#0F172A',
                  }}
                >
                  {plan.price === 'Özel' ? 'Özel' : `₺${plan.price}`}
                </Typography>
                {plan.price !== 'Özel' && (
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    /ay
                  </Typography>
                )}
              </Box>
              <Typography variant="body2" sx={{ color: '#64748B', mb: 3 }}>
                {plan.description}
              </Typography>

              <Divider sx={{ mb: 3 }} />

              <List sx={{ mb: 3, p: 0, flex: 1 }}>
                {plan.features.map((feature, idx) => (
                  <ListItem key={idx} sx={{ px: 0, py: 0.75 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleIcon sx={{ color: '#22C55E', fontSize: 18 }} />
                    </ListItemIcon>
                    {/* ✅ slotProps ile düzeltildi */}
                    <ListItemText
                      primary={feature}
                      slotProps={{
                        primary: {
                          variant: 'body2',
                          sx: { color: '#1E293B' },
                        },
                      }}
                    />
                  </ListItem>
                ))}
              </List>

              <PrimaryButton
                variant={plan.highlighted ? 'contained' : 'outlined'}
                fullWidth
                sx={{
                  mt: 'auto',
                  ...(plan.highlighted && {
                    boxShadow: '0 4px 16px rgba(11,94,215,0.25)',
                    '&:hover': {
                      boxShadow: '0 8px 32px rgba(11,94,215,0.35)',
                    },
                  }),
                }}
              >
                {plan.buttonText}
              </PrimaryButton>
            </Paper>
          </motion.div>
        ))}
      </Box>
    </SectionContainer>
  );
}

export default PricingSection;