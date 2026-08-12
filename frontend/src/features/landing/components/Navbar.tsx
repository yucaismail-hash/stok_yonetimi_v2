// src/features/landing/components/Navbar.tsx
import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Box,
  Button,
  IconButton,
  Drawer,
  List,
  ListItemButton,
  Container,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import { useNavigate } from 'react-router-dom';
import { Logo } from '../../../shared/ui';

const navItems = [
  { label: 'Yaklaşım', href: '#yaklasim', isRoute: false },
  { label: 'Akademi', href: '/akademi', isRoute: true },
];

export function Navbar() {
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

  const handleNavClick = (item: { label: string; href: string; isRoute: boolean }) => {
    if (item.isRoute) {
      navigate(item.href);
      setMobileOpen(false);
    } else {
      const element = document.querySelector(item.href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
      setMobileOpen(false);
    }
  };

  const handleCtaClick = () => {
    const element = document.querySelector('#gelismeler');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
    setMobileOpen(false);
  };

  const drawer = (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 4,
        }}
      >
        <Logo size="small" />
        <IconButton onClick={handleDrawerToggle}>
          <CloseIcon />
        </IconButton>
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItemButton
            key={item.label}
            onClick={() => handleNavClick(item)}
            sx={{
              borderRadius: (theme) => theme.shape.borderRadius,
              '&:hover': {
                bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
              },
            }}
          >
            <Typography
              variant="body1"
              sx={{
                fontWeight: 500,
                color: (theme) => theme.palette.text.primary,
                fontSize: '0.875rem',
              }}
            >
              {item.label}
            </Typography>
          </ListItemButton>
        ))}
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Button
            fullWidth
            variant="contained"
            onClick={handleCtaClick}
          >
            Gelişmeleri Takip Et
          </Button>
        </Box>
      </List>
    </Box>
  );

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: scrolled
          ? (theme) => alpha(theme.palette.background.paper, 0.85)
          : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled
          ? (theme) => `1px solid ${theme.palette.divider}`
          : 'none',
        transition: 'all 0.3s ease-in-out',
      }}
    >
      <Container maxWidth="xl">
        <Toolbar sx={{ py: 1, justifyContent: 'space-between' }}>
          <Logo size="medium" />

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
                  color: (theme) => theme.palette.text.primary,
                  fontWeight: 500,
                  fontSize: '0.875rem',
                  px: 2,
                  py: 1,
                  borderRadius: (theme) => theme.shape.borderRadius,
                  '&:hover': {
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
                  },
                }}
                onClick={() => handleNavClick(item)}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              alignItems: 'center',
              gap: 2,
            }}
          >
            <Button
              variant="contained"
              onClick={handleCtaClick}
            >
              Gelişmeleri Takip Et
            </Button>
          </Box>

          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{
              display: { md: 'none' },
              color: (theme) => theme.palette.text.primary,
            }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </Container>

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
  );
}

export default Navbar;