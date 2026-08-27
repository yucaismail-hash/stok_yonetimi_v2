// src/features/academy/AcademyPage.tsx
import React from 'react';
import {
  Box, Button, Chip, Container, Grid, Paper, Skeleton, Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { Logo } from '../../shared/ui';
import { canonicalUrl, Seo } from '../../seo';
import { useAcademyArticles } from './api';
import { getAcademyCategoryIcon } from './components/categoryIcons';
import { PUBLIC_ANALYTICS_EVENTS, trackPublicEvent } from '../../shared/analytics/ga';

function AcademyLoadingCards() {
  return (
    <Grid container spacing={3} aria-label="Akademi içerikleri yükleniyor">
      {[0, 1, 2, 3].map((item) => (
        <Grid size={{ xs: 12, sm: 6, md: 3 }} key={item}>
          <Paper elevation={0} sx={{ p: 3.5, minHeight: 220, border: 1, borderColor: 'divider' }}>
            <Skeleton width="45%" height={24} />
            <Skeleton width="85%" height={36} sx={{ mt: 2 }} />
            <Skeleton height={22} />
            <Skeleton width="70%" height={22} />
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
}

export default function AcademyPage() {
  const articlesQuery = useAcademyArticles();
  const articles = articlesQuery.data ?? [];

  return (
    <>
      <Seo
        title="Stokonomi Akademi | Stok Yönetimi ve Talep Tahmini"
        description="Stok yönetimi, emniyet stoku, yeniden sipariş noktası, talep tahmini ve envanter planlama konularında uygulamalı içerikler."
        canonical={canonicalUrl('/akademi')}
        robots="index, follow"
      />
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: { xs: 4, md: 6 } }}>
      <Container maxWidth="xl">
        <Box sx={{ mb: 4 }}>
          <Button component={Link} to="/" startIcon={<ArrowBackIcon />} sx={{ color: 'text.secondary', fontWeight: 500, textTransform: 'none' }}>
            Ana Sayfa
          </Button>
        </Box>

        <Box sx={{ textAlign: 'center', maxWidth: 760, mx: 'auto', mb: { xs: 6, md: 8 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}><Logo size="medium" /></Box>
          <Typography variant="overline" sx={{ color: 'primary.main', fontWeight: 600, letterSpacing: '0.5px', display: 'block', mb: 1 }}>
            STOKONOMİ AKADEMİ
          </Typography>
          <Typography variant="h2" sx={{ fontWeight: 700, color: 'text.primary', mb: 2, fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' } }}>
            Stok yönetimini<br />
            <Box component="span" sx={{ background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              daha anlaşılır
            </Box><br />
            hale getiriyoruz.
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', maxWidth: 660, mx: 'auto', lineHeight: 1.8, fontSize: { xs: '0.95rem', md: '1.05rem' } }}>
            Stok yönetimi, talep tahmini, emniyet stoku ve karar destek süreçlerini açık,
            uygulanabilir ve örneklerle ele alan Stokonomi bilgi merkezi.
          </Typography>
        </Box>

        {articlesQuery.isLoading && <AcademyLoadingCards />}

        {articlesQuery.isError && (
          <Paper elevation={0} sx={{ maxWidth: 680, mx: 'auto', p: { xs: 4, md: 5 }, textAlign: 'center', border: 1, borderColor: 'divider' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1.5 }}>Akademi içeriklerine şu anda erişilemiyor.</Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>Bu geçici bir bağlantı veya içerik servisi hatası olabilir.</Typography>
            <Button variant="contained" onClick={() => void articlesQuery.refetch()}>Tekrar Dene</Button>
          </Paper>
        )}

        {!articlesQuery.isLoading && !articlesQuery.isError && articles.length === 0 && (
          <Paper elevation={0} sx={{ maxWidth: 680, mx: 'auto', p: { xs: 4, md: 5 }, textAlign: 'center', border: 1, borderColor: 'divider' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1.5 }}>Yeni içerikler hazırlanıyor.</Typography>
            <Typography color="text.secondary">Yayına hazır Akademi içerikleri burada listelenecek.</Typography>
          </Paper>
        )}

        {!articlesQuery.isLoading && !articlesQuery.isError && articles.length > 0 && (
          <Grid container spacing={3}>
            {articles.map((article, index) => {
              const CategoryIcon = getAcademyCategoryIcon(article.category);
              return (
                <Grid size={{ xs: 12, sm: 6, md: 3 }} key={article.id}>
                  <Paper
                    component={Link}
                    to={`/akademi/${article.slug}`}
                    onClick={() => trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.ACADEMY_CARD_CLICK, {
                      article_slug: article.slug,
                      category: article.category,
                      position: index + 1,
                      surface: 'academy',
                    })}
                    elevation={0}
                    sx={{
                      p: { xs: 2.5, md: 3.5 }, height: '100%', minHeight: 220, display: 'flex', flexDirection: 'column',
                      borderRadius: (theme) => theme.shape.borderRadius, border: (theme) => `1px solid ${theme.palette.divider}`,
                      bgcolor: 'background.paper', color: 'inherit', textDecoration: 'none', transition: 'all 0.25s ease-in-out',
                      '&:hover': { borderColor: 'primary.main', boxShadow: (theme) => `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`, transform: 'translateY(-2px)' },
                    }}
                  >
                    <Chip label={article.category} size="small" sx={{ alignSelf: 'flex-start', mb: 2, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06), color: 'primary.main' }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, borderRadius: 2, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06), color: 'primary.main', flexShrink: 0 }}>
                        <CategoryIcon sx={{ fontSize: 20 }} />
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '0.95rem', lineHeight: 1.3 }}>{article.title}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7, flex: 1, mb: 2 }}>{article.description}</Typography>
                    <Chip label={`Yayında · ${article.readingTime} dk`} size="small" sx={{ alignSelf: 'flex-start', bgcolor: (theme) => alpha(theme.palette.success.main, 0.08), color: 'success.main' }} />
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        )}

        <Paper
          component="aside"
          elevation={0}
          sx={{
            mt: { xs: 6, md: 8 },
            maxWidth: 780,
            mx: 'auto',
            p: { xs: 3, md: 4 },
            textAlign: 'center',
            border: 1,
            borderColor: 'divider',
            bgcolor: (theme) => alpha(theme.palette.primary.main, 0.03),
          }}
        >
          <Typography variant="h2" sx={{ fontWeight: 700, fontSize: { xs: '1.35rem', md: '1.6rem' }, mb: 1 }}>
            Kavramları karar akışına bağlayın.
          </Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 620, mx: 'auto', lineHeight: 1.75, mb: 2.5 }}>
            Stokonomi, tahminden doğrulamaya uzanan stok kararlarını birlikte değerlendirmek için geliştirilen bir yaklaşım sunuyor.
          </Typography>
          <Button
            component="a"
            href="/#karar-sistemi"
            variant="outlined"
            endIcon={<ArrowForwardIcon />}
            onClick={() => trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.ACADEMY_LISTING_TO_LANDING_CLICK, { placement: 'academy_listing', destination: '/#karar-sistemi' })}
          >
            Stokonomi yaklaşımını keşfet
          </Button>
        </Paper>
      </Container>
      </Box>
    </>
  );
}
