// src/components/ui/SectionContainer.tsx
import React from 'react';
import { Box, Container, SxProps, Theme } from '@mui/material';

interface SectionContainerProps {
  children: React.ReactNode;
  id?: string;
  bgcolor?: string;
  py?: number;
  sx?: SxProps<Theme>;
}

export function SectionContainer({
  children,
  id,
  bgcolor = 'transparent',
  py = 8,
  sx = {},
}: SectionContainerProps) {
  return (
    <Box
      id={id}
      sx={{
        py: { xs: py * 0.75, md: py },
        bgcolor: bgcolor,
        ...sx,
      }}
    >
      <Container maxWidth="xl">{children}</Container>
    </Box>
  );
}

export default SectionContainer;