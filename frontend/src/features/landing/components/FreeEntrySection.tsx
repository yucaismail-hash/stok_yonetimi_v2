import React from 'react';
import { ArrowForward as ArrowForwardIcon, CheckCircleOutlined as CheckCircleOutlinedIcon } from '@mui/icons-material';
import { alpha } from '@mui/material/styles';
import { Box, Button, Chip, Container, Paper, Typography } from '@mui/material';
import { Link } from 'react-router-dom';

import { PUBLIC_ANALYTICS_EVENTS, trackPublicEvent } from '../../../shared/analytics/ga';

const steps = [
  {
    label: 'Ücretsiz',
    title: 'Ücretsiz analiz edin',
    description: 'Talep tahmini, emniyet stoku, simülasyon ve diğer bireysel analizleri kendi verinizle kullanın.',
  },
  {
    label: '5 tam Business Workflow',
    title: 'İlk 5 çalıştırmada tamamını görün',
    description: 'Forecast → Safety Stock → Simulation → Backtest → Supplier → Decision Intelligence zincirini ilk 5 başarılı Business Workflow’da tam kapsamıyla deneyin.',
  },
  {
    label: '60 günlük deneme',
    title: '60 gün boyunca ön izleme',
    description: 'İlk 5 tam workflow hakkından sonra, deneme süresi boyunca sonuçların limited/preview görünümüne erişmeye devam edin.',
  },
];

export function FreeEntrySection() {
  return (
    <Box id="ucretsiz-basla" component="section" sx={{ py: { xs: 8, md: 10 }, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.025) }}>
      <Container maxWidth="xl">
        <Box sx={{ maxWidth: 760, mx: 'auto', textAlign: 'center', mb: { xs: 5, md: 6 } }}>
          <Typography variant="overline" sx={{ color: 'primary.main', fontWeight: 600, letterSpacing: '0.6px' }}>
            ÜCRETSİZ BAŞLANGIÇ
          </Typography>
          <Typography component="h2" variant="h2" sx={{ mt: 1, mb: 2, fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' }, fontWeight: 700, lineHeight: 1.2 }}>
            Stokonomi’yi gerçek verinizle deneyin.
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 680, mx: 'auto', lineHeight: 1.8, fontSize: { xs: '0.95rem', md: '1.05rem' } }}>
            Bireysel analizleri ücretsiz kullanın. Business Workflow’da ilk 5 çalıştırmada tüm karar çıktılarını görün; ardından 60 günlük deneme süresince sonuçların ön izlemesine erişmeye devam edin.
          </Typography>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' }, gap: 3 }}>
          {steps.map((step, index) => (
            <Box key={step.title}>
              <Paper elevation={0} sx={{ height: '100%', p: { xs: 3, md: 3.5 }, border: (theme) => `1px solid ${theme.palette.divider}`, borderRadius: (theme) => theme.shape.borderRadius, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1.5, mb: 2.5 }}>
                  <Chip label={step.label} size="small" sx={{ maxWidth: '100%', fontWeight: 600, color: 'primary.main', bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08) }} />
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>{`0${index + 1}`}</Typography>
                </Box>
                <Typography component="h3" variant="h6" sx={{ fontWeight: 700, mb: 1.25, fontSize: '1.15rem' }}>{step.title}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.75, flex: 1 }}>{step.description}</Typography>
              </Paper>
            </Box>
          ))}
        </Box>

        <Box sx={{ maxWidth: 760, mx: 'auto', mt: { xs: 4, md: 5 }, p: { xs: 2.5, md: 3 }, borderLeft: (theme) => `3px solid ${theme.palette.primary.main}`, bgcolor: (theme) => alpha(theme.palette.background.paper, 0.75) }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Tam kapsam, kararları daha derine indirir.</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.75 }}>
            Ön izleme; genel karar özeti, temel risk göstergeleri ve seçilmiş KPI’ları gösterebilir. Tam Business planı ise SKU bazlı aksiyonlar, operasyonel planlar, senaryo karşılaştırmaları ve tam Decision Intelligence çıktıları gibi daha ayrıntılı sonuçları açar.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, alignItems: 'center', justifyContent: 'center', mt: { xs: 4, md: 5 } }}>
          <Button component={Link} to="/register" variant="contained" size="large" endIcon={<ArrowForwardIcon />} onClick={() => trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.LANDING_FREE_START_CLICK, { placement: 'free_entry', destination: '/register' })} sx={{ px: 4, py: 1.5, textTransform: 'none', fontWeight: 600 }}>
            Ücretsiz Başla
          </Button>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
            <CheckCircleOutlinedIcon sx={{ fontSize: 16 }} /> Kullanım limitleri uygulanabilir.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default FreeEntrySection;
