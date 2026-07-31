// src/routes/routeConfig.ts
export interface RouteConfig {
  path: string;
  component: React.LazyExoticComponent<React.ComponentType<any>>;
  title: string;
  description?: string;
  requiresAuth?: boolean;
  layout?: 'landing' | 'product' | 'app' | 'auth' | 'error';
}

export const routeConfigs: RouteConfig[] = [
  // Public Routes
  {
    path: '/',
    component: lazy(() => import('../features/landing/LandingPage')),
    title: 'Stokonomi - AI Destekli Stok Yönetimi',
    description: 'Veriye dayalı stok kararları için AI destekli platform',
    layout: 'landing',
  },
  {
    path: '/login',
    component: lazy(() => import('../features/auth/LoginPage')),
    title: 'Giriş Yap - Stokonomi',
    layout: 'auth',
  },
  {
    path: '/register',
    component: lazy(() => import('../features/auth/RegisterPage')),
    title: 'Kayıt Ol - Stokonomi',
    layout: 'auth',
  },

  // Product Routes (Layout: product)
  {
    path: '/pricing',
    component: lazy(() => import('../features/pricing/PricingPage')),
    title: 'Fiyatlandırma - Stokonomi',
    layout: 'product',
  },
  {
    path: '/executive-summary',
    component: lazy(() => import('../features/executive-summary/ExecutiveSummaryPage')),
    title: 'Executive Summary - Stokonomi',
    layout: 'product',
  },
  {
    path: '/ai-analysis',
    component: lazy(() => import('../features/ai-analysis/AIAnalysisPage')),
    title: 'AI Analiz - Stokonomi',
    layout: 'product',
  },

  // Private Routes (Layout: app)
  {
    path: '/dashboard',
    component: lazy(() => import('../features/dashboard/DashboardPage')),
    title: 'Dashboard - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/safety-stock',
    component: lazy(() => import('../features/safety-stock/SafetyStockPage')),
    title: 'Emniyet Stoğu - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/forecast',
    component: lazy(() => import('../features/forecast/ForecastPage')),
    title: 'Talep Tahmini - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/simulation',
    component: lazy(() => import('../features/simulation/SimulationPage')),
    title: 'Simülasyon - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/backtest',
    component: lazy(() => import('../features/backtest/BacktestPage')),
    title: 'Backtest - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/supplier',
    component: lazy(() => import('../features/supplier/SupplierPage')),
    title: 'Tedarikçi Analizi - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/risk',
    component: lazy(() => import('../features/risk/RiskPage')),
    title: 'Risk Analizi - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/profile',
    component: lazy(() => import('../features/profile/ProfilePage')),
    title: 'Profil - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/admin',
    component: lazy(() => import('../features/admin/AdminPage')),
    title: 'Admin - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
  {
    path: '/tasks',
    component: lazy(() => import('../features/tasks/TaskListPage')),
    title: 'Görevler - Stokonomi',
    requiresAuth: true,
    layout: 'app',
  },
];