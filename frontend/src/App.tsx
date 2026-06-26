import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout/Layout';
import DashboardPage from './pages/DashboardPage';
import PatternPage from './pages/PatternPage_silindi';
import SafetyStockPage from './pages/SafetyStockPage';
import ForecastPage from './pages/ForecastPage';
import SimulationPage from './pages/SimulationPage';
import BacktestPage from './pages/BacktestPage';
import SupplierPage from './pages/SupplierPage';
import TaskListPage from './pages/TaskListPage';
import AdminPage from './pages/AdminPage';
import ProfilePage from './pages/ProfilePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import LandingPage from './pages/LandingPage';

const theme = createTheme({
  palette: {
    primary: { main: '#1f4e79' },
    secondary: { main: '#dc004e' },
  },
});

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            {/* Landing Page - Layoutsız */}
            <Route path="/" element={<LandingPage />} />
            
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Ana uygulama - Layout ile */}
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/safety-stock" element={<SafetyStockPage />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/simulation" element={<SimulationPage />} />
              <Route path="/backtest" element={<BacktestPage />} />
              <Route path="/supplier" element={<SupplierPage />} />
              <Route path="/tasks" element={<TaskListPage />} /> {/* ✅ Yeni route */}
              <Route path="/admin" element={<AdminPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;