// src/layouts/index.ts
import React from 'react';

// ✅ Layout'lar (Phase 3'te doldurulacak)
import LandingLayout from './LandingLayout';
import ProductLayout from './ProductLayout';
import AppLayout from './AppLayout';
import AuthLayout from './AuthLayout';
import ErrorLayout from './ErrorLayout';

export type LayoutName = 'landing' | 'product' | 'app' | 'auth' | 'error';

export const layouts: Record<LayoutName, React.ComponentType<any>> = {
  landing: LandingLayout,
  product: ProductLayout,
  app: AppLayout,
  auth: AuthLayout,
  error: ErrorLayout,
};

export const getLayout = (name: LayoutName): React.ComponentType<any> => {
  return layouts[name] || layouts.app;
};

// Layout'ları export et
export { default as LandingLayout } from './LandingLayout';
export { default as ProductLayout } from './ProductLayout';
export { default as AppLayout } from './AppLayout';
export { default as AuthLayout } from './AuthLayout';
export { default as ErrorLayout } from './ErrorLayout';