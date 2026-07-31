// src/features/not-found/NotFoundPage.tsx
import React from 'react';
import { Box, Container, Typography, Button } from '@mui/material';
import { Home as HomeIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md" sx={{ py: 12, textAlign: 'center' }}>
      <Typography variant="h1" sx={{ fontSize: '6rem', fontWeight: 700, color: '#0B5ED7' }}>404</Typography>
      <Typography variant="h4" sx={{ fontWeight: 600, color: '#0F172A', mt: 2 }}>Sayfa Bulunamadı</Typography>
      <Typography variant="body1" sx={{ color: '#64748B', mt: 2, maxWidth: 400, mx: 'auto' }}>
        Aradığınız sayfa taşınmış veya silinmiş olabilir.
      </Typography>
      <Button variant="contained" startIcon={<HomeIcon />} onClick={() => navigate('/')} sx={{ mt: 4, borderRadius: 2, px: 4 }}>
        Ana Sayfaya Dön
      </Button>
    </Container>
  );
}