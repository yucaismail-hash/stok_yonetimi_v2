// src/theme.ts
import { createTheme } from '@mui/material/styles';

// Stokonomi Renk Paleti
const colors = {
  primary: {
    main: '#0B5ED7',
    light: '#2F80ED',
    dark: '#094AB5',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#2F80ED',
    light: '#5B9CF5',
    dark: '#1A6BC4',
    contrastText: '#FFFFFF',
  },
  success: {
    main: '#22C55E',
    light: '#4ADE80',
    dark: '#16A34A',
    contrastText: '#FFFFFF',
  },
  warning: {
    main: '#F59E0B',
    light: '#FBBF24',
    dark: '#D97706',
    contrastText: '#FFFFFF',
  },
  error: {
    main: '#EF4444',
    light: '#F87171',
    dark: '#DC2626',
    contrastText: '#FFFFFF',
  },
  background: {
    default: '#F8FAFC',
    paper: '#FFFFFF',
  },
  text: {
    primary: '#0F172A',
    secondary: '#64748B',
  },
  divider: '#E2E8F0',
};

// Font Ailesi
const fontFamily = '"Inter", "Roboto", "Helvetica", "Arial", sans-serif';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    background: colors.background,
    text: colors.text,
    divider: colors.divider,
  },
  typography: {
    fontFamily: fontFamily,
    h1: {
      fontSize: '4.5rem', // 72px
      fontWeight: 700,
      lineHeight: 1.1,
      letterSpacing: '-0.02em',
      color: colors.text.primary,
    },
    h2: {
      fontSize: '3rem', // 48px
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      color: colors.text.primary,
    },
    h3: {
      fontSize: '2.25rem', // 36px
      fontWeight: 700,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
      color: colors.text.primary,
    },
    h4: {
      fontSize: '1.5rem', // 24px
      fontWeight: 600,
      lineHeight: 1.4,
      color: colors.text.primary,
    },
    h5: {
      fontSize: '1.25rem', // 20px
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.text.primary,
    },
    h6: {
      fontSize: '1rem', // 16px
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.text.primary,
    },
    body1: {
      fontSize: '1.125rem', // 18px
      fontWeight: 400,
      lineHeight: 1.7,
      color: colors.text.secondary,
    },
    body2: {
      fontSize: '0.875rem', // 14px
      fontWeight: 400,
      lineHeight: 1.6,
      color: colors.text.secondary,
    },
    caption: {
      fontSize: '0.75rem', // 12px
      fontWeight: 400,
      lineHeight: 1.5,
      color: colors.text.secondary,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      color: colors.primary.main,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '10px 24px',
          fontWeight: 600,
          textTransform: 'none',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
        contained: {
          boxShadow: '0 4px 16px rgba(11,94,215,0.15)',
          '&:hover': {
            boxShadow: '0 8px 32px rgba(11,94,215,0.25)',
          },
        },
        outlined: {
          borderColor: colors.divider,
          '&:hover': {
            borderColor: colors.primary.main,
            backgroundColor: 'rgba(11,94,215,0.04)',
          },
        },
        sizeLarge: {
          padding: '14px 36px',
          fontSize: '1rem',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          border: `1px solid ${colors.divider}`,
          boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
          transition: 'all 0.3s ease-in-out',
        },
        elevation1: {
          boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
        },
        elevation2: {
          boxShadow: '0 8px 40px rgba(0,0,0,0.06)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          border: `1px solid ${colors.divider}`,
          boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
            transform: 'translateY(-4px)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          fontWeight: 600,
        },
      },
    },
    MuiContainer: {
      styleOverrides: {
        root: {
          paddingLeft: 24,
          paddingRight: 24,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
        },
      },
    },
  },
});

export default theme;