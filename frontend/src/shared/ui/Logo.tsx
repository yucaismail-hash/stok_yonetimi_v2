// src/shared/ui/Logo.tsx
import React from 'react';
import { Box } from '@mui/material';

import logoHorizontalLight from '../../assets/brand/stokonomi-logo-horizontal-light.png';
import logoHorizontalDark from '../../assets/brand/stokonomi-logo-horizontal-dark.png';
import iconLight from '../../assets/brand/stokonomi-icon-light.png';
import iconDark from '../../assets/brand/stokonomi-icon-dark.png';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'dark' | 'light';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  small: {
    icon: 36,
    width: 170,
    height: 48,
  },
  medium: {
    icon: 44,
    width: 250,
    height: 70,
  },
  large: {
    icon: 56,
    width: 300,
    height: 82,
  },
};

export function Logo({
  size = 'medium',
  variant = 'default',
  showText = true,
  className = '',
}: LogoProps) {
  const {
    icon: iconSize,
    width: logoWidth,
    height: logoHeight,
  } = sizeMap[size];

  // variant="light" = koyu zemin üzerinde kullanılacak açık renk logo
  const isDarkBackground = variant === 'light';

  const logoSrc = showText
    ? isDarkBackground
      ? logoHorizontalDark
      : logoHorizontalLight
    : isDarkBackground
      ? iconLight
      : iconDark;

  return (
    <Box
      className={className}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        textDecoration: 'none',
        lineHeight: 0,
        flexShrink: 0,
      }}
    >
      <Box
        component="img"
        src={logoSrc}
        alt="Stokonomi - Karar Destek Platformu"
        sx={{
          width: showText ? logoWidth : iconSize,
          height: showText ? logoHeight : iconSize,
          objectFit: 'contain',
          display: 'block',
          flexShrink: 0,
        }}
      />
    </Box>
  );
}

export default Logo;