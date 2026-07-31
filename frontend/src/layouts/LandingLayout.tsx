// src/layouts/LandingLayout.tsx
import React from 'react';
import { Box } from '@mui/material';
import Navbar from '../features/landing/components/Navbar';
import Footer from '../features/landing/components/Footer';

interface LandingLayoutProps {
  children: React.ReactNode;
}

export default function LandingLayout({ children }: LandingLayoutProps) {
  return (
    <Box sx={{ bgcolor: 'white', minHeight: '100vh' }}>
      <Navbar />
      {children}
      <Footer />
    </Box>
  );
}