// src/features/academy/index.ts
export { default as AcademyPage } from './AcademyPage';
export { default as ArticlePage } from './ArticlePage';
export { getArticleBySlug, getAllArticles, getPublishedArticles } from './content';
export type { Article, Section, FAQ } from './content/types';