// src/features/landing/LandingPage.tsx
import React from 'react';
import { Box } from '@mui/material';

// ✅ YENİ YOLLAR (components/landing/ yerine ./components/)
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import StatsSection from './components/StatsSection';
import HowItWorks from './components/HowItWorks';
import ProblemSection from './components/ProblemSection';
import SolutionSection from './components/SolutionSection';
import ModulesSection from './components/ModulesSection';
import AiSection from './components/AiSection';
import FeaturesSection from './components/FeaturesSection';
import SecuritySection from './components/SecuritySection';
import PricingSection from './components/PricingSection';
import CallToAction from './components/CallToAction';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <Box sx={{ bgcolor: 'white' }}>
      <Navbar />
      <Hero />
      <StatsSection />
      <HowItWorks />
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