// frontend/src/types/import.ts

export interface FileInfo {
  file_name: string;
  file_size: number;
  sheet_count: number;
  total_rows: number;
  total_cols: number;
  sheets: string[];
}

export interface SheetCheckResult {
  sheet: string;
  exists: boolean;
  status: 'success' | 'error' | 'warning';
  message: string;
}

export interface SheetCheck {
  success: boolean;
  found: string[];
  missing: string[];
  results: SheetCheckResult[];
  summary: string;
}

export interface DataQualitySummary {
  total_checks: number;
  passed: number;
  failed: number;
  score: number;
  business_errors?: number;  // ✅ EKLENDI
  error?: string;
}

export interface ColumnCheck {
  sheet: string;
  column: string;
  exists: boolean;
  status: 'success' | 'error';
  message: string;
}

export interface DataQualityResult {
  column_checks: ColumnCheck[];
  structural_checks: any[];
  missing_data: any[];
  data_type_errors: any[];
  business_rule_errors: any[];
  summary: DataQualitySummary;
  score: number;
}

export interface NormalizationChange {
  sheet: string;
  column: string;
  original: string;
  new: string;
  confidence: number;
}

export interface NormalizationSuggestion {
  sheet: string;
  column: string;
  original: string;
  suggestion: string;
  confidence: number;
}

export interface NormalizationError {
  sheet: string;
  column: string;
  value: string;
  message: string;
}

export interface NormalizationResult {
  normalized_data: any;
  changes: NormalizationChange[];
  suggestions: NormalizationSuggestion[];
  errors: NormalizationError[];
  total_changes: number;
  total_suggestions: number;
  total_errors: number;
}

export interface ImpactItem {
  field: string;
  importance: string;
  status: string;
  message: string;
  recommendation?: string;
}

export interface AnalysisImpact {
  analysis_scores: Record<string, number>;
  analysis_results: Record<string, ImpactItem[]>;
  detailed_impacts?: any[];        // ✅ YENİ
  ai_comment: string;
  ai_recommendation?: string;      // ✅ YENİ - AI Önerisi
  overall_score: number;
}

export interface ValidationSummary {
  step1_file_info: FileInfo;
  step2_sheet_check: SheetCheck;
  step3_data_quality: DataQualityResult;
  step4_normalization: NormalizationResult;
  step5_impact: AnalysisImpact;
  summary: string;
}

export interface ValidationResponse {
  success: boolean;
  upload_id: string;
  file_info: FileInfo;
  sheet_check: SheetCheck;
  data_quality: DataQualityResult;
  normalization: NormalizationResult;
  impact: AnalysisImpact;
  summary: ValidationSummary;
}