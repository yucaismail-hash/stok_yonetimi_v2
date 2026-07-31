// src/layouts/ProductLayout.tsx
import React from 'react';
import { Box, Container } from '@mui/material';
import Navbar from '../features/landing/components/Navbar';
import Footer from '../features/landing/components/Footer';

interface ProductLayoutProps {
  children: React.ReactNode;
}

export default function ProductLayout({ children }: ProductLayoutProps) {
  return (
    <Box sx={{ bgcolor: 'white', minHeight: '100vh' }}>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 6 }}>
        {children}
      </Container>
      <Footer />
    </Box>
  );
}