// src/layouts/AuthLayout.tsx
import React from 'react';
import { Box, Container } from '@mui/material';
import Logo from '../shared/ui/Logo';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#F8FAFC',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Logo size="large" />
        </Box>
        {children}
      </Container>
    </Box>
  );
}