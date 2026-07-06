import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout/Layout';
import DashboardPage from './pages/DashboardPage';
import ForecastPage from './pages/ForecastPage';
import SafetyStockPage from './pages/SafetyStockPage';
import SimulationPage from './pages/SimulationPage';
import BacktestPage from './pages/BacktestPage';
import SupplierPage from './pages/SupplierPage';
import TaskListPage from './pages/TaskListPage';
import AdminPage from './pages/AdminPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import LandingPage from './pages/LandingPage';
import ProfilePage from './pages/ProfilePage';

// ✅ PrivateRoute Bileşeni - Zustand ile uyumlu
const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const { user, isLoading } = useAuth();
  
  // ✅ Loading durumunda bekle
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        Yükleniyor...
      </div>
    );
  }
  
  // ✅ Kullanıcı yoksa login sayfasına yönlendir
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes - Giriş yapmadan erişilebilir */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Private Routes - Giriş gerektirir */}
        <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/safety-stock" element={<SafetyStockPage />} />
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/supplier" element={<SupplierPage />} />
          <Route path="/tasks" element={<TaskListPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
        
        {/* 404 - Tanımlı olmayan route'lar */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;