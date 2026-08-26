export const SEO_SITE_URL = 'https://www.stokonomi.com';
export const DEFAULT_OG_IMAGE = `${SEO_SITE_URL}/og/stokonomi-og.png`;

export function canonicalUrl(path = '/') {
  return new URL(path, `${SEO_SITE_URL}/`).toString();
}

export function httpImageOrDefault(value: string | null | undefined) {
  if (!value) return DEFAULT_OG_IMAGE;

  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:'
      ? url.toString()
      : DEFAULT_OG_IMAGE;
  } catch {
    return DEFAULT_OG_IMAGE;
  }
}
