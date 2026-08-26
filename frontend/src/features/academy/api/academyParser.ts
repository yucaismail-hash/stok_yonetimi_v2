import type {
  AcademyArticleDetail,
  AcademyArticleListItem,
  AcademyArticleListResponse,
  AcademyInternalLink,
  FAQ,
  Section,
} from '../content/types';

export class AcademyPayloadError extends Error {
  constructor(message = 'Academy API returned an invalid payload') {
    super(message);
    this.name = 'AcademyPayloadError';
  }
}

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new AcademyPayloadError();
  }
  return value as Record<string, unknown>;
}

function string(value: unknown): string {
  if (typeof value !== 'string') throw new AcademyPayloadError();
  return value;
}

function nullableString(value: unknown): string | null {
  if (value === null) return null;
  return string(value);
}

function number(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new AcademyPayloadError();
  }
  return value;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) throw new AcademyPayloadError();
  return value.map(string);
}

function parseFaq(value: unknown): FAQ {
  const item = record(value);
  return { question: string(item.question), answer: string(item.answer) };
}

const ACADEMY_INTERNAL_PATH = /^\/akademi\/[a-z0-9]+(?:-[a-z0-9]+)*$/;

function parseInternalLinks(value: unknown, content: string): AcademyInternalLink[] | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value)) throw new AcademyPayloadError();

  const links = value.map((item) => {
    const link = record(item);
    const text = string(link.text);
    const href = string(link.href);
    if (!text || !ACADEMY_INTERNAL_PATH.test(href) || !content.includes(text)) {
      throw new AcademyPayloadError();
    }
    return { text, href };
  });

  if (new Set(links.map((link) => link.href)).size !== links.length) {
    throw new AcademyPayloadError();
  }

  return links;
}

export function parseAcademySection(value: unknown): Section {
  const section = record(value);
  const type = string(section.type);

  switch (type) {
    case 'heading': {
      if (section.level !== 2 && section.level !== 3) throw new AcademyPayloadError();
      return { type, level: section.level, content: string(section.content) };
    }
    case 'paragraph': {
      const content = string(section.content);
      return { type, content, links: parseInternalLinks(section.links, content) };
    }
    case 'callout':
    case 'formula':
    case 'example':
      return { type, content: string(section.content) };
    case 'bulletList':
    case 'numberedList':
      return { type, items: stringArray(section.items) };
    case 'table': {
      const headers = stringArray(section.headers);
      if (!Array.isArray(section.rows)) throw new AcademyPayloadError();
      const rows = section.rows.map(stringArray);
      if (rows.some((row) => row.length !== headers.length)) throw new AcademyPayloadError();
      return { type, headers, rows };
    }
    case 'faq':
      if (!Array.isArray(section.faqs)) throw new AcademyPayloadError();
      return { type, faqs: section.faqs.map(parseFaq) };
    case 'divider':
      if (section.content === undefined || section.content === null) return { type };
      return { type, content: string(section.content) };
    default:
      throw new AcademyPayloadError(`Unsupported Academy section type: ${type}`);
  }
}

export function parseAcademyListItem(value: unknown): AcademyArticleListItem {
  const item = record(value);
  return {
    id: string(item.id),
    slug: string(item.slug),
    title: string(item.title),
    description: string(item.description),
    category: string(item.category),
    publishedAt: string(item.publishedAt),
    updatedAt: nullableString(item.updatedAt),
    readingTime: number(item.readingTime),
    featuredImage: nullableString(item.featuredImage),
    featuredImageAlt: nullableString(item.featuredImageAlt),
  };
}

export function parseAcademyListResponse(value: unknown): AcademyArticleListResponse {
  const envelope = record(value);
  if (!Array.isArray(envelope.items)) throw new AcademyPayloadError();
  return { items: envelope.items.map(parseAcademyListItem) };
}

export function parseAcademyDetail(value: unknown): AcademyArticleDetail {
  const item = record(value);
  const base = parseAcademyListItem(item);
  if (item.status !== 'published' || !Array.isArray(item.sections)) {
    throw new AcademyPayloadError();
  }
  return {
    ...base,
    status: 'published',
    sections: item.sections.map(parseAcademySection),
    seoTitle: nullableString(item.seoTitle),
    seoDescription: nullableString(item.seoDescription),
  };
}
