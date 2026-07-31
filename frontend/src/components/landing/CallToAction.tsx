// src/components/landing/CallToAction.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
} from '@mui/material';
import { ArrowForward as ArrowForwardIcon } from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { PrimaryButton } from '../ui';

export function CallToAction() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <Box
      ref={ref}
      sx={{
        py: 12,
        bgcolor: '#0B5ED7',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Glow Efekti */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 600,
          height: 600,
          background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto' }}>
            {/* ✅ Yeni Başlık */}
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', md: '3rem' },
                fontWeight: 700,
                color: 'white',
                mb: 1,
              }}
            >
              Daha Akıllı
              <br />
              Stok Kararları İçin
              <br />
              <Box component="span" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Bugün Başlayın.
              </Box>
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255,255,255,0.8)',
                fontSize: '1.125rem',
                mb: 4,
                mt: 2,
              }}
            >
              14 gün ücretsiz deneyin. Kredi kartı gerekmez.
            </Typography>

            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                justifyContent: 'center',
              }}
            >
              <PrimaryButton
                variant="contained"
                size="large"
                endIcon={<ArrowForwardIcon />}
                sx={{
                  bgcolor: 'white',
                  color: '#0B5ED7',
                  px: 4,
                  '&:hover': {
                    bgcolor: '#F8FAFC',
                    transform: 'scale(1.02)',
                  },
                }}
              >
                Ücretsiz Başla
              </PrimaryButton>
              <Button
                variant="outlined"
                size="large"
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255,255,255,0.3)',
                  px: 4,
                  py: 1.5,
                  borderRadius: '12px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  textTransform: 'none',
                  '&:hover': {
                    borderColor: 'white',
                    bgcolor: 'rgba(255,255,255,0.08)',
                  },
                }}
              >
                Demo İzle
              </Button>
            </Box>

            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255,255,255,0.5)',
                mt: 3,
                display: 'block',
              }}
            >
              • 14 gün ücretsiz • Hemen başlayın • İptal kolay
            </Typography>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}

export default CallToAction;