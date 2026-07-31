// src/components/landing/Navbar.tsx
import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Box,
  Button,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Container,
  useScrollTrigger,
  Slide,
  Typography,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import { Logo } from '../ui';
import { useNavigate } from 'react-router-dom';

interface NavbarProps {
  isLoggedIn?: boolean;
}

const navItems = [
  { label: 'Ürün', href: '#products' },
  { label: 'Özellikler', href: '#features' },
  { label: 'Çözümler', href: '#solutions' },
  { label: 'Fiyatlandırma', href: '#pricing' },
  { label: 'Blog', href: '#blog' },
  { label: 'İletişim', href: '#contact' },
];

function HideOnScroll({ children }: { children: React.ReactElement }) {
  const trigger = useScrollTrigger();
  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

export function Navbar({ isLoggedIn = false }: NavbarProps) {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavClick = (href: string) => {
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
    setMobileOpen(false);
  };

  const drawer = (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Logo size="small" />
        <IconButton onClick={handleDrawerToggle}>
          <CloseIcon />
        </IconButton>
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItem
            key={item.label}
            onClick={() => handleNavClick(item.href)}
            sx={{
              borderRadius: 2,
              '&:hover': {
                bgcolor: 'rgba(11,94,215,0.04)',
              },
            }}
          >
            {/* ✅ Typography ile doğrudan render */}
            <Typography
              variant="body1"
              sx={{
                fontWeight: 500,
                color: '#1E293B',
                fontSize: '0.875rem',
              }}
            >
              {item.label}
            </Typography>
          </ListItem>
        ))}
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {isLoggedIn ? (
            <Button
              fullWidth
              variant="contained"
              onClick={() => navigate('/dashboard')}
            >
              Dashboard
            </Button>
          ) : (
            <>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => navigate('/login')}
              >
                Giriş Yap
              </Button>
              <Button
                fullWidth
                variant="contained"
                onClick={() => navigate('/register')}
              >
                Ücretsiz Başla
              </Button>
            </>
          )}
        </Box>
      </List>
    </Box>
  );

  return (
    <HideOnScroll>
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: scrolled
            ? 'rgba(255,255,255,0.85)'
            : 'transparent',
          backdropFilter: scrolled ? 'blur(12px)' : 'none',
          borderBottom: scrolled ? '1px solid #E2E8F0' : 'none',
          transition: 'all 0.3s ease-in-out',
        }}
      >
        <Container maxWidth="xl">
          <Toolbar sx={{ py: 1, justifyContent: 'space-between' }}>
            {/* Logo */}
            <Logo size="medium" />

            {/* Desktop Nav */}
            <Box
              sx={{
                display: { xs: 'none', md: 'flex' },
                alignItems: 'center',
                gap: 1,
              }}
            >
              {navItems.map((item) => (
                <Button
                  key={item.label}
                  color="inherit"
                  sx={{
                    color: '#1E293B',
                    fontWeight: 500,
                    fontSize: '0.875rem',
                    px: 2,
                    py: 1,
                    borderRadius: 2,
                    '&:hover': {
                      bgcolor: 'rgba(11,94,215,0.04)',
                    },
                  }}
                  onClick={() => handleNavClick(item.href)}
                >
                  {item.label}
                </Button>
              ))}
            </Box>

            {/* Desktop Actions */}
            <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 2 }}>
              {isLoggedIn ? (
                <Button
                  variant="contained"
                  onClick={() => navigate('/dashboard')}
                >
                  Dashboard
                </Button>
              ) : (
                <>
                  <Button
                    variant="text"
                    color="inherit"
                    sx={{
                      color: '#1E293B',
                      fontWeight: 500,
                      '&:hover': {
                        bgcolor: 'rgba(11,94,215,0.04)',
                      },
                    }}
                    onClick={() => navigate('/login')}
                  >
                    Giriş Yap
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => navigate('/register')}
                  >
                    Ücretsiz Başla
                  </Button>
                </>
              )}
            </Box>

            {/* Mobile Menu Button */}
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{
                display: { md: 'none' },
                color: '#1E293B',
              }}
            >
              <MenuIcon />
            </IconButton>
          </Toolbar>
        </Container>

        {/* Mobile Drawer */}
        <Drawer
          variant="temporary"
          anchor="right"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: 320,
            },
          }}
        >
          {drawer}
        </Drawer>
      </AppBar>
    </HideOnScroll>
  );
}

export default Navbar;