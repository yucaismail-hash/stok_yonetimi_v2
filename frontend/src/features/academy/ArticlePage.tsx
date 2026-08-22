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
  CircularProgress,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { ArrowBack as ArrowBackIcon, Home as HomeIcon } from '@mui/icons-material';
import { Logo } from '../../shared/ui';
import { canonicalUrl, httpImageOrDefault, Seo, SEO_SITE_URL } from '../../seo';
import type { Article } from './content/types';
import { AcademyApiError, useAcademyArticle } from './api';
import ArticleContent from './components/ArticleContent';

interface ArticleStateProps {
  kind: 'loading' | 'notFound' | 'error';
  onRetry?: () => void;
}

function ArticleState({ kind, onRetry }: ArticleStateProps) {
  const notFound = kind === 'notFound';
  const loading = kind === 'loading';
  return (
    <>
      {notFound && (
        <Seo
          title="İçerik Hazırlanıyor | Stokonomi Akademi"
          description="Bu Akademi içeriği henüz yayına hazırlanıyor."
          robots="noindex, nofollow"
          noindex
        />
      )}
      {kind === 'error' && (
        <Seo
          title="İçeriğe Erişilemiyor | Stokonomi Akademi"
          description="Akademi içeriğine şu anda geçici olarak erişilemiyor."
          robots="noindex, nofollow"
          noindex
        />
      )}
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
            <Button component={RouterLink} to="/akademi" startIcon={<ArrowBackIcon />}>
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
              {loading ? <CircularProgress size={36} /> : <Logo size="medium" />}
            </Box>
            <Typography variant="overline" sx={{ color: 'primary.main', fontWeight: 600 }}>
              STOKONOMİ AKADEMİ
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700, my: 2 }}>
              {loading
                ? 'İçerik yükleniyor...'
                : notFound
                  ? 'İçerik hazırlanıyor.'
                  : 'İçeriğe şu anda erişilemiyor.'}
            </Typography>
            <Typography color="text.secondary" sx={{ lineHeight: 1.8, mb: kind === 'error' ? 4 : 0 }}>
              {loading
                ? 'Makale bilgileri getiriliyor.'
                : notFound
                  ? 'Bu Akademi içeriği henüz yayına hazırlanıyor.'
                  : 'Bu geçici bir bağlantı veya içerik servisi hatası olabilir.'}
            </Typography>
            {kind === 'error' && (
              <Button variant="contained" onClick={onRetry}>
                Tekrar Dene
              </Button>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
}

export default function ArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const articleQuery = useAcademyArticle(slug);

  if (!slug) return <ArticleState kind="notFound" />;
  if (articleQuery.isLoading) return <ArticleState kind="loading" />;
  if (articleQuery.isError) {
    const notFound =
      articleQuery.error instanceof AcademyApiError &&
      articleQuery.error.kind === 'notFound';
    return (
      <ArticleState
        kind={notFound ? 'notFound' : 'error'}
        onRetry={() => void articleQuery.refetch()}
      />
    );
  }
  if (!articleQuery.data) {
    return <ArticleState kind="error" onRetry={() => void articleQuery.refetch()} />;
  }

  const article: Article = articleQuery.data;

  // Article found - render it with SEO
  const canonical = canonicalUrl(`/akademi/${article.slug}`);
  const seoTitle = article.seoTitle || article.title;
  const seoDescription = article.seoDescription || article.description;
  const featuredImage = httpImageOrDefault(article.featuredImage);

  // Extract FAQ from article sections
  const faqs = article.sections.flatMap((section) =>
    section.type === 'faq' ? section.faqs || [] : []
  );

  return (
    <>
      <Seo
        title={seoTitle}
        description={seoDescription}
        canonical={canonical}
        ogType="article"
        ogTitle={seoTitle}
        ogDescription={seoDescription}
        ogUrl={canonical}
        ogImage={featuredImage}
        ogImageAlt={article.featuredImageAlt || article.title}
        twitterCard="summary_large_image"
        twitterTitle={seoTitle}
        twitterDescription={seoDescription}
        twitterImage={featuredImage}
        articlePublishedTime={article.publishedAt}
        articleModifiedTime={article.updatedAt || undefined}
        faqs={faqs}
        breadcrumbs={[
          { name: 'Ana Sayfa', url: `${SEO_SITE_URL}/` },
          { name: 'Akademi', url: canonicalUrl('/akademi') },
          { name: article.title, url: canonical },
        ]}
      />

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
    </>
  );
}
