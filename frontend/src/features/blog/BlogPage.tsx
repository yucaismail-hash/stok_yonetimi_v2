// src/features/blog/BlogPage.tsx
import React from 'react';
import { Box, Container, Typography, Grid, Paper, Chip } from '@mui/material';
import { CalendarToday, Person } from '@mui/icons-material';

const posts = [
  { title: 'Emniyet Stoğu Nedir?', date: '30 Temmuz 2026', author: 'Stokonomi Ekibi', category: 'Stok Yönetimi', excerpt: 'Emniyet stoğu, belirsizlikleri karşılamak için tutulan ek stok miktarıdır...' },
  { title: 'Talep Tahmini Yöntemleri', date: '28 Temmuz 2026', author: 'Stokonomi Ekibi', category: 'Talep Tahmini', excerpt: 'Geçmiş verilere dayanarak gelecekteki talebi tahmin etmek için kullanılan yöntemler...' },
  { title: 'ABC/XYZ Analizi', date: '25 Temmuz 2026', author: 'Stokonomi Ekibi', category: 'Analiz', excerpt: 'Ürünleri maliyet ve talep değişkenliğine göre sınıflandırma yöntemi...' },
];

export default function BlogPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 8 }}>
      <Box sx={{ mb: 6 }}>
        <Typography variant="overline" sx={{ color: '#0B5ED7' }}>Blog</Typography>
        <Typography variant="h3" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>Stokonomi <Box component="span" sx={{ color: '#0B5ED7' }}>Blog</Box></Typography>
        <Typography variant="body1" sx={{ color: '#64748B', mt: 2 }}>Stok yönetimi ve AI hakkında en güncel içerikler.</Typography>
      </Box>

      <Grid container spacing={3}>
        {posts.map((post, index) => (
          <Grid size={{ xs: 12, md: 4 }} key={index}>
            <Paper sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', height: '100%', transition: 'all 0.3s', '&:hover': { boxShadow: 3, transform: 'translateY(-4px)' } }}>
              <Chip label={post.category} size="small" sx={{ bgcolor: '#EFF6FF', color: '#0B5ED7', mb: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#0F172A', mb: 1 }}>{post.title}</Typography>
              <Typography variant="body2" sx={{ color: '#64748B', mb: 2 }}>{post.excerpt}</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, color: '#94A3B8' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><CalendarToday sx={{ fontSize: 14 }} />{post.date}</Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Person sx={{ fontSize: 14 }} />{post.author}</Box>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}