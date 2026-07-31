// src/components/landing/HowItWorks.tsx
import React, { useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Avatar,
  Step,
  StepLabel,
  Stepper,
  stepConnectorClasses,
  styled,
  StepConnector,
} from '@mui/material';
import {
  UploadFile as UploadFileIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { motion, useInView } from 'framer-motion';
import { SectionContainer } from '../../../shared/ui';

const steps = [
  {
    icon: UploadFileIcon,
    label: 'Excel dosyanızı yükleyin',
    description: 'Stok ve talep verilerinizi birkaç saniyede sisteme aktarın.',
    color: '#0B5ED7',
  },
  {
    icon: PsychologyIcon,
    label: 'Analizleri çalıştırın',
    description: 'Emniyet stoku, talep tahmini, simülasyon ve backtest analizlerini tek tıkla oluşturun.',
    color: '#2F80ED',
  },
  {
    icon: AssessmentIcon,
    label: 'Sonuçları inceleyin',
    description: 'AI yorumları, Executive Summary ve önerilen stok seviyelerini görüntüleyin.',
    color: '#22C55E',
  },
  {
    icon: DownloadIcon,
    label: 'Raporunuzu alın',
    description: 'Excel raporlarını dışa aktarın ve kararlarınızı uygulayın.',
    color: '#F59E0B',
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

export function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <SectionContainer bgcolor="#F8FAFC" py={10}>
      <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>
          Nasıl Çalışır?
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1, mb: 2 }}>
          Stokonomi ile <br />
          <Box component="span" sx={{ color: '#0B5ED7' }}>Dakikalar İçinde</Box>
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748B' }}>
          4 basit adımda stok kararlarınızı veriye dayandırın.
        </Typography>
      </Box>

      <Box ref={ref}>
        <Stepper
          alternativeLabel
          connector={<CustomConnector />}
          sx={{
            '& .MuiStepLabel-root': {
              flexDirection: 'column',
            },
            '& .MuiStepLabel-label': {
              mt: 1,
              fontWeight: 600,
              color: '#0F172A',
              fontSize: '0.875rem',
            },
            '& .MuiStepLabel-labelContainer': {
              '& .MuiTypography-root': {
                fontSize: '0.75rem',
                color: '#64748B',
                fontWeight: 400,
              },
            },
          }}
        >
          {steps.map((step, index) => (
            <Step key={index}>
              <StepLabel
                icon={
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={isInView ? { opacity: 1, scale: 1 } : {}}
                    transition={{ delay: index * 0.15, duration: 0.4 }}
                  >
                    <Avatar
                      sx={{
                        width: 56,
                        height: 56,
                        bgcolor: `${step.color}10`,
                        color: step.color,
                        border: `2px solid ${step.color}20`,
                      }}
                    >
                      <step.icon sx={{ fontSize: 28 }} />
                    </Avatar>
                  </motion.div>
                }
              >
                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 600, color: '#0F172A', fontSize: '0.875rem' }}
                  >
                    {step.label}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{ color: '#64748B', display: 'block', mt: 0.5 }}
                  >
                    {step.description}
                  </Typography>
                </Box>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>
    </SectionContainer>
  );
}

export default HowItWorks;