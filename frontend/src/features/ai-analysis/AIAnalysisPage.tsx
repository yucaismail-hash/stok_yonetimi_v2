// src/features/ai-analysis/AIAnalysisPage.tsx
import React from 'react';
import { Box, Container, Typography, Paper, Grid, Avatar, Chip, Stack } from '@mui/material';
import { Psychology, AutoAwesome, CheckCircle } from '@mui/icons-material';

const features = [
  'AI destekli analiz yorumları',
  'Executive Summary oluşturma',
  'Şirket analiz geçmişi ile karşılaştırma',
  'Analiz hafızası',
];

export default function AIAnalysisPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 8 }}>
      <Box sx={{ mb: 6 }}>
        <Chip icon={<AutoAwesome />} label="Yapay Zeka Motoru" sx={{ bgcolor: '#0B5ED7', color: 'white', mb: 2 }} />
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A' }}>Stokonomi AI</Typography>
        <Typography variant="h5" sx={{ color: '#64748B', mt: 1, fontWeight: 400 }}>
          Sadece Hesap Yapmaz. <Box component="span" sx={{ color: '#0B5ED7' }}>Karar Destek Sağlar.</Box>
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 4, borderRadius: 4, border: '1px solid #E2E8F0' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#0F172A', mb: 3 }}>AI Özellikleri</Typography>
            <Stack spacing={2}>
              {features.map((item, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#F8FAFC', borderRadius: 2 }}>
                  <CheckCircle sx={{ color: '#22C55E' }} />
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#0F172A' }}>{item}</Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 4, borderRadius: 4, border: '1px solid #E2E8F0', bgcolor: '#F8FAFC' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Avatar sx={{ bgcolor: '#0B5ED7' }}><Psychology /></Avatar>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#0F172A' }}>Stokonomi AI</Typography>
                <Typography variant="caption" sx={{ color: '#64748B' }}>v1.0 • Aktif</Typography>
              </Box>
              <Chip label="Canlı" size="small" sx={{ ml: 'auto', bgcolor: '#22C55E', color: 'white' }} />
            </Box>
            <Paper sx={{ p: 3, bgcolor: 'white', borderRadius: 2, border: '1px solid #E2E8F0' }}>
              <Typography variant="body2" sx={{ color: '#1E293B', lineHeight: 1.8, fontStyle: 'italic' }}>
                "Analiz tamamlandı. 124 ürün incelendi. 18 üründe fazla stok riski tespit edildi. 
                7 ürün için emniyet stoğu artırılması öneriliyor. En uygun tahmin yöntemi: Croston SBA"
              </Typography>
            </Paper>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}