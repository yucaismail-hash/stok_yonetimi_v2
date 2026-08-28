type GtagArgs = [command: 'js', date: Date] | [command: 'config', targetId: string, config?: Record<string, unknown>] | [command: 'event', eventName: string, params?: Record<string, unknown>];

export const PUBLIC_ANALYTICS_EVENTS = {
  LANDING_PRIMARY_CTA_CLICK: 'landing_primary_cta_click',
  LANDING_ACADEMY_CTA_CLICK: 'landing_academy_cta_click',
  ACADEMY_CARD_CLICK: 'academy_card_click',
  ACADEMY_ARTICLE_VIEW: 'academy_article_view',
  ACADEMY_TO_LANDING_CLICK: 'academy_to_landing_click',
  ACADEMY_CONTINUE_CLICK: 'academy_continue_click',
  ACADEMY_LISTING_TO_LANDING_CLICK: 'academy_listing_to_landing_click',
  NAVBAR_ACADEMY_CLICK: 'navbar_academy_click',
} as const;

type PublicAnalyticsEventParams = {
  [PUBLIC_ANALYTICS_EVENTS.LANDING_PRIMARY_CTA_CLICK]: { placement: string; destination: string };
  [PUBLIC_ANALYTICS_EVENTS.LANDING_ACADEMY_CTA_CLICK]: { placement: string; destination: string };
  [PUBLIC_ANALYTICS_EVENTS.ACADEMY_CARD_CLICK]: { article_slug: string; category: string; position: number; surface: 'landing' | 'academy' };
  [PUBLIC_ANALYTICS_EVENTS.ACADEMY_ARTICLE_VIEW]: { article_slug: string; category: string };
  [PUBLIC_ANALYTICS_EVENTS.ACADEMY_TO_LANDING_CLICK]: { article_slug: string; placement: string; destination: string };
  [PUBLIC_ANALYTICS_EVENTS.ACADEMY_CONTINUE_CLICK]: { article_slug: string; placement: string; destination: string };
  [PUBLIC_ANALYTICS_EVENTS.ACADEMY_LISTING_TO_LANDING_CLICK]: { placement: string; destination: string };
  [PUBLIC_ANALYTICS_EVENTS.NAVBAR_ACADEMY_CLICK]: { placement: string; destination: string };
};

export type PublicAnalyticsEventName = keyof PublicAnalyticsEventParams;

declare global {
  interface Window {
    dataLayer?: IArguments[];
    gtag?: (...args: GtagArgs) => void;
  }
}

const measurementId = import.meta.env.VITE_GA_MEASUREMENT_ID;
const enabled = import.meta.env.PROD && Boolean(measurementId);
const scriptId = 'ga4-gtag-js';

let initialized = false;

export function initGoogleAnalytics() {
  if (!enabled || !measurementId || typeof window === 'undefined' || typeof document === 'undefined') return false;
  if (initialized) return true;

  try {
    window.dataLayer = window.dataLayer ?? [];
    window.gtag =
      window.gtag ??
      function gtag(..._args: GtagArgs) {
        // Match Google's bootstrap snippet: gtag.js consumes Arguments entries, not Arrays.
        window.dataLayer?.push(arguments);
      };

    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
      document.head.appendChild(script);
    }

    window.gtag('js', new Date());
    window.gtag('config', measurementId, {
      send_page_view: false,
    });

    initialized = true;
    return true;
  } catch {
    // Analytics is optional and must never interrupt public page rendering or navigation.
    return false;
  }
}

export function trackPageView(pagePath: string) {
  if (!initGoogleAnalytics()) return;

  try {
    window.gtag?.('event', 'page_view', {
      page_path: pagePath,
      page_location: window.location.href,
      page_title: document.title,
    });
  } catch {
    // Analytics must never interrupt public page rendering or navigation.
  }
}

export function trackPublicEvent<EventName extends PublicAnalyticsEventName>(
  name: EventName,
  params: PublicAnalyticsEventParams[EventName],
) {
  if (!initGoogleAnalytics()) return;

  try {
    window.gtag?.('event', name, params);
  } catch {
    // Analytics must never interrupt public page rendering or navigation.
  }
}
