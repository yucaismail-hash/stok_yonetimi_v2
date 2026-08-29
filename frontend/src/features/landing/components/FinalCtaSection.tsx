// src/features/landing/components/FinalCtaSection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Stack,
  Button,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { PUBLIC_ANALYTICS_EVENTS, trackPublicEvent } from '../../../shared/analytics/ga';

export function FinalCtaSection() {
  return (
    <Box
      id="final-cta"
      sx={{
        py: { xs: 8, md: 9 },
        bgcolor: (theme) => theme.palette.text.primary,
        position: 'relative',
        overflow: 'hidden',
        borderBottom: (theme) =>
          `1px solid ${alpha(theme.palette.common.white, 0.06)}`,
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          right: '-10%',
          width: { xs: 300, md: 600 },
          height: { xs: 300, md: 600 },
          background: (theme) =>
            `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.08)} 0%, transparent 70%)`,
          borderRadius: '50%',
          transform: 'translateY(-50%)',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            maxWidth: 760,
            mx: 'auto',
            textAlign: 'center',
          }}
        >
          <Typography
            variant="overline"
            sx={{
              color: (theme) => theme.palette.primary.main,
              fontWeight: 600,
              letterSpacing: '1px',
              display: 'block',
              mb: 1.5,
            }}
          >
            STOKONOMİ
          </Typography>

          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              color: (theme) => theme.palette.common.white,
              mb: 2,
              fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },
              lineHeight: 1.2,
            }}
          >
            Belirsizliği daha görünür,
            <br />
            <Box
              component="span"
              sx={{
                background: (theme) =>
                  `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              kararları daha güçlü
            </Box>
            <br />
            hale getirmek için.
          </Typography>

          <Typography
            variant="body1"
            sx={{
              color: (theme) => alpha(theme.palette.common.white, 0.7),
              maxWidth: 600,
              mx: 'auto',
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
              mb: 3,
            }}
          >
            Bireysel analizlerle ücretsiz başlayın; Business Workflow'un ilk
            5 başarılı çalıştırmasında tam karar çıktılarını deneyin.
          </Typography>

          <Box
            sx={{
              display: 'inline-block',
              px: { xs: 2.5, md: 4 },
              py: { xs: 1.5, md: 2 },
              mb: 4,
              borderRadius: (theme) => theme.shape.borderRadius,
              border: (theme) =>
                `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
              bgcolor: (theme) => alpha(theme.palette.common.white, 0.04),
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 500,
                color: (theme) => theme.palette.common.white,
                fontSize: { xs: '1rem', md: '1.2rem' },
                letterSpacing: '0.02em',
              }}
            >
              "Hesaplar. Doğrular. Öğrenir."
            </Typography>
          </Box>

          <Typography
            variant="body2"
            sx={{
              color: (theme) => alpha(theme.palette.common.white, 0.5),
              maxWidth: 520,
              mx: 'auto',
              lineHeight: 1.7,
              fontSize: '0.875rem',
              mb: 4,
            }}
          >
            İlk günden matematiksel yöntemlerle çalışır,
            sonuçları test eder ve kullanım arttıkça
            öğrenme katmanlarını geliştirir.
          </Typography>

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
            sx={{ justifyContent: 'center', mb: 3 }}
          >
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForwardIcon />}
              component={Link}
              to="/register"
              onClick={() => trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.LANDING_FREE_START_CLICK, { placement: 'final_cta', destination: '/register' })}
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: (theme) => theme.shape.borderRadius,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
              }}
            >
              Ücretsiz Başla
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<ArrowForwardIcon />}
              component={Link}
              to="/login"
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: (theme) => theme.shape.borderRadius,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
                borderColor: (theme) => alpha(theme.palette.common.white, 0.2),
                color: (theme) => theme.palette.common.white,
                '&:hover': {
                  borderColor: (theme) => theme.palette.common.white,
                  bgcolor: (theme) => alpha(theme.palette.common.white, 0.05),
                },
              }}
            >
              Giriş Yap
            </Button>
          </Stack>

          <Typography
            variant="caption"
            sx={{
              color: (theme) => alpha(theme.palette.common.white, 0.3),
              fontSize: '0.7rem',
              letterSpacing: '0.3px',
              display: 'block',
              mt: 2,
            }}
          >
            Stokonomi şu anda geliştirme aşamasındadır.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default FinalCtaSection;
