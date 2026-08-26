import { Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Divider, ListItemButton, Box, Typography } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import stokonomiLogo from '../../assets/brand/stokonomi-logo-horizontal-light.png';
import { useCurrentPilotDataset } from '../../features/dataset/api/pilotDatasetQueries';
import {
  LayoutDashboard,
  Shield,
  TrendingUp,
  Dice5,
  School,
  Truck,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  drawerWidth: number;
}

// ✅ Menü grupları - Lucide icon'lar ile
const menuGroups = [
  {
    title: 'GENEL',
    items: [
      { 
        path: '/dashboard', 
        label: 'Ana Panel', 
        icon: <LayoutDashboard size={18} strokeWidth={1.8} /> 
      },
    ]
  },
  {
    title: 'KLASİK ARAÇLAR',
    items: [
      {
        path: '/safety-stock', 
        label: 'Emniyet Stoku', 
        icon: <Shield size={18} strokeWidth={1.8} />,
        requiresDataset: true,
      },
      { 
        path: '/forecast', 
        label: 'Talep Tahmini', 
        icon: <TrendingUp size={18} strokeWidth={1.8} />,
        requiresDataset: true,
      },
      { 
        path: '/simulation', 
        label: 'Senaryo Simülasyonu', 
        icon: <Dice5 size={18} strokeWidth={1.8} />,
        requiresDataset: true,
      },
      { 
        path: '/backtest', 
        label: 'Geçmiş Performans Testi', 
        icon: <School size={18} strokeWidth={1.8} />,
        requiresDataset: true,
      },
    ]
  },
  {
    title: 'OPERASYON',
    items: [
      { 
        path: '/supplier', 
        label: 'Tedarikçi Analizi', 
        icon: <Truck size={18} strokeWidth={1.8} />,
        requiresDataset: true,
      },
    ]
  },
];

// ✅ Admin için ekstra menü
const adminItem = { 
  path: '/admin', 
  label: 'Admin Panel', 
  icon: <Sparkles size={18} strokeWidth={1.8} /> 
};

export default function Sidebar({ drawerWidth }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const currentDataset = useCurrentPilotDataset(user?.company_id);

  const isAdmin = user?.role === 'admin';

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#ffffff',
          borderRight: '1px solid #f0f0f0',
          boxShadow: '2px 0 12px rgba(0,0,0,0.04)',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* ✅ Logo Alanı */}
      <Toolbar sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        py: 2,
        minHeight: 64,
      }}>
        <Box
          sx={{
            width: 180,
            height: 55,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box
            component="img"
            src={stokonomiLogo}
            alt="Stokonomi - Karar Destek Platformu"
            sx={{
              width: '100%',
              maxWidth: 200,
              height: 60,
              objectFit: 'contain',
              display: 'block',
            }}
          />
        </Box>
      </Toolbar>
      
      <Divider sx={{ borderColor: '#f0f0f0', mb: 0.5 }} />

      {/* ✅ Menü Grupları */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 1 }}>
        <List sx={{ py: 0.5 }}>
          {menuGroups.map((group, groupIndex) => (
            <Box key={groupIndex}>
              {/* Grup Başlığı */}
              <Typography
                variant="caption"
                sx={{
                  px: 1.5,
                  py: 1,
                  display: 'block',
                  color: '#9e9e9e',
                  fontWeight: 600,
                  letterSpacing: '0.8px',
                  fontSize: '0.6rem',
                  textTransform: 'uppercase',
                }}
              >
                {group.title}
              </Typography>

              {/* Grup Öğeleri */}
              {group.items.map((item) => {
                const isActive = location.pathname === item.path;
                const requiresDataset = 'requiresDataset' in item && item.requiresDataset;
                const disabled = Boolean(requiresDataset && (currentDataset.isLoading || currentDataset.isError || !currentDataset.data));
                return (
                  <ListItem key={item.path} disablePadding sx={{ mb: 0.25 }}>
                    <ListItemButton
                      component={Link}
                      to={disabled ? '/dashboard' : item.path}
                      disabled={disabled}
                      aria-label={disabled ? `${item.label}: önce veri seti yükleyin` : item.label}
                      sx={{
                        borderRadius: 1.5,
                        py: 0.5,
                        px: 1.5,
                        position: 'relative',
                        backgroundColor: isActive ? '#f0f7ff' : 'transparent',
                        minHeight: 32,
                        '&:hover': {
                          backgroundColor: '#f5f5f5',
                        },
                        '& .MuiListItemIcon-root': {
                          minWidth: 32,
                          color: isActive ? '#1f4e79' : '#6b7280',
                        },
                        '& .MuiListItemText-primary': {
                          fontSize: '0.8rem',
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? '#1f4e79' : '#374151',
                        },
                      }}
                    >
                      {/* ✅ İnce Mavi Çizgi */}
                      {isActive && (
                        <Box
                          sx={{
                            position: 'absolute',
                            left: 0,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            width: 2.5,
                            height: 20,
                            backgroundColor: '#1f4e79',
                            borderRadius: '0 3px 3px 0',
                          }}
                        />
                      )}
                      
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.label} />
                    </ListItemButton>
                  </ListItem>
                );
              })}

              {/* ✅ Gruplar arası ayraç */}
              {groupIndex < menuGroups.length - 1 && (
                <Divider sx={{ borderColor: '#f0f0f0', my: 0.5 }} />
              )}
            </Box>
          ))}

          {/* ✅ Admin Paneli (varsa) */}
          {isAdmin && (
            <>
              <Divider sx={{ borderColor: '#f0f0f0', my: 0.5 }} />
              <Typography
                variant="caption"
                sx={{
                  px: 1.5,
                  py: 1,
                  display: 'block',
                  color: '#9e9e9e',
                  fontWeight: 600,
                  letterSpacing: '0.8px',
                  fontSize: '0.6rem',
                  textTransform: 'uppercase',
                }}
              >
                YÖNETİM
              </Typography>
              <ListItem key={adminItem.path} disablePadding sx={{ mb: 0.25 }}>
                <ListItemButton
                  component={Link}
                  to={adminItem.path}
                  sx={{
                    borderRadius: 1.5,
                    py: 0.5,
                    px: 1.5,
                    position: 'relative',
                    backgroundColor: location.pathname === adminItem.path ? '#f0f7ff' : 'transparent',
                    minHeight: 32,
                    '&:hover': {
                      backgroundColor: '#f5f5f5',
                    },
                    '& .MuiListItemIcon-root': {
                      minWidth: 32,
                      color: location.pathname === adminItem.path ? '#1f4e79' : '#6b7280',
                    },
                    '& .MuiListItemText-primary': {
                      fontSize: '0.8rem',
                      fontWeight: location.pathname === adminItem.path ? 600 : 400,
                      color: location.pathname === adminItem.path ? '#1f4e79' : '#374151',
                    },
                  }}
                >
                  {location.pathname === adminItem.path && (
                    <Box
                      sx={{
                        position: 'absolute',
                        left: 0,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 2.5,
                        height: 20,
                        backgroundColor: '#1f4e79',
                        borderRadius: '0 3px 3px 0',
                      }}
                    />
                  )}
                  <ListItemIcon>{adminItem.icon}</ListItemIcon>
                  <ListItemText primary={adminItem.label} />
                </ListItemButton>
              </ListItem>
            </>
          )}
        </List>
      </Box>

      {/* ✅ Footer - Versiyon bilgisi */}
      <Box
        sx={{
          borderTop: '1px solid #f0f0f0',
          py: 1.5,
          textAlign: 'center',
          backgroundColor: '#fafafa',
          flexShrink: 0,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: '#b0b0b0',
            fontSize: '0.6rem',
            letterSpacing: '0.5px',
            fontWeight: 400,
          }}
        >
          v2.0 • Premium
        </Typography>
      </Box>
    </Drawer>
  );
}
