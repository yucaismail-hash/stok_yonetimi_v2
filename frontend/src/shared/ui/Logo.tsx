// src/shared/ui/Logo.tsx
import React from 'react';
import { Box } from '@mui/material';

// Gerçek asset import'ları
import logoHorizontalDark from '../../assets/brand/stokonomi-logo-horizontal-dark.png';
import logoVerticalLight from '../../assets/brand/stokonomi-logo-vertical-light.png';
import iconLight from '../../assets/brand/stokonomi-icon-light.png';
import iconDark from '../../assets/brand/stokonomi-icon-dark.png';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'dark' | 'light';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  small: { icon: 28, width: 120 },
  medium: { icon: 36, width: 160 },
  large: { icon: 48, width: 200 },
};

export function Logo({
  size = 'medium',
  variant = 'default',
  showText = true,
  className = '',
}: LogoProps) {
  const { icon: iconSize, width: logoWidth } = sizeMap[size];

  // variant: 'light' → koyu zemin (light/white logo), 'default'/'dark' → açık zemin (dark logo)
  const isLightBackground = variant === 'light';

  // Asset seçimi: showText true → yatay logo, false → icon
  const logoSrc = showText
    ? isLightBackground
      ? logoHorizontalDark
      : logoVerticalLight
    : isLightBackground
      ? iconLight
      : iconDark;

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        alignItems: 'center',
        textDecoration: 'none',
      }}
    >
      <Box
        component="img"
        src={logoSrc}
        alt="Stokonomi"
        sx={{
          width: showText ? logoWidth : iconSize,
          height: iconSize,
          objectFit: 'contain',
          flexShrink: 0,
          display: 'block',
        }}
        onError={(e) => {
          // Asset yüklenemezse görseli gizle, layout korunsun
          e.currentTarget.style.display = 'none';
        }}
      />
    </Box>
  );
}

export default Logo;