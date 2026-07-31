// src/features/pricing/PricingPage.tsx
import React from 'react';
import { Box, Container, Typography, Grid, Paper, Button, Chip, Divider, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { motion } from 'framer-motion';

const plans = [
  {
    name: 'Starter',
    price: '0',
    description: 'Küçük işletmeler için ideal',
    features: ['5 ürün analizi', 'Temel talep tahmini', 'Email desteği', '14 gün veri saklama'],
    highlighted: false,
    buttonText: 'Ücretsiz Başla',
  },
  {
    name: 'Professional',
    price: '499',
    description: 'Büyüyen işletmeler için',
    features: ['Sınırsız ürün analizi', 'AI destekli talep tahmini', 'Öncelikli destek', '90 gün veri saklama', 'Çoklu kullanıcı'],
    highlighted: true,
    buttonText: 'Ücretsiz Deneyin',
  },
  {
    name: 'Enterprise',
    price: 'Özel',
    description: 'Kurumsal ihtiyaçlar için',
    features: ['Özel AI modelleri', '7/24 destek', 'Sınırsız veri saklama', 'Özel SLA', 'Teknik müşteri yöneticisi'],
    highlighted: false,
    buttonText: 'İletişime Geç',
  },
];

export default function PricingPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>Fiyatlandırma</Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>
          İhtiyacınıza Uygun <Box component="span" sx={{ color: '#0B5ED7' }}>Planı Seçin</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B', mt: 2 }}>14 gün ücretsiz deneyin. Kredi kartı gerekmez.</Typography>
      </Box>

      <Grid container spacing={4} justifyContent="center">
        {plans.map((plan, index) => (
          <Grid size={{ xs: 12, md: 4 }} key={index}>
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }}>
              <Paper sx={{ p: 4, borderRadius: 4, border: plan.highlighted ? '2px solid #0B5ED7' : '1px solid #E2E8F0', height: '100%', position: 'relative' }}>
                {plan.highlighted && <Chip label="Popüler" sx={{ position: 'absolute', top: -12, right: 24, bgcolor: '#0B5ED7', color: 'white' }} />}
                <Typography variant="overline">{plan.name}</Typography>
                <Typography variant="h2" sx={{ fontSize: '2.5rem', fontWeight: 700, color: '#0F172A', mt: 1 }}>
                  {plan.price === 'Özel' ? 'Özel' : `₺${plan.price}`}
                  {plan.price !== 'Özel' && <Typography component="span" variant="body2" sx={{ color: '#64748B' }}>/ay</Typography>}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 3 }}>{plan.description}</Typography>
                <Divider sx={{ mb: 3 }} />
                <List sx={{ mb: 3 }}>
                  {plan.features.map((feature, idx) => (
                    <ListItem key={idx} sx={{ px: 0, py: 0.75 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}><CheckCircleIcon sx={{ color: '#22C55E', fontSize: 18 }} /></ListItemIcon>
                      <ListItemText primary={feature} primaryTypographyProps={{ variant: 'body2' }} />
                    </ListItem>
                  ))}
                </List>
                <Button variant={plan.highlighted ? 'contained' : 'outlined'} fullWidth sx={{ borderRadius: 2, py: 1.5 }}>
                  {plan.buttonText}
                </Button>
              </Paper>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}