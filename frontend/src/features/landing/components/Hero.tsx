// src/components/landing/Hero.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Chip,
  Paper,
  Button,
} from '@mui/material';
import {
  ArrowForward as ArrowForwardIcon,
  PlayArrow as PlayArrowIcon,
  Inventory as InventoryIcon,
  TrendingUp as TrendingUpIcon,
  Science as ScienceIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { PrimaryButton } from '../../../shared/ui';

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
              {/* AI Badge */}
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

              {/* ✅ Yeni Başlık */}
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
                    Veriye Dayalı
                    <br />
                    Daha Akıllı
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
                    Stok Kararları
                  </Box>
                </Typography>
              </motion.div>

              {/* ✅ Yeni Alt Yazı */}
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
                  Emniyet stoku, talep tahmini, Monte Carlo simülasyonu ve backtest analizlerini tek platformda çalıştırın. 
                  Excel dosyanızı yükleyin, dakikalar içinde karar destek raporunuzu alın.
                </Typography>
              </motion.div>

              {/* CTA Butonları */}
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

              {/* ✅ Yeni Badge'ler - Ürün Özellikleri */}
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
                    <InventoryIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Emniyet Stoku
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Talep Tahmini
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScienceIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Monte Carlo Simülasyonu
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <HistoryIcon sx={{ fontSize: 18, color: '#0B5ED7' }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Backtest
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            </motion.div>
          </Box>

          {/* ✅ Sağ: GERÇEK Dashboard Görseli */}
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

                {/* ✅ Dashboard Content - Gerçek Ekran Görüntüsü */}
                <Box sx={{ p: 0, bgcolor: 'white' }}>
                  <Box
                    component="img"
                    src="/dashboard-preview.png"
                    alt="Stokonomi Dashboard"
                    sx={{
                      width: '100%',
                      height: 'auto',
                      display: 'block',
                    }}
                    onError={(e) => {
                      // Görsel yoksa placeholder
                      e.currentTarget.style.display = 'none';
                      const parent = e.currentTarget.parentElement;
                      if (parent) {
                        parent.innerHTML = `
                          <div style="padding: 40px; text-align: center; background: #F8FAFC; min-height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                            <div style="font-size: 16px; font-weight: 600; color: #0F172A;">Dashboard</div>
                            <div style="font-size: 14px; color: #64748B; margin-top: 4px;">Executive Summary • AI Yorumları • Grafikler</div>
                            <div style="font-size: 12px; color: #94A3B8; margin-top: 16px;">📁 dashboard-preview.png ekleyin</div>
                          </div>
                        `;
                      }
                    }}
                  />
                </Box>
              </Paper>
            </motion.div>
          </Box>
        </Box>

        {/* ✅ YENİ: Felsefe Cümlesi - Hero Altı */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <Box
            sx={{
              mt: 6,
              pt: 4,
              borderTop: '1px solid #E2E8F0',
              textAlign: 'center',
              maxWidth: 700,
              mx: 'auto',
            }}
          >
            <Typography
              variant="body1"
              sx={{
                fontSize: '1.125rem',
                color: '#0F172A',
                fontWeight: 500,
                lineHeight: 1.7,
              }}
            >
              Excel dosyalarınız yalnızca veri değildir.
              <br />
              <Box component="span" sx={{ color: '#0B5ED7' }}>
                Doğru analiz edildiğinde daha iyi stok kararlarının temelidir.
              </Box>
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 1.5,
                color: '#64748B',
                fontSize: '0.875rem',
              }}
            >
              Excel'i yükleyin. Analizleri çalıştırın. Kararlarınızı veriye dayandırın.
            </Typography>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}

export default Hero;