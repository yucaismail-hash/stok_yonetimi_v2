import { AppBar, Toolbar, Typography, IconButton, Badge, Avatar, Menu, MenuItem, Chip, Box, Popover, List, ListItem, ListItemText, ListItemIcon, Button, Divider, Tabs, Tab } from '@mui/material';
import { Notifications, Logout, CheckCircle, Warning, Error, Info, Close } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface NavbarProps {
  drawerWidth: number;
}

interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  link?: string;
  created_at: string;
}

export default function Navbar({ drawerWidth }: NavbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    handleClose();
  };

  const handleProfile = () => {
    navigate('/profile');
    handleClose();
  };

  // ✅ Bildirim Popover
  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
    fetchNotifications();
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  // ✅ Bildirimleri getir
  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/notifications/?limit=20');
      if (res.data.success) {
        setNotifications(res.data.notifications || []);
      }
    } catch (error) {
      console.error('❌ Bildirim hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Okunmamış sayısını getir
  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/api/notifications/unread-count');
      setUnreadCount(res.data.unread_count || 0);
    } catch (error) {
      console.error('❌ Okunmamış bildirim hatası:', error);
    }
  };

  // ✅ Bildirimi okundu işaretle
  const markAsRead = async (id: number) => {
    try {
      await api.post(`/api/notifications/mark-read/${id}`);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('❌ Bildirim okundu hatası:', error);
    }
  };

  // ✅ Tümünü okundu işaretle
  const markAllAsRead = async () => {
    try {
      await api.post('/api/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('❌ Tümünü okundu hatası:', error);
    }
  };

  // ✅ Bildirim tıklama
  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    if (notification.link) {
      navigate(notification.link);
      handleNotificationClose();
    }
  };

  // ✅ Bildirim icon'u
  const getNotificationIcon = (type: string) => {
    switch(type) {
      case 'success': return <CheckCircle sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main', fontSize: 20 }} />;
      case 'error': return <Error sx={{ color: 'error.main', fontSize: 20 }} />;
      default: return <Info sx={{ color: 'info.main', fontSize: 20 }} />;
    }
  };

  // ✅ Her 30 saniyede bir bildirimleri kontrol et
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const open = Boolean(notificationAnchor);

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { sm: `calc(100% - ${drawerWidth}px)` },
        ml: { sm: `${drawerWidth}px` },
        backgroundColor: '#fff',
        color: '#1f4e79',
        boxShadow: 1,
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          📊 Stokonomi
        </Typography>

        <Chip
          label={`🪙 ${user?.token_balance || 0}`}
          size="small"
          sx={{ mr: 2, bgcolor: '#e3f2fd' }}
        />

        {/* ✅ Bildirim Butonu */}
        <IconButton 
          color="inherit" 
          onClick={handleNotificationOpen}
          sx={{ mr: 1 }}
        >
          <Badge badgeContent={unreadCount} color="error">
            <Notifications />
          </Badge>
        </IconButton>

        {/* ✅ Bildirim Popover - DÜZELTİLDİ */}
        <Popover
          open={open}
          anchorEl={notificationAnchor}
          onClose={handleNotificationClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          slotProps={{
            paper: {
              sx: { width: 400, maxHeight: 500, overflow: 'hidden' }
            }
          }}
        >
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee' }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
              Bildirimler
            </Typography>
            {unreadCount > 0 && (
              <Button size="small" onClick={markAllAsRead}>
                Tümünü Okundu İşaretle
              </Button>
            )}
          </Box>
          
          <Box sx={{ maxHeight: 380, overflowY: 'auto' }}>
            {loading ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">Yükleniyor...</Typography>
              </Box>
            ) : notifications.length === 0 ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">Henüz bildirim yok</Typography>
              </Box>
            ) : (
              notifications.map((notification) => (
                <ListItem
                  key={notification.id}
                  sx={{
                    cursor: 'pointer',
                    bgcolor: notification.is_read ? 'transparent' : '#f0f7ff',
                    '&:hover': { bgcolor: '#e3f2fd' },
                    borderBottom: '1px solid #f5f5f5'
                  }}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getNotificationIcon(notification.type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={notification.title}
                    secondary={notification.message}
                    slotProps={{
                      primary: { 
                        variant: 'body2', 
                        sx: { fontWeight: notification.is_read ? 'normal' : 'bold' } 
                      },
                      secondary: { 
                        variant: 'caption',
                        sx: { display: 'block', mt: 0.5 }
                      }
                    }}
                  />
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); markAsRead(notification.id); }}>
                    <Close fontSize="small" />
                  </IconButton>
                </ListItem>
              ))
            )}
          </Box>
          
          <Divider />
          <Box sx={{ p: 1, textAlign: 'center' }}>
            <Button size="small" onClick={() => { handleNotificationClose(); navigate('/profile'); }}>
              Tüm Bildirimleri Gör
            </Button>
          </Box>
        </Popover>

        {/* ✅ Kullanıcı Menüsü */}
        <IconButton onClick={handleMenu} color="inherit">
          <Avatar sx={{ width: 32, height: 32, bgcolor: '#1f4e79' }}>
            {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
          </Avatar>
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          keepMounted
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          open={Boolean(anchorEl)}
          onClose={handleClose}
        >
          <MenuItem onClick={handleProfile}>Profil</MenuItem>
          <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
            <Logout fontSize="small" sx={{ mr: 1 }} /> Çıkış Yap
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}