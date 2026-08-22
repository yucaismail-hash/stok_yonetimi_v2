export const academyQueryKeys = {
  articles: ['academy', 'articles'] as const,
  article: (slug: string) => ['academy', 'article', slug] as const,
};
