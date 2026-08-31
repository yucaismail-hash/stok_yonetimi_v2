import React from 'react';
import { Box, Container, Paper, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  AccountTree as AccountTreeIcon,
  Assessment as AssessmentIcon,
  AutoGraph as AutoGraphIcon,
  FactCheck as FactCheckIcon,
  LocalShipping as LocalShippingIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';

const stages = [
  {
    icon: AutoGraphIcon,
    title: 'Talep Tahmini',
    description: 'Talep davranışını analiz ederek uygun tahmin yaklaşımlarını karşılaştırmaya yardımcı olur.',
  },
  {
    icon: AssessmentIcon,
    title: 'Emniyet Stoğu',
    description: 'Talep ve tedarik belirsizliğine karşı stokout ve fazla stok dengesini destekler.',
  },
  {
    icon: AccountTreeIcon,
    title: 'Simülasyon',
    description: 'Alınabilecek stok kararlarının farklı koşullardaki olası etkilerini değerlendirmeyi amaçlar.',
  },
  {
    icon: FactCheckIcon,
    title: 'Geriye Dönük Doğrulama',
    description: 'Model ve kararların geçmiş veride nasıl performans göstereceğini geriye dönük doğrulama (backtest) ile sınamaya yardımcı olur.',
  },
  {
    icon: LocalShippingIcon,
    title: 'Tedarikçi İçgörüsü',
    description: 'Teslim süresi ve tedarikçi davranışını stok kararının bağlamına eklemeyi amaçlar.',
  },
  {
    icon: PsychologyIcon,
    title: 'Karar Zekâsı',
    description: 'Farklı analiz çıktılarını birlikte değerlendirerek karar vericiye açıklanabilir destek sunmayı hedefler.',
  },
];

export function DecisionSystemSection() {
  return (
    <Box id="karar-sistemi" sx={{ py: { xs: 8, md: 10 }, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.025) }}>
      <Container maxWidth="xl">
        <Box sx={{ textAlign: 'center', maxWidth: 760, mx: 'auto', mb: { xs: 5, md: 6 } }}>
          <Typography variant="overline" sx={{ color: 'primary.main', fontWeight: 600, letterSpacing: '0.5px', display: 'block', mb: 1 }}>
            KARAR SİSTEMİ
          </Typography>
          <Typography variant="h2" sx={{ fontWeight: 700, color: 'text.primary', mb: 2, fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' } }}>
            Tahmin etmek yetmez.
            <br />
            <Box component="span" sx={{ color: 'primary.main' }}>Sınamak gerekir.</Box>
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8, fontSize: { xs: '0.95rem', md: '1.05rem' } }}>
            Stokonomi, birbirinden kopuk analiz ekranları yerine birbirini besleyen bir karar akışı için tasarlanıyor.
          </Typography>
        </Box>

        <Paper elevation={0} sx={{ p: { xs: 2.5, md: 4 }, border: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(6, 1fr)' }, gap: { xs: 2, lg: 0 } }}>
            {stages.map((stage, index) => {
              const Icon = stage.icon;
              return (
                <Box key={stage.title} sx={{ position: 'relative', px: { lg: 2 }, py: { xs: 1, lg: 0 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.25 }}>
                    <Box aria-hidden="true" sx={{ width: 36, height: 36, display: 'grid', placeItems: 'center', borderRadius: 2, color: 'primary.main', bgcolor: (theme) => alpha(theme.palette.primary.main, 0.08), flexShrink: 0 }}>
                      <Icon sx={{ fontSize: 19 }} />
                    </Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1.3 }}>{stage.title}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65, fontSize: '0.825rem' }}>
                    {stage.description}
                  </Typography>
                  {index < stages.length - 1 && (
                    <Box aria-hidden="true" sx={{ display: { xs: 'none', lg: 'grid' }, placeItems: 'center', position: 'absolute', right: -9, top: 12, zIndex: 1, width: 18, height: 18, borderRadius: '50%', bgcolor: 'background.paper', color: 'primary.main', fontSize: '0.9rem' }}>→</Box>
                  )}
                </Box>
              );
            })}
          </Box>
        </Paper>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 3, maxWidth: 960, mx: 'auto' }}>
          <Box sx={{ flex: 1, p: 2.5, borderLeft: 3, borderColor: 'primary.main', bgcolor: 'background.paper' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>Her veri alanı mevcut olmak zorunda değildir.</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65 }}>Stokonomi mevcut veriyle çalışabilecek, yeni veri kaynakları geldikçe analizini zenginleştirecek şekilde tasarlanıyor.</Typography>
          </Box>
          <Box sx={{ flex: 1, p: 2.5, borderLeft: 3, borderColor: 'primary.main', bgcolor: 'background.paper' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>Şirket verisi temel kaynaktır.</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65 }}>Excel ve ilerleyen entegrasyonlardaki API / ERP verileri; ekonomik göstergeler, döviz ve enflasyon gibi uygun dış sinyallerle gerektiğinde ek bağlam kazanabilir.</Typography>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}

export default DecisionSystemSection;
