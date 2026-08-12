// src/features/academy/ArticlePage.tsx
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Breadcrumbs,
  Link,
  Chip,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { ArrowBack as ArrowBackIcon, Home as HomeIcon } from '@mui/icons-material';
import { Logo } from '../../shared/ui';
import { getArticleBySlug } from './content';
import ArticleContent from './components/ArticleContent';

export default function ArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const article = slug ? getArticleBySlug(slug) : undefined;

  // Article not found - show placeholder
  if (!article) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          bgcolor: (theme) => theme.palette.background.default,
          py: { xs: 4, md: 6 },
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <Container maxWidth="xl">
          <Box sx={{ mb: 4 }}>
            <Button
              component={RouterLink}
              to="/akademi"
              startIcon={<ArrowBackIcon />}
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontWeight: 500,
                textTransform: 'none',
                '&:hover': {
                  color: (theme) => theme.palette.text.primary,
                  bgcolor: 'transparent',
                },
              }}
            >
              Akademi'ye Dön
            </Button>
          </Box>

          <Box
            sx={{
              maxWidth: 760,
              mx: 'auto',
              p: { xs: 4, md: 6 },
              borderRadius: (theme) => theme.shape.borderRadius,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              bgcolor: (theme) => theme.palette.background.paper,
              textAlign: 'center',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
              <Logo size="medium" />
            </Box>

            <Typography
              variant="overline"
              sx={{
                color: (theme) => theme.palette.primary.main,
                fontWeight: 600,
                letterSpacing: '0.5px',
                display: 'block',
                mb: 2,
              }}
            >
              STOKONOMİ AKADEMİ
            </Typography>

            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                color: (theme) => theme.palette.text.primary,
                mb: 2,
                fontSize: { xs: '1.75rem', md: '2.5rem' },
              }}
            >
              İçerik hazırlanıyor.
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                maxWidth: 560,
                mx: 'auto',
                lineHeight: 1.8,
                fontSize: { xs: '0.95rem', md: '1.05rem' },
                mb: 4,
              }}
            >
              Bu Akademi içeriği henüz yayına hazırlanıyor.
            </Typography>

            <Button
              component={RouterLink}
              to="/akademi"
              variant="contained"
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: (theme) => theme.shape.borderRadius,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
              }}
            >
              Akademi'ye Dön
            </Button>
          </Box>
        </Container>
      </Box>
    );
  }

  // Article found - render it
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: (theme) => theme.palette.background.default,
        py: { xs: 4, md: 6 },
      }}
    >
      <Container maxWidth="xl">
        {/* Navigation */}
        <Box sx={{ mb: 4 }}>
          <Breadcrumbs
            aria-label="breadcrumb"
            sx={{
              '& .MuiBreadcrumbs-separator': {
                color: (theme) => theme.palette.text.secondary,
              },
            }}
          >
            <Link
              component={RouterLink}
              to="/"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                color: (theme) => theme.palette.text.secondary,
                textDecoration: 'none',
                '&:hover': {
                  color: (theme) => theme.palette.text.primary,
                },
              }}
            >
              <HomeIcon sx={{ fontSize: 16 }} />
              Ana Sayfa
            </Link>
            <Link
              component={RouterLink}
              to="/akademi"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                textDecoration: 'none',
                '&:hover': {
                  color: (theme) => theme.palette.text.primary,
                },
              }}
            >
              Akademi
            </Link>
            <Typography
              sx={{
                color: (theme) => theme.palette.text.primary,
                fontWeight: 500,
              }}
            >
              {article.title}
            </Typography>
          </Breadcrumbs>
        </Box>

        {/* Article Content */}
        <Box
          sx={{
            maxWidth: 820,
            mx: 'auto',
          }}
        >
          {/* Article Header */}
          <Box
            sx={{
              mb: 4,
              pb: 4,
              borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
            }}
          >
            <Chip
              label={article.category}
              size="small"
              sx={{
                mb: 2,
                bgcolor: (theme) => alpha(theme.palette.primary.main, 0.06),
                color: (theme) => theme.palette.primary.main,
                fontWeight: 500,
                fontSize: '0.7rem',
                borderRadius: 2,
                height: 28,
                '& .MuiChip-label': {
                  px: 2,
                },
              }}
            />

            <Typography
              variant="h1"
              component="h1"
              sx={{
                fontWeight: 700,
                color: (theme) => theme.palette.text.primary,
                fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },
                lineHeight: 1.2,
                mb: 2,
              }}
            >
              {article.title}
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: { xs: '1rem', md: '1.125rem' },
                lineHeight: 1.7,
                maxWidth: 680,
              }}
            >
              {article.description}
            </Typography>

            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 2,
                mt: 2,
                color: (theme) => theme.palette.text.secondary,
                fontSize: '0.85rem',
              }}
            >
              <span>
                📅 Yayınlanma: {new Date(article.publishedAt).toLocaleDateString('tr-TR')}
              </span>
              <span>·</span>
              <span>⏱️ {article.readingTime} dakika okuma</span>
            </Box>
          </Box>

          {/* Article Body */}
          <ArticleContent sections={article.sections} />
        </Box>
      </Container>
    </Box>
  );
}