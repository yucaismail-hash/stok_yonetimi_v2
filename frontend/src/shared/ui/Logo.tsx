// src/shared/ui/Logo.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'dark' | 'light';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  small: { icon: 28, text: '1.1rem', gap: 1 },
  medium: { icon: 36, text: '1.5rem', gap: 1.5 },
  large: { icon: 48, text: '2rem', gap: 2 },
};

const colorMap = {
  default: '#0B5ED7',
  dark: '#0F172A',
  light: '#FFFFFF',
};

export function Logo({
  size = 'medium',
  variant = 'default',
  showText = true,
  className = '',
}: LogoProps) {
  const { icon: iconSize, text: textSize, gap } = sizeMap[size];
  const color = colorMap[variant];

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: gap,
        textDecoration: 'none',
      }}
    >
      <Box
        component="img"
        src="/logo/icon.png"
        alt="Stokonomi"
        sx={{
          width: iconSize,
          height: iconSize,
          objectFit: 'contain',
          flexShrink: 0,
        }}
        onError={(e) => {
          // Logo yoksa placeholder
          e.currentTarget.style.display = 'none';
          const parent = e.currentTarget.parentElement;
          if (parent) {
            const placeholder = document.createElement('div');
            placeholder.style.cssText = `
              width: ${iconSize}px;
              height: ${iconSize}px;
              background: ${color};
              border-radius: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-weight: 700;
              font-size: ${iconSize / 2}px;
              font-family: Inter, sans-serif;
            `;
            placeholder.textContent = 'S';
            parent.appendChild(placeholder);
          }
        }}
      />

      {showText && (
        <Typography
          component="span"
          sx={{
            fontWeight: 700,
            fontSize: textSize,
            color: color,
            letterSpacing: '-0.02em',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          STOKONOMI
        </Typography>
      )}
    </Box>
  );
}

export default Logo;