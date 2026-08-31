// src/constants/routes.ts
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  BUSINESS_ANALYSIS: '/business-analysis',
  BUSINESS_RESULTS: '/business-results',
  BUSINESS_HISTORY: '/business-history',
  SAFETY_STOCK: '/safety-stock',
  FORECAST: '/forecast',
  SIMULATION: '/simulation',
  BACKTEST: '/backtest',
  SUPPLIER: '/supplier',
  RISK: '/risk',
  PROFILE: '/profile',
  ADMIN: '/admin',
  TASKS: '/tasks',
  EXECUTION_RESULTS: (executionId: string) => `/executions/${encodeURIComponent(executionId)}/results`,
  PRICING: '/pricing',
  EXECUTIVE_SUMMARY: '/executive-summary',
  AI_ANALYSIS: '/ai-analysis',
} as const;

export type AppRoute = typeof ROUTES[keyof typeof ROUTES];

// Landing Page içi CTA yönlendirmeleri
export const CTA_ROUTES = {
  GET_STARTED: ROUTES.REGISTER,
  DEMO: '#demo',
  PRICING: ROUTES.PRICING,
  SAFETY_STOCK: ROUTES.SAFETY_STOCK,
  FORECAST: ROUTES.FORECAST,
  SIMULATION: ROUTES.SIMULATION,
  BACKTEST: ROUTES.BACKTEST,
  EXECUTIVE_SUMMARY: ROUTES.EXECUTIVE_SUMMARY,
  AI_ANALYSIS: ROUTES.AI_ANALYSIS,
};
