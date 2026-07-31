// src/components/landing/SolutionSection.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Stack,
  Avatar,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
  stepConnectorClasses,
  styled,
} from '@mui/material';
import {
  UploadFile as UploadFileIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  ShoppingCart as ShoppingCartIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../ui';

const steps = [
  {
    icon: UploadFileIcon,
    label: 'Excel Yükle',
    description: 'Mevcut stok verilerinizi sisteme yükleyin.',
    color: '#0B5ED7',
  },
  {
    icon: PsychologyIcon,
    label: 'AI Analizi',
    description: 'Yapay zeka, talep desenlerini ve riskleri analiz eder.',
    color: '#2F80ED',
  },
  {
    icon: AssessmentIcon,
    label: 'Risk Hesabı',
    description: 'ABC/XYZ analizi ve 6 farklı metot ile risk hesaplanır.',
    color: '#F59E0B',
  },
  {
    icon: ShoppingCartIcon,
    label: 'Sipariş Önerisi',
    description: 'Optimum stok seviyesi ve sipariş önerisi sunulur.',
    color: '#22C55E',
  },
];

const CustomConnector = styled(StepConnector)(({ theme }) => ({
  [`& .${stepConnectorClasses.line}`]: {
    borderColor: '#E2E8F0',
    borderWidth: 2,
  },
  [`&.${stepConnectorClasses.active} .${stepConnectorClasses.line}`]: {
    borderColor: '#0B5ED7',
  },
  [`&.${stepConnectorClasses.completed} .${stepConnectorClasses.line}`]: {
    borderColor: '#22C55E',
  },
}));

export function SolutionSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#FFFFFF" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Çözüm
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Stok Yönetimini <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Otomatikleştirin</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          Excel'den AI destekli kararlara, tüm süreci tek platformda yönetin.
        </Typography>
      </Box>

      {/* ✅ Grid kaldırıldı, Box ile grid sistemi oluşturuldu */}
      <Box
        ref={ref}
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          gap: 4,
          alignItems: 'center',
        }}
      >
        {/* Sol Taraf: Adımlar */}
        <Box sx={{ position: 'relative' }}>
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 300,
              height: 300,
              background: 'radial-gradient(circle, rgba(11,94,215,0.05) 0%, transparent 70%)',
              borderRadius: '50%',
              pointerEvents: 'none',
            }}
          />
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: index * 0.15, duration: 0.5 }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  mb: 2,
                  borderRadius: '16px',
                  border: '1px solid #E2E8F0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
                  position: 'relative',
                  '&:hover': {
                    borderColor: step.color,
                    boxShadow: `0 4px 16px ${step.color}15`,
                  },
                  transition: 'all 0.3s ease-in-out',
                }}
              >
                <Avatar
                  sx={{
                    width: 48,
                    height: 48,
                    bgcolor: `${step.color}10`,
                    color: step.color,
                  }}
                >
                  <step.icon />
                </Avatar>
                <Box>
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 600, color: '#0F172A' }}
                  >
                    {step.label}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    {step.description}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    ml: 'auto',
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    bgcolor: `${step.color}10`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{ fontWeight: 600, color: step.color }}
                  >
                    {index + 1}
                  </Typography>
                </Box>
              </Paper>
            </motion.div>
          ))}
        </Box>

        {/* Sağ Taraf: Özet Kart */}
        <Box>
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 4,
                borderRadius: '24px',
                border: '1px solid #E2E8F0',
                bgcolor: '#F8FAFC',
              }}
            >
              <Stack spacing={3}>
                <Box>
                  <Typography variant="caption" sx={{ color: '#64748B' }}>
                    Toplam Süre
                  </Typography>
                  <Typography variant="h2" sx={{ fontSize: '2.5rem', fontWeight: 700, color: '#0F172A' }}>
                    7 Dakika
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Geleneksel yöntemlerle 8 saat
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  {[85, 92, 78, 96].map((value, index) => (
                    <Box key={index} sx={{ flex: 1, textAlign: 'center' }}>
                      <Box
                        sx={{
                          width: '100%',
                          height: 4,
                          bgcolor: '#E2E8F0',
                          borderRadius: 2,
                          overflow: 'hidden',
                          mb: 1,
                        }}
                      >
                        <Box
                          sx={{
                            width: `${value}%`,
                            height: '100%',
                            bgcolor: '#0B5ED7',
                            borderRadius: 2,
                            animation: isInView ? 'grow 1s ease-out forwards' : 'none',
                          }}
                        />
                      </Box>
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        {value}%
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Stack>
            </Paper>
          </motion.div>
        </Box>
      </Box>
    </SectionContainer>
  );
}

export default SolutionSection;