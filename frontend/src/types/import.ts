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
  can_proceed?: boolean; // ✅ EKLENDI - Dataset Gate için
}

export interface DataQualitySummary {
  total_checks: number;
  passed: number;
  failed: number;
  score: number;
  business_errors?: number;
  error?: string;
  // ✅ YENİ ALANLAR
  total_structural?: number;
  total_missing?: number;
  total_type_errors?: number;
  total_business?: number;
  total_suggestions?: number;
  total_critical?: number;
  total_warnings?: number;
  total_info?: number;
  total_rows?: number;
}

export interface ColumnCheck {
  sheet: string;
  column: string;
  exists: boolean;
  status: 'success' | 'error';
  message: string;
}

// ✅ YENİ: ValidationError tipi (detaylı hata raporlaması için)
export interface ValidationError {
  sheet: string;
  row?: number;
  column?: string;
  canonical_field?: string;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  original_value?: any;
  expected_type?: string;
  coverage_percentage?: number;
  missing_rows_list?: number[];
  rows?: number[];
  auto_fixable: boolean;
  requires_user_action: boolean;
}

export interface DataQualityResult {
  column_checks: ColumnCheck[];
  structural_checks: any[];
  missing_data: any[];
  data_type_errors: any[];
  business_rule_errors: any[];
  summary: DataQualitySummary;
  score: number;
  can_proceed?: boolean;
  structural_errors?: ValidationError[];
  normalization_suggestions?: ValidationError[];
  // ✅ YENİ ALANLAR
  critical_errors?: ValidationError[];
  warnings?: ValidationError[];
  info_messages?: ValidationError[];
}

export interface NormalizationChange {
  sheet: string;
  column: string;
  original: string;
  new: string;
  confidence: number;
  row?: number; // ✅ EKLENDI - satır numarası için
  canonical_field?: string; // ✅ EKLENDI
  reason?: string; // ✅ EKLENDI
}

export interface NormalizationSuggestion {
  sheet: string;
  column: string;
  original: string;
  suggestion: string;
  confidence: number;
  row?: number; // ✅ EKLENDI
  canonical_field?: string; // ✅ EKLENDI
  message?: string; // ✅ EKLENDI
}

// frontend/src/types/import.ts - NormalizationError GÜNCELLENDİ

export interface NormalizationError {
  sheet: string;
  column: string;
  value: string;           // mevcut değer
  original_value?: string; // alternatif
  message: string;
  row?: number;
  canonical_field?: string;
  original?: string;       // bazı durumlar için
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
  // ✅ YENİ ALANLAR (detaylı impact için)
  problem?: string;
  reason?: string;
  affected_analyses?: string[];
  expected_result?: string;
}

export interface AnalysisImpact {
  analysis_scores: Record<string, number>;
  analysis_results: Record<string, ImpactItem[]>;
  detailed_impacts?: any[];
  ai_comment: string;
  ai_recommendation?: string;
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

// ✅ VALIDATION RESPONSE - GÜNCELLENDİ
export interface ValidationResponse {
  success: boolean;
  upload_id: string;
  can_proceed?: boolean; // ✅ EKLENDI - Dataset Gate için
  file_info: FileInfo;
  sheet_check: SheetCheck;
  data_quality: DataQualityResult;
  normalization: NormalizationResult | null;
  impact: AnalysisImpact;
  summary: ValidationSummary | string; // hem nesne hem string olabilir
  dataset_id?: number; // ✅ EKLENDI - oluşturulduysa
  error?: string; // ✅ EKLENDI - hata mesajı için
}

// ✅ RE-VALIDATION RESPONSE
export interface ReValidationResponse {
  success: boolean;
  validation_data: ValidationResponse;
  error?: string;
}

// ✅ DATASET CREATE RESPONSE
export interface DatasetCreateResponse {
  success: boolean;
  dataset_id: number;
  message?: string;
  error?: string;
}