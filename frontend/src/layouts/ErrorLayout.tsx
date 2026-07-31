// src/layouts/ErrorLayout.tsx
import React from 'react';
import { Box, Container } from '@mui/material';

interface ErrorLayoutProps {
  children: React.ReactNode;
}

export default function ErrorLayout({ children }: ErrorLayoutProps) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#F8FAFC',
      }}
    >
      <Container maxWidth="md">
        {children}
      </Container>
    </Box>
  );
}