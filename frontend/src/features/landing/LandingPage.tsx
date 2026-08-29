// src/features/landing/LandingPage.tsx
import React from 'react';
import { Box } from '@mui/material';

import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ProblemSection from './components/ProblemSection';
import ApproachSection from './components/ApproachSection';
import DecisionSystemSection from './components/DecisionSystemSection';
import IntelligenceLevelsSection from './components/IntelligenceLevelsSection';
import HumanAiSection from './components/HumanAiSection';
import FreeEntrySection from './components/FreeEntrySection';
import AcademySection from './components/AcademySection';
import DevelopmentStatusSection from './components/DevelopmentStatusSection';
import FinalCtaSection from './components/FinalCtaSection';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <Box sx={{ bgcolor: 'white' }}>
      <Navbar />
      <Hero />
      <ProblemSection />
      <ApproachSection />
      <DecisionSystemSection />
      <IntelligenceLevelsSection />
      <HumanAiSection />
      <FreeEntrySection />
      <AcademySection />
      <DevelopmentStatusSection />
      <FinalCtaSection />
      <Footer />
    </Box>
  );
}
