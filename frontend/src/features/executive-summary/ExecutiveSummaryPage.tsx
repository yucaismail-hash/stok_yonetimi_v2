// src/features/executive-summary/ExecutiveSummaryPage.tsx
import React from 'react';
import { Box, Container, Typography, Paper, Grid, Chip, Divider } from '@mui/material';
import { Psychology, TrendingUp, TrendingDown, CheckCircle, Warning } from '@mui/icons-material';

export default function ExecutiveSummaryPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 8 }}>
      <Box sx={{ mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>Executive Summary</Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>
          Yönetici <Box component="span" sx={{ color: '#0B5ED7' }}>Özeti</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B', mt: 2, maxWidth: 600 }}>
          Analiz sonuçlarının özeti, AI yorumları ve aksiyon önerileri tek bir raporda.
        </Typography>
      </Box>

      <Paper sx={{ p: 4, borderRadius: 4, border: '1px solid #E2E8F0', bgcolor: '#F8FAFC' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Psychology sx={{ color: '#0B5ED7', fontSize: 32 }} />
          <Typography variant="h5" sx={{ fontWeight: 600, color: '#0F172A' }}>Stokonomi AI Analizi</Typography>
          <Chip label="v1.0" size="small" sx={{ ml: 'auto' }} />
        </Box>
        <Divider sx={{ mb: 3 }} />
        
        <Typography variant="body1" sx={{ color: '#1E293B', lineHeight: 1.8, mb: 4 }}>
          "9 ürün analiz edildi. 3 ürünün emniyet stoğu artırılmalı, 4 ürün azaltılabilir. 
          Yüksek riskli 3 ürün için Syntetos-Boylan metodu öneriliyor."
        </Typography>

        <Grid container spacing={3}>
          <Grid size={{ xs: 6, md: 3 }}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'white' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#0B5ED7' }}>9</Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>Toplam Ürün</Typography>
            </Paper>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'white' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#EF4444' }}>3</Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>Artırılacak</Typography>
            </Paper>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'white' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#22C55E' }}>4</Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>Azaltılacak</Typography>
            </Paper>
          </Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'white' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#F59E0B' }}>3</Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>Yüksek Riskli</Typography>
            </Paper>
          </Grid>
        </Grid>

        <Box sx={{ mt: 4, p: 3, bgcolor: 'white', borderRadius: 2, border: '1px solid #E2E8F0' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0F172A', mb: 2 }}>💡 Öneriler</Typography>
          {['Yüksek değişkenlik gösteren kalemler için Syntetos-Boylan uygulayın.', 'Z-segmenti kalemlerde stok seviyelerini gözden geçirin.', 'Sıfır talep gösteren kalemler için stoksuz çalışma stratejisi değerlendirin.']}
        </Box>
      </Paper>
    </Container>
  );
}