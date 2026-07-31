// src/components/landing/Hero.tsx (TAMAMEN DÜZELTİLMİŞ)
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Stack,
  Chip,
  Paper,
  Button,
} from '@mui/material';
import {
  ArrowForward as ArrowForwardIcon,
  PlayArrow as PlayArrowIcon,
  Shield as ShieldIcon,
  Lock as LockIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { PrimaryButton } from '../ui';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

export function Hero() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        bgcolor: '#F8FAFC',
        pt: { xs: 8, md: 0 },
      }}
    >
      {/* Arkaplan Glow */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: { xs: 400, md: 800 },
          height: { xs: 400, md: 800 },
          background: 'radial-gradient(circle, rgba(11,94,215,0.06) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 6,
            alignItems: 'center',
          }}
        >
          {/* Sol: Metin */}
          <Box>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
            >
              <motion.div variants={fadeInUp}>
                <Chip
                  icon={<Box component="span" sx={{ fontSize: 16 }}>⚡</Box>}
                  label="Yapay Zeka Destekli"
                  sx={{
                    bgcolor: '#0B5ED7',
                    color: 'white',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    mb: 3,
                    '& .MuiChip-icon': { color: 'white' },
                  }}
                />
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4.5rem' },
                    fontWeight: 700,
                    lineHeight: 1.1,
                    letterSpacing: '-0.02em',
                    mb: 2,
                  }}
                >
                  <Box component="span" sx={{ color: '#0F172A' }}>
                    AI ile
                    <br />
                    Stok Yönetimini
                    <br />
                  </Box>
                  <Box
                    component="span"
                    sx={{
                      background: 'linear-gradient(135deg, #0B5ED7, #2F80ED)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    Yeniden Tanımlayın
                  </Box>
                </Typography>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Typography
                  variant="body1"
                  sx={{
                    fontSize: { xs: '1rem', md: '1.125rem' },
                    color: '#64748B',
                    maxWidth: 560,
                    mb: 4,
                    lineHeight: 1.7,
                  }}
                >
                  Yapay zekâ destekli stok optimizasyonu, talep tahmini ve karar destek
                  sistemi ile maliyetlerinizi azaltın, servis seviyenizi artırın.
                </Typography>
              </motion.div>

              {/* ✅ CTA Butonları - Stack düzeltildi */}
              <motion.div variants={fadeInUp}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    gap: 2,
                    mb: 4,
                  }}
                >
                  <PrimaryButton
                    size="large"
                    endIcon={<ArrowForwardIcon />}
                    sx={{ px: 4 }}
                  >
                    Ücretsiz Başla
                  </PrimaryButton>
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<PlayArrowIcon />}
                    sx={{
                      px: 4,
                      py: 1.5,
                      borderRadius: '12px',
                      fontSize: '1rem',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderColor: '#E2E8F0',
                      color: '#0F172A',
                      '&:hover': {
                        borderColor: '#0B5ED7',
                        bgcolor: 'rgba(11,94,215,0.04)',
                      },
                    }}
                  >
                    Canlı Demo
                  </Button>
                </Box>
              </motion.div>

              {/* ✅ Güven Badge'leri - Stack düzeltildi */}
              <motion.div variants={fadeInUp}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'row',
                    gap: 3,
                    flexWrap: 'wrap',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShieldIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      ISO 27001
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LockIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      GDPR Uyumlu
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PeopleIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      500+ Şirket
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            </motion.div>
          </Box>

          {/* Sağ: Dashboard Preview */}
          <Box>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              <Paper
                elevation={0}
                sx={{
                  borderRadius: '24px',
                  overflow: 'hidden',
                  boxShadow: '0 24px 64px rgba(11,94,215,0.12)',
                  border: '1px solid #E2E8F0',
                  bgcolor: 'white',
                  position: 'relative',
                }}
              >
                {/* Laptop Frame */}
                <Box
                  sx={{
                    p: 2,
                    bgcolor: '#0F172A',
                    borderTopLeftRadius: '24px',
                    borderTopRightRadius: '24px',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, bgcolor: '#EF4444', borderRadius: '50%' }} />
                      <Box sx={{ width: 12, height: 12, bgcolor: '#F59E0B', borderRadius: '50%' }} />
                      <Box sx={{ width: 12, height: 12, bgcolor: '#22C55E', borderRadius: '50%' }} />
                    </Box>
                    <Box
                      sx={{
                        flex: 1,
                        height: 24,
                        bgcolor: 'rgba(255,255,255,0.08)',
                        borderRadius: 1,
                        mx: 2,
                      }}
                    />
                    <Box
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: 'rgba(255,255,255,0.08)',
                        borderRadius: '50%',
                      }}
                    />
                  </Box>
                </Box>

                {/* Dashboard Content */}
                <Box sx={{ p: 3, bgcolor: 'white' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 8, height: 8, bgcolor: '#22C55E', borderRadius: '50%' }} />
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        Canlı Veri
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Box sx={{ width: 32, height: 32, bgcolor: 'rgba(11,94,215,0.08)', borderRadius: '8px' }} />
                      <Box sx={{ width: 32, height: 32, bgcolor: 'rgba(11,94,215,0.08)', borderRadius: '8px' }} />
                    </Box>
                  </Box>

                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ color: '#64748B' }}>Stok Seviyesi</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>%82</Typography>
                    </Box>
                    <Box sx={{ width: '100%', height: 6, bgcolor: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
                      <Box sx={{ width: '82%', height: '100%', bgcolor: '#0B5ED7', borderRadius: 3 }} />
                    </Box>

                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: 1,
                        mt: 2,
                      }}
                    >
                      <Box sx={{ p: 1.5, bgcolor: '#F0FDF4', borderRadius: 2, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.6rem' }}>Tahmin</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>%94</Typography>
                      </Box>
                      <Box sx={{ p: 1.5, bgcolor: '#EFF6FF', borderRadius: 2, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.6rem' }}>Risk</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>Düşük</Typography>
                      </Box>
                      <Box sx={{ p: 1.5, bgcolor: '#F5F3FF', borderRadius: 2, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.6rem' }}>AI Kararı</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>Artır</Typography>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              </Paper>
            </motion.div>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default Hero;