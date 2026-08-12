// src/features/landing/LandingPage.tsx
import React from 'react';
import { Box } from '@mui/material';

import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ProblemSection from './components/ProblemSection';
import ApproachSection from './components/ApproachSection';
import HumanAiSection from './components/HumanAiSection';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <Box sx={{ bgcolor: 'white' }}>
      <Navbar />
      <Hero />
      <ProblemSection />
      <ApproachSection />
      <HumanAiSection />
      <Footer />
    </Box>
  );
}