// frontend/src/types/recommendation.ts

export interface Recommendation {
  title: string;
  reason: string;
  benefit: string;
  target_page: string;
  analysis_type: string;
  analysis_id: number | null;
  priority: number;
  action_label: string;
  critical_count?: number;
  critical_items?: any[];
  high_risk_suppliers?: string[];
  dataset_id?: number;
}