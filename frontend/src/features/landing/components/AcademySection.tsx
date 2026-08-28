// src/features/landing/components/AcademySection.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Chip,
  Button,
  Skeleton,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import { useAcademyArticles } from '../../academy/api';
import { getAcademyCategoryIcon } from '../../academy/components/categoryIcons';
import { PUBLIC_ANALYTICS_EVENTS, trackPublicEvent } from '../../../shared/analytics/ga';

export function AcademySection() {
  const articlesQuery = useAcademyArticles();
  const articles = (articlesQuery.data ?? []).slice(0, 4);

  return (
    <Box
      id="akademi"
      sx={{
        py: { xs: 8, md: 10 },
        bgcolor: (theme) => theme.palette.background.default,
      }}
    >
      <Container maxWidth="xl">
        <Box
          sx={{
            textAlign: 'center',
            maxWidth: 760,
            mx: 'auto',
            mb: { xs: 6, md: 6 },
          }}
        >
          <Typography
            variant="overline"
            sx={{
              color: (theme) => theme.palette.primary.main,
              fontWeight: 600,
              letterSpacing: '0.5px',
              display: 'block',
              mb: 1,
            }}
          >
            STOKONOMİ AKADEMİ
          </Typography>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              color: (theme) => theme.palette.text.primary,
              mb: 2,
              fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },
            }}
          >
            Stok yönetimini
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
              daha anlaşılır
            </Box>
            <br />
            hale getiriyoruz.
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              maxWidth: 660,
              mx: 'auto',
              lineHeight: 1.8,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
            }}
          >
            Stok kararlarının arkasındaki kavramları açık ve uygulanabilir
            şekilde anlatıyoruz. Akademi, alan bilgisini karar süreçlerine
            daha sağlam bir başlangıç noktası yapmak için var.
          </Typography>

          <Box
            sx={{
              mt: 3,
              pt: 3,
              borderTop: (theme) => `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                color: (theme) => theme.palette.text.primary,
                fontSize: '1rem',
                mb: 0.5,
              }}
            >
              Bilgi, daha iyi kararların başlangıcıdır.
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: '0.875rem',
                lineHeight: 1.6,
                maxWidth: 580,
                mx: 'auto',
              }}
            >
              Temel kavramlardan ileri analiz yöntemlerine kadar,
              stok yönetimini sahadaki gerçek sorular üzerinden ele alıyoruz.
            </Typography>
          </Box>
        </Box>

        {articlesQuery.isLoading && (
          <Grid container spacing={3} aria-label="Akademi içerikleri yükleniyor">
            {[0, 1, 2, 3].map((item) => (
              <Grid size={{ xs: 12, sm: 6, md: 6, lg: 3 }} key={item}>
                <Paper elevation={0} sx={{ p: { xs: 2.5, md: 3.5 }, minHeight: 210, border: 1, borderColor: 'divider' }}>
                  <Skeleton width="45%" height={24} />
                  <Skeleton width="85%" height={34} sx={{ mt: 2 }} />
                  <Skeleton height={22} />
                  <Skeleton width="70%" height={22} />
                </Paper>
              </Grid>
            ))}
          </Grid>
        )}

        {articlesQuery.isError && (
          <Paper elevation={0} sx={{ maxWidth: 680, mx: 'auto', p: { xs: 3, md: 4 }, textAlign: 'center', border: 1, borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>Akademi içeriklerine şu anda erişilemiyor.</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>Bu geçici bir içerik servisi hatası olabilir.</Typography>
            <Button size="small" variant="outlined" onClick={() => void articlesQuery.refetch()}>Tekrar Dene</Button>
          </Paper>
        )}

        {!articlesQuery.isLoading && !articlesQuery.isError && articles.length === 0 && (
          <Paper elevation={0} sx={{ maxWidth: 680, mx: 'auto', p: { xs: 3, md: 4 }, textAlign: 'center', border: 1, borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>Stokonomi Akademi içerikleri hazırlanıyor.</Typography>
            <Typography variant="body2" color="text.secondary">Yayına hazır içerikler burada yer alacak.</Typography>
          </Paper>
        )}

        {!articlesQuery.isLoading && !articlesQuery.isError && articles.length > 0 && (
          <Grid container spacing={3}>
            {articles.map((article, index) => {
              const CategoryIcon = getAcademyCategoryIcon(article.category);
              return (
                <Grid size={{ xs: 12, sm: 6, md: 6, lg: 3 }} key={article.id}>
                  <Paper
                    component={Link}
                    to={`/akademi/${article.slug}`}
                    onClick={() => trackPublicEvent(PUBLIC_ANALYTICS_EVENTS.ACADEMY_CARD_CLICK, {
                      article_slug: article.slug,
                      category: article.category,
                      position: index + 1,
                      surface: 'landing',
                    })}
                    elevation={0}
                    sx={{
                      p: { xs: 2.25, sm: 2.5, md: 2.75 }, height: '100%', minHeight: { xs: 238, sm: 248, lg: 254 }, display: 'flex', flexDirection: 'column',
                      borderRadius: 1, border: (theme) => `1px solid ${theme.palette.divider}`,
                      bgcolor: 'background.paper', color: 'inherit', textDecoration: 'none', overflow: 'hidden', transition: 'all 0.25s ease-in-out',
                      '&:hover': { borderColor: 'primary.main', boxShadow: (theme) => `0 8px 32px ${alpha(theme.palette.primary.main, 0.06)}`, transform: 'translateY(-2px)' },
                    }}
                  >
                    <Chip label={article.category} size="small" sx={{ alignSelf: 'flex-start', maxWidth: '100%', mb: 1.5, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06), color: 'primary.main' }} />
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.25, mb: 1.5, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, borderRadius: 2, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06), color: 'primary.main', flexShrink: 0 }}>
                        <CategoryIcon sx={{ fontSize: 20 }} />
                      </Box>
                      <Typography variant="h6" sx={{ minWidth: 0, minHeight: '2.6em', fontWeight: 600, fontSize: '0.95rem', lineHeight: 1.3, overflow: 'hidden', overflowWrap: 'anywhere', display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2 }}>{article.title}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ minHeight: '4.95em', lineHeight: 1.65, fontSize: '0.875rem', flex: 1, overflow: 'hidden', overflowWrap: 'anywhere', display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 3 }}>{article.description}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 'auto', pt: 1.5, flexShrink: 0 }}>{article.readingTime} dakika okuma</Typography>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        )}

        <Box
          sx={{
            mt: { xs: 6, md: 6 },
            textAlign: 'center',
          }}
        >
          <Button component={Link} to="/akademi" variant="outlined" sx={{ textTransform: 'none', fontWeight: 600 }}>
            Tüm içerikleri gör
          </Button>
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 1.5,
              color: (theme) => theme.palette.text.secondary,
              fontSize: '0.75rem',
              opacity: 0.6,
            }}
          >
            Stokonomi Akademi
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default AcademySection;
