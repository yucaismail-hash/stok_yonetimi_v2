// src/pages/LandingPage/LandingPage.tsx
import React from 'react';
import { Box } from '@mui/material';
import Navbar from '../../components/landing/Navbar';
import Hero from '../../components/landing/Hero';
import StatsSection from '../../components/landing/StatsSection';
import ProblemSection from '../../components/landing/ProblemSection';
import SolutionSection from '../../components/landing/SolutionSection';
import ModulesSection from '../../components/landing/ModulesSection';
import AiSection from '../../components/landing/AiSection';
import FeaturesSection from '../../components/landing/FeaturesSection';
import SecuritySection from '../../components/landing/SecuritySection';
import PricingSection from '../../components/landing/PricingSection';
import CallToAction from '../../components/landing/CallToAction';
import Footer from '../../components/landing/Footer';

export function LandingPage() {
  return (
    <Box sx={{ bgcolor: 'white' }}>
      <Navbar />
      <Hero />
      <StatsSection />
      <ProblemSection />
      <SolutionSection />
      <ModulesSection />
      <AiSection />
      <FeaturesSection />
      <SecuritySection />
      <PricingSection />
      <CallToAction />
      <Footer />
    </Box>
  );
}

export default LandingPage;