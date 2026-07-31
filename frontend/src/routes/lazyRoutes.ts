// src/routes/lazyRoutes.ts
import { lazy } from 'react';

// ✅ Mevcut Sayfalar - Lazy Loading ile
export const LandingPage = lazy(() => import('../features/landing/LandingPage'));
export const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage'));
export const SafetyStockPage = lazy(() => import('../features/safety-stock/SafetyStockPage'));
export const ForecastPage = lazy(() => import('../features/forecast/ForecastPage'));
export const SimulationPage = lazy(() => import('../features/simulation/SimulationPage'));
export const BacktestPage = lazy(() => import('../features/backtest/BacktestPage'));
export const SupplierPage = lazy(() => import('../features/supplier/SupplierPage'));
export const RiskPage = lazy(() => import('../features/risk/RiskPage'));
export const ProfilePage = lazy(() => import('../features/profile/ProfilePage'));
export const AdminPage = lazy(() => import('../features/admin/AdminPage'));
export const TaskListPage = lazy(() => import('../features/tasks/TaskListPage'));
export const LoginPage = lazy(() => import('../features/auth/LoginPage'));
export const RegisterPage = lazy(() => import('../features/auth/RegisterPage'));

// ✅ Yeni Sayfalar
export const PricingPage = lazy(() => import('../features/pricing/PricingPage'));
export const ExecutiveSummaryPage = lazy(() => import('../features/executive-summary/ExecutiveSummaryPage'));
export const AIAnalysisPage = lazy(() => import('../features/ai-analysis/AIAnalysisPage'));
export const NotFoundPage = lazy(() => import('../features/not-found/NotFoundPage'));