// src/features/academy/content/types.ts

export interface FAQ {
  question: string;
  answer: string;
}

export interface Section {
  type:
    | 'heading'
    | 'paragraph'
    | 'bulletList'
    | 'numberedList'
    | 'callout'
    | 'formula'
    | 'example'
    | 'table'
    | 'faq'
    | 'divider';
  level?: 2 | 3;
  content?: string;
  items?: string[];
  headers?: string[];
  rows?: string[][];
  faqs?: FAQ[];
}

export interface Article {
  id?: string;
  slug: string;
  title: string;
  description: string;
  category: string;
  publishedAt: string;
  updatedAt: string | null;
  readingTime: number;
  status: 'published' | 'draft';
  sections: Section[];
  // ✅ SEO alanları
  seoTitle?: string | null;
  seoDescription?: string | null;
  featuredImage?: string | null;
  featuredImageAlt?: string | null;
}

export interface AcademyArticleListItem {
  id: string;
  slug: string;
  title: string;
  description: string;
  category: string;
  publishedAt: string;
  updatedAt: string | null;
  readingTime: number;
  featuredImage: string | null;
  featuredImageAlt: string | null;
}

export interface AcademyArticleDetail extends AcademyArticleListItem {
  status: 'published';
  sections: Section[];
  seoTitle: string | null;
  seoDescription: string | null;
}

export interface AcademyArticleListResponse {
  items: AcademyArticleListItem[];
}
