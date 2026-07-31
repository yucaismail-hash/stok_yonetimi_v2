// src/features/privacy/PrivacyPage.tsx
import React from 'react';
import { Container, Typography, Paper } from '@mui/material';

export default function PrivacyPage() {
  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mb: 4 }}>Gizlilik Politikası</Typography>
      <Paper sx={{ p: 4, borderRadius: 3, border: '1px solid #E2E8F0' }}>
        <Typography variant="body1" sx={{ color: '#64748B', lineHeight: 1.8 }}>Bu sayfa gizlilik politikası içeriği ile doldurulacaktır.</Typography>
      </Paper>
    </Container>
  );
}