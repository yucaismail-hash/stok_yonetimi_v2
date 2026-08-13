// src/seo/Seo.tsx
import { useEffect } from 'react';

export interface SeoProps {
  title: string;
  description: string;
  canonical?: string;
  robots?: string;
  ogType?: 'website' | 'article';
  ogTitle?: string;
  ogDescription?: string;
  ogUrl?: string;
  ogImage?: string;
  ogImageAlt?: string;
  twitterCard?: 'summary' | 'summary_large_image';
  twitterTitle?: string;
  twitterDescription?: string;
  twitterImage?: string;
  articlePublishedTime?: string;
  articleModifiedTime?: string;
  faqs?: Array<{ question: string; answer: string }>;
  breadcrumbs?: Array<{ name: string; url: string }>;
  noindex?: boolean;
}

const SEO_DATA_ATTR = 'data-stokonomi-seo';

function upsertMeta(name: string, content: string, isProperty: boolean = false) {
  const selector = isProperty ? `meta[property="${name}"]` : `meta[name="${name}"]`;
  let element = document.querySelector(selector) as HTMLMetaElement | null;

  if (!element) {
    element = document.createElement('meta');
    if (isProperty) {
      element.setAttribute('property', name);
    } else {
      element.setAttribute('name', name);
    }
    document.head.appendChild(element);
  }

  element.setAttribute('content', content);
}

function upsertLink(rel: string, href: string) {
  let element = document.querySelector(`link[rel="${rel}"]`) as HTMLLinkElement | null;

  if (!element) {
    element = document.createElement('link');
    element.setAttribute('rel', rel);
    document.head.appendChild(element);
  }

  element.setAttribute('href', href);
}

function removeMeta(name: string, isProperty: boolean = false) {
  const selector = isProperty ? `meta[property="${name}"]` : `meta[name="${name}"]`;
  const element = document.querySelector(selector);
  if (element) {
    element.remove();
  }
}

function removeLink(rel: string) {
  const element = document.querySelector(`link[rel="${rel}"]`);
  if (element) {
    element.remove();
  }
}

function removeOldSeoScripts() {
  const scripts = document.querySelectorAll(`script[${SEO_DATA_ATTR}]`);
  scripts.forEach((script) => script.remove());
}

function injectJsonLd(data: object) {
  const script = document.createElement('script');
  script.setAttribute('type', 'application/ld+json');
  script.setAttribute(SEO_DATA_ATTR, 'true');
  script.textContent = JSON.stringify(data);
  document.head.appendChild(script);
}

function getBaseUrl() {
  return 'https://stokonomi.com';
}

export default function Seo({
  title,
  description,
  canonical,
  robots = 'index, follow',
  ogType = 'website',
  ogTitle,
  ogDescription,
  ogUrl,
  ogImage = 'https://stokonomi.com/og/stokonomi-og.png',
  ogImageAlt,
  twitterCard = 'summary_large_image',
  twitterTitle,
  twitterDescription,
  twitterImage = 'https://stokonomi.com/og/stokonomi-og.png',
  articlePublishedTime,
  articleModifiedTime,
  faqs = [],
  breadcrumbs = [],
  noindex = false,
}: SeoProps) {
  useEffect(() => {
    const finalRobots = noindex ? 'noindex, follow' : robots;
    const finalOgTitle = ogTitle || title;
    const finalOgDescription = ogDescription || description;
    const finalOgUrl = ogUrl || canonical || getBaseUrl();
    const finalTwitterTitle = twitterTitle || title;
    const finalTwitterDescription = twitterDescription || description;

    // Document title
    document.title = title;

    // Meta tags
    upsertMeta('description', description);
    upsertMeta('robots', finalRobots);

    // Open Graph
    upsertMeta('og:type', ogType, true);
    upsertMeta('og:title', finalOgTitle, true);
    upsertMeta('og:description', finalOgDescription, true);
    upsertMeta('og:url', finalOgUrl, true);
    upsertMeta('og:image', ogImage, true);
    upsertMeta('og:locale', 'tr_TR', true);
    if (ogImageAlt) {
      upsertMeta('og:image:alt', ogImageAlt, true);
    }

    // Twitter
    upsertMeta('twitter:card', twitterCard);
    upsertMeta('twitter:title', finalTwitterTitle);
    upsertMeta('twitter:description', finalTwitterDescription);
    if (twitterImage) {
      upsertMeta('twitter:image', twitterImage);
    }

    // Canonical
    if (canonical) {
      upsertLink('canonical', canonical);
    } else {
      removeLink('canonical');
    }

    // Remove old JSON-LD scripts
    removeOldSeoScripts();

    // Article JSON-LD
    if (ogType === 'article' && articlePublishedTime) {
      injectJsonLd({
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: title,
        description: description,
        datePublished: articlePublishedTime,
        dateModified: articleModifiedTime || articlePublishedTime,
        mainEntityOfPage: {
          '@type': 'WebPage',
          '@id': canonical || finalOgUrl,
        },
        inLanguage: 'tr-TR',
        publisher: {
          '@type': 'Organization',
          name: 'Stokonomi',
          url: 'https://stokonomi.com/',
        },
        author: {
          '@type': 'Organization',
          name: 'Stokonomi',
          url: 'https://stokonomi.com/',
        },
        image: ogImage,
      });
    }

    // Breadcrumb JSON-LD
    if (breadcrumbs.length > 0) {
      injectJsonLd({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: breadcrumbs.map((item, index) => ({
          '@type': 'ListItem',
          position: index + 1,
          name: item.name,
          item: item.url,
        })),
      });
    }

    // FAQ JSON-LD
    if (faqs.length > 0) {
      injectJsonLd({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: faqs.map((faq) => ({
          '@type': 'Question',
          name: faq.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: faq.answer,
          },
        })),
      });
    }

    // Cleanup: remove page-specific SEO meta on unmount
    return () => {
      // Remove SEO scripts
      removeOldSeoScripts();

      // Remove canonical if it was added by this component
      if (canonical) {
        removeLink('canonical');
      }
    };
  }, [
    title,
    description,
    canonical,
    robots,
    ogType,
    ogTitle,
    ogDescription,
    ogUrl,
    ogImage,
    ogImageAlt,
    twitterCard,
    twitterTitle,
    twitterDescription,
    twitterImage,
    articlePublishedTime,
    articleModifiedTime,
    faqs,
    breadcrumbs,
    noindex,
  ]);

  return null;
}