import React from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Functions as FunctionsIcon, HistoryEdu as HistoryEduIcon, School as SchoolIcon } from '@mui/icons-material';

const levels = [
  {
    icon: FunctionsIcon,
    title: 'Matematiksel Zekâ',
    line: 'Şirketinizi henüz tanımıyor olabilir. Ama matematiği biliyor.',
    description: 'İlk veriyle birlikte matematiksel ve istatistiksel yöntemler üzerinden çalışabilecek temel analiz katmanı.',
  },
  {
    icon: HistoryEduIcon,
    title: 'Kanıt / Ampirik Zekâ',
    line: 'Bir karar yalnızca hesaplandığı için doğru kabul edilmemeli.',
    description: 'Simülasyon ve geriye dönük doğrulama ile yalnız hesaplanan sonucu değil, geçmiş performansı ve olası senaryoları da değerlendirmeyi amaçlar.',
  },
  {
    icon: SchoolIcon,
    title: 'Öğrenilmiş Zekâ',
    line: 'Yeni kanıtlar geldikçe karar bağlamı güçlenir.',
    description: 'Yeni gerçekleşen veriler, model performansı, simülasyon ve doğrulama sonuçları ile geri bildirim biriktikçe şirket davranışını öğrenmeye yönelik katman.',
  },
];

export function IntelligenceLevelsSection() {
  return (
    <Box sx={{ py: { xs: 8, md: 10 }, bgcolor: 'background.paper' }}>
      <Container maxWidth="xl">
        <Box sx={{ textAlign: 'center', maxWidth: 760, mx: 'auto', mb: { xs: 5, md: 6 } }}>
          <Typography variant="overline" sx={{ color: 'primary.main', fontWeight: 600, letterSpacing: '0.5px', display: 'block', mb: 1 }}>ZEKÂ KATMANLARI</Typography>
          <Typography variant="h2" sx={{ fontWeight: 700, color: 'text.primary', mb: 2, fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' } }}>
            Karar, tek bir modelden daha fazlasıdır.
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8, fontSize: { xs: '0.95rem', md: '1.05rem' } }}>
            Amaç kararı yapay zekâya bırakmak değil; karar vericinin daha fazla kanıtla değerlendirme yapmasını sağlamaktır.
          </Typography>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
          {levels.map((level, index) => {
            const Icon = level.icon;
            return (
              <Paper key={level.title} elevation={0} sx={{ p: { xs: 3, md: 3.5 }, border: 1, borderColor: 'divider', bgcolor: index === 1 ? (theme) => alpha(theme.palette.primary.main, 0.025) : 'background.default', display: 'flex', flexDirection: 'column' }}>
                <Box aria-hidden="true" sx={{ width: 44, height: 44, display: 'grid', placeItems: 'center', borderRadius: 2, color: 'primary.main', bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08), mb: 2 }}>
                  <Icon sx={{ fontSize: 22 }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, fontSize: '1.1rem', mb: 1 }}>{level.title}</Typography>
                <Typography variant="body2" sx={{ color: 'primary.main', fontWeight: 600, lineHeight: 1.55, mb: 1.5 }}>{level.line}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>{level.description}</Typography>
              </Paper>
            );
          })}
        </Box>
      </Container>
    </Box>
  );
}

export default IntelligenceLevelsSection;
