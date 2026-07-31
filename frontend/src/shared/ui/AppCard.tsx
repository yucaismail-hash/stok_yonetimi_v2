// src/components/ui/AppCard.tsx
import React from 'react';
import { Card, CardProps, SxProps, Theme } from '@mui/material';

interface AppCardProps extends CardProps {
  hover?: boolean;
  sx?: SxProps<Theme>;
}

export function AppCard({
  children,
  hover = true,
  sx = {},
  ...props
}: AppCardProps) {
  return (
    <Card
      sx={{
        borderRadius: '20px',
        border: '1px solid #E2E8F0',
        boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
        transition: 'all 0.3s ease-in-out',
        ...(hover && {
          '&:hover': {
            boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
            transform: 'translateY(-4px)',
          },
        }),
        ...sx,
      }}
      {...props}
    >
      {children}
    </Card>
  );
}

export default AppCard;