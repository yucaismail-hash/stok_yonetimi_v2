// src/components/ui/PrimaryButton.tsx
import React from 'react';
import { Button, ButtonProps, SxProps, Theme } from '@mui/material';
import { alpha } from '@mui/material/styles';

interface PrimaryButtonProps extends ButtonProps {
  variant?: 'contained' | 'outlined' | 'text';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  sx?: SxProps<Theme>;
}

export function PrimaryButton({
  children,
  variant = 'contained',
  size = 'medium',
  fullWidth = false,
  sx = {},
  ...props
}: PrimaryButtonProps) {
  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      sx={{
        borderRadius: '12px',
        fontWeight: 600,
        textTransform: 'none',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
        },
        ...(variant === 'contained' && {
          boxShadow: '0 4px 16px rgba(11,94,215,0.15)',
          '&:hover': {
            boxShadow: '0 8px 32px rgba(11,94,215,0.25)',
          },
        }),
        ...(variant === 'outlined' && {
          borderColor: '#E2E8F0',
          '&:hover': {
            borderColor: '#0B5ED7',
            backgroundColor: 'rgba(11,94,215,0.04)',
          },
        }),
        ...sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
}

export default PrimaryButton;