// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ✅ Theme import
import theme from './theme';

// ✅ Layout
import Layout from './components/Layout/Layout';

// ✅ YENİ IMPORTLAR - DOĞRUDAN features/ klasöründen
import LandingPage from './features/landing/LandingPage';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import DashboardPage from './features/dashboard/DashboardPage';
import ForecastPage from './features/forecast/ForecastPage';
import SafetyStockPage from './features/safety-stock/SafetyStockPage';
import SimulationPage from './features/simulation/SimulationPage';
import BacktestPage from './features/backtest/BacktestPage';
import SupplierPage from './features/supplier/SupplierPage';
import RiskPage from './features/risk/RiskPage';
import ProfilePage from './features/profile/ProfilePage';
import AdminPage from './features/admin/AdminPage';
import TaskListPage from './features/tasks/TaskListPage';

// ✅ ACADEMY
import { AcademyPage, ArticlePage } from './features/academy';

import { useAuth } from './hooks/useAuth';
import { useCurrentPilotDataset } from './features/dataset/api/pilotDatasetQueries';

const queryClient = new QueryClient();

// 🔒 Private Route Component
function PrivateRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Yükleniyor...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout />;
}

function AdminRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Yükleniyor...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <AdminPage />;
}

function DatasetRequiredRoute() {
  const { user } = useAuth();
  const currentDataset = useCurrentPilotDataset(user?.company_id);

  if (currentDataset.isLoading) return <div>Veri seti durumu kontrol ediliyor...</div>;
  if (currentDataset.isError) {
    return <div role="alert">Veri seti durumu alınamadı. <button type="button" onClick={() => currentDataset.refetch()}>Tekrar dene</button></div>;
  }
  if (!currentDataset.data) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

// 🚀 App Routes
function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* ✅ Academy Public Routes */}
      <Route path="/akademi" element={<AcademyPage />} />
      <Route path="/akademi/:slug" element={<ArticlePage />} />

      {/* Private Routes */}
      <Route element={<PrivateRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route element={<DatasetRequiredRoute />}>
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/safety-stock" element={<SafetyStockPage />} />
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/supplier" element={<SupplierPage />} />
          <Route path="/tasks" element={<TaskListPage />} />
        </Route>
        <Route path="/risk" element={<RiskPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/admin" element={<AdminRoute />} />
      </Route>
    </Routes>
  );
}

// 📦 Main App Component
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
