// frontend/src/components/common/index.ts
// Stokonomi Design System - Tüm Common Component'lerin Export'u

// Layout Components
export { default as PageLayout } from './PageLayout';
export { default as SectionHeader } from './SectionHeader';
export type { SectionHeaderProps } from './SectionHeader';
export { default as Hero } from './Hero';
export type { HeroProps } from './Hero';

// Card Components
export { default as KpiCard } from './KpiCard';
export type { KpiCardProps } from './KpiCard';
export { default as MetricCard } from './MetricCard';
export type { MetricCardProps } from './MetricCard';
export { default as ExecutiveSummaryCard } from './ExecutiveSummaryCard';
export type { ExecutiveSummaryData } from './ExecutiveSummaryCard';
export { default as ProcessFlowCard } from './ProcessFlowCard';
export type { ProcessStep } from './ProcessFlowCard';

// Table Components
export { default as StandardTable } from './StandardTable';
export type { TableColumn } from './StandardTable';

// Badge Components
export { default as AIRecommendationBadge } from './AIRecommendationBadge';
export type { AIRecommendationType, AIRecommendationBadgeProps } from './AIRecommendationBadge';

// ✅ AI Assistant Card
export { default as AIAssistantCard } from './AIAssistantCard';
export type { AIAssistantData, AIAssistantCardProps } from './AIAssistantCard';