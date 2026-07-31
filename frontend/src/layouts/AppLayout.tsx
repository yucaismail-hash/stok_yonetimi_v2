// src/layouts/AppLayout.tsx
import React from 'react';
import { Box } from '@mui/material';
import Layout from '../components/Layout/Layout'; // ✅ Mevcut Layout'u kullan

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return <Layout>{children}</Layout>;
}