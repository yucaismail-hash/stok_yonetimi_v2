// src/features/academy/content/index.ts
import { Article } from './types';
import { article as stokYonetimiNedir } from './articles/stok-yonetimi-nedir';

// Registry of all published articles
const articleRegistry: Record<string, Article> = {
  'stok-yonetimi-nedir': stokYonetimiNedir,
};

export function getArticleBySlug(slug: string): Article | undefined {
  return articleRegistry[slug];
}

export function getAllArticles(): Article[] {
  return Object.values(articleRegistry);
}

export function getPublishedArticles(): Article[] {
  return Object.values(articleRegistry).filter(
    (article) => article.status === 'published'
  );
}