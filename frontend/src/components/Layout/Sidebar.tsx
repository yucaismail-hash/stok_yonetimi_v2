import { Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Divider, ListItemButton } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import SecurityIcon from '@mui/icons-material/Security';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TuneIcon from '@mui/icons-material/Tune';
import BackpackIcon from '@mui/icons-material/Backpack';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import WarningIcon from '@mui/icons-material/Warning';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import { useAuth } from '../../hooks/useAuth';

interface SidebarProps {
  drawerWidth: number;
}

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/pattern', label: 'Pattern Analizi', icon: <AnalyticsIcon /> },
  { path: '/safety-stock', label: 'Emniyet Stoku', icon: <SecurityIcon /> },
  { path: '/forecast', label: 'Talep Tahmini', icon: <ShowChartIcon /> },
  { path: '/simulation', label: 'Simülasyon', icon: <TuneIcon /> },
  { path: '/backtest', label: 'Backtest', icon: <BackpackIcon /> },
  { path: '/supplier', label: 'Tedarikçi', icon: <LocalShippingIcon /> },
];

const adminItem = { path: '/admin', label: 'Admin Panel', icon: <AdminPanelSettingsIcon /> };

export default function Sidebar({ drawerWidth }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();

  const isAdmin = user?.email === 'admin@stok.com';
  const allMenuItems = isAdmin ? [...menuItems, adminItem] : menuItems;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <Divider />
      <List>
        {allMenuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: '#e3f2fd',
                  borderRight: '4px solid #1f4e79',
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}