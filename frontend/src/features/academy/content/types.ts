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
  slug: string;
  title: string;
  description: string;
  category: string;
  publishedAt: string;
  updatedAt: string;
  readingTime: number;
  status: 'published' | 'draft';
  sections: Section[];
}