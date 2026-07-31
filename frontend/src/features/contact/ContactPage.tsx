// src/features/contact/ContactPage.tsx
import React from 'react';
import { Box, Container, Typography, Paper, TextField, Button, Grid } from '@mui/material';
import { Email, Phone, LocationOn } from '@mui/icons-material';

export default function ContactPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>İletişim</Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>Bizimle <Box component="span" sx={{ color: '#0B5ED7' }}>İletişime Geçin</Box></Typography>
        <Typography variant="body1" sx={{ color: '#64748B', mt: 2 }}>Sorularınız için size yardımcı olmaktan mutluluk duyarız.</Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Paper sx={{ p: 4, borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#0F172A', mb: 3 }}>İletişim Bilgileri</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Email sx={{ color: '#0B5ED7' }} /><Typography variant="body2" color="#64748B">info@stokonomi.com</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Phone sx={{ color: '#0B5ED7' }} /><Typography variant="body2" color="#64748B">+90 (555) 123 45 67</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <LocationOn sx={{ color: '#0B5ED7' }} /><Typography variant="body2" color="#64748B">İstanbul, Türkiye</Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          <Paper sx={{ p: 4, borderRadius: 3, border: '1px solid #E2E8F0' }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 6 }}><TextField fullWidth label="Ad Soyad" variant="outlined" /></Grid>
              <Grid size={{ xs: 6 }}><TextField fullWidth label="E-posta" variant="outlined" type="email" /></Grid>
              <Grid size={{ xs: 12 }}><TextField fullWidth label="Konu" variant="outlined" /></Grid>
              <Grid size={{ xs: 12 }}><TextField fullWidth label="Mesaj" variant="outlined" multiline rows={4} /></Grid>
              <Grid size={{ xs: 12 }}><Button variant="contained" fullWidth sx={{ py: 1.5, borderRadius: 2, mt: 1 }}>Gönder</Button></Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}