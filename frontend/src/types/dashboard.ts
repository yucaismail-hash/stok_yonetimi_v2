// frontend/src/types/dashboard.ts - AlertItem (GÜNCELLENMİŞ)

export interface AlertItem {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  action_label: string;
  action_path: string;
  priority?: number;
  // ✅ YENİ ALANLAR
  analysis_id?: number;
  analysis_type?: string;
  dataset_id?: number | null;
  critical_items?: CriticalItem[];
  ai_comment?: string;
}

export interface ChangeItem {
  old: number;
  new: number;
  change: number;
  improved: boolean;
  label?: string;
}

export interface ChangeMeta {
  analysis_id: number;
  created_at: string;
}

// ✅ _meta alanını ChangeMeta olarak tanımla
export interface ModuleChanges {
  [key: string]: ChangeItem | ChangeMeta | undefined;
  _meta?: ChangeMeta;
}

export interface DashboardChangeResponse {
  success: boolean;
  changes: {
    forecast?: ModuleChanges;
    safety_stock?: ModuleChanges;
    supplier?: ModuleChanges;
    simulation?: ModuleChanges;
    backtest?: ModuleChanges;
  };
  gains: string[];
  has_changes: boolean;
  error?: string;
}

// Aksiyon Dialog için
export interface CriticalItem {
  code: string;
  name?: string;
  current_stock?: number;
  min_stock?: number;
  risk_score?: number;
  estimated_days?: number;
  ss?: number;  // Safety Stock değeri
  risk_level?: string;
  [key: string]: any;
}

export interface ActionDialogData {
  title: string;
  summary: string;
  critical_items: CriticalItem[];
  ai_comment?: string;
  analysis_id: number;
  analysis_type: string;
  target_page: string;
  dataset_id?: number | null;
}