import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout/Layout';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ForecastPage from './pages/ForecastPage';
import SafetyStockPage from './pages/SafetyStockPage';
import SimulationPage from './pages/SimulationPage';
import BacktestPage from './pages/BacktestPage';
import SupplierPage from './pages/SupplierPage';
import RiskPage from './pages/RiskPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import TaskListPage from './pages/TaskListPage';
import { useAuth } from './hooks/useAuth';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 🎨 Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

const queryClient = new QueryClient();

// 🔒 Private Route Component - Outlet kullanımı için
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

// 🚀 App Routes
function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes - Layout'sız */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* 🔒 Private Routes - Layout ile (Outlet kullanıyor) */}
      <Route element={<PrivateRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/safety-stock" element={<SafetyStockPage />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="/supplier" element={<SupplierPage />} />
        <Route path="/risk" element={<RiskPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/tasks" element={<TaskListPage />} />
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