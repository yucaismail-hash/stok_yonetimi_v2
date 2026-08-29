import axios, { AxiosError } from 'axios';

import api from '../../../services/api';

export type ExecutionStatus =
  | 'created'
  | 'queued'
  | 'running'
  | 'waiting'
  | 'retrying'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface BusinessWorkflowStartResponse {
  execution_id: string;
  status: ExecutionStatus;
  created_at: string;
  workflow_type: 'business_workflow';
  dataset_id: string;
  duplicate: boolean;
}

export interface ExecutionDetail {
  execution_id: string;
  status: ExecutionStatus;
  progress: number;
  current_stage: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  failure_summary: string | null;
  dataset_id: string;
  workflow_type: 'business_workflow';
  workflow_id: string;
}

export interface AnalyticalModuleResult<TItem extends Record<string, unknown> = Record<string, unknown>> {
  items: TItem[];
  metrics?: Record<string, unknown>;
  warnings?: unknown[];
}

export interface ForecastResultItem extends Record<string, unknown> {
  material_code: string;
  forecast: number[];
  model_used?: string;
  lower_80?: number[];
  upper_80?: number[];
  lower_95?: number[];
  upper_95?: number[];
  selection_info?: Record<string, unknown>;
}

export interface SafetyStockResultItem extends Record<string, unknown> {
  material_code: string;
  safety_stock: number;
  service_level?: number;
  selected_method?: string;
  effective_lead_time_used?: number;
  effective_unit?: string;
  lead_time_source?: string;
  demand_observations?: number;
}

export interface SimulationResultItem extends Record<string, unknown> {
  material_code: string;
  service_level?: number;
  cvar_95?: number;
  rop?: number;
  weeks?: number;
  n_simulations?: number;
  lead_time_days?: number;
  stockout_probability?: number[];
}

export interface BacktestResultItem extends Record<string, unknown> {
  material_code: string;
  backtest_mode?: string;
  validated_strategy?: string | null;
  strategies_tested?: string[];
  metrics?: Record<string, Record<string, unknown>>;
  recommendation?: Record<string, unknown>;
  test_window?: number;
}

export interface SupplierResultItem extends Record<string, unknown> {
  supplier_id: string;
  name?: string;
  risk_score?: number;
  performance_score?: number;
  lead_time_mean?: number;
  lead_time_std?: number;
  supplier_factor?: number;
  material_mappings?: { material_code: string; share?: number }[];
}

/** Exact durable Business Workflow aggregate envelope; Supplier is conditional. */
export interface BusinessWorkflowAggregateResult {
  execution_id: string;
  workflow_type: 'business_workflow';
  workflow_version?: string;
  dataset_id: string;
  company_id: string;
  forecast?: AnalyticalModuleResult<ForecastResultItem> & { horizon?: number };
  safety_stock?: AnalyticalModuleResult<SafetyStockResultItem> & {
    service_level?: number;
    service_level_metadata?: Record<string, unknown>;
  };
  simulation?: AnalyticalModuleResult<SimulationResultItem>;
  backtest?: AnalyticalModuleResult<BacktestResultItem>;
  supplier?: { suppliers: SupplierResultItem[]; mapping_count?: number; provenance?: Record<string, unknown> };
  provenance?: Record<string, string>;
}

export interface BusinessWorkflowResultResponse {
  execution_id: string;
  workflow_type: 'business_workflow';
  dataset_id: string;
  completed_at: string;
  result: BusinessWorkflowAggregateResult;
}

/** Mirrors app.schemas.business_workflow_presentation exactly. */
export interface ExecutionPresentation {
  execution_id: string;
  status: ExecutionStatus;
  progress: number;
  current_stage: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  dataset_id: string;
  workflow_id: string;
  failure_summary: string | null;
}

export interface AggregatePresentation {
  result_reference_id: string;
  result_type: string;
  result_version: string;
  contract_version: string;
  validation_status: string;
  created_at: string;
  available_result_types: string[];
}

export interface DecisionFinalizationPresentation {
  id: string;
  status: 'pending' | 'running' | 'succeeded' | 'partially_succeeded' | 'failed';
  attempt_count: number;
  completed_material_codes: string[];
  limitations: Record<string, unknown>[];
  finalized_at: string | null;
}

export interface DecisionAssociationPresentation {
  id: string;
  decision_snapshot_id: string;
  material_code: string;
  demand_type: string;
  decision_context: string;
  decision_cutoff_period: string;
}

export interface DecisionSnapshotPresentation {
  id: string;
  status: string;
  agreement_status: string;
  confidence: number;
  decision_policy_version: string;
  confidence_policy_version: string;
  generated_at: string;
  uncertainty_codes: string[];
}

export interface DecisionCandidatePresentation {
  ordinal: number;
  candidate_type: string;
  severity: string;
  priority: number;
  reason_codes: string[];
  supporting_evidence: unknown[];
  conflicting_evidence: unknown[];
  confidence: number;
  expected_impact_references: unknown[];
  what_would_change_this: unknown[];
}

export interface DecisionExplanationSourcePresentation {
  group: string;
  source: string;
  semantic_type: string;
  evidence: unknown;
}

export interface DecisionExplanationPresentation {
  decision: Record<string, unknown>;
  limitations: string[];
  source_provenance: DecisionExplanationSourcePresentation[];
  explanation_fingerprint: string;
}

export interface DecisionPresentationItem {
  association: DecisionAssociationPresentation;
  snapshot: DecisionSnapshotPresentation;
  candidates: DecisionCandidatePresentation[];
  explanation: DecisionExplanationPresentation;
}

export interface BusinessWorkflowDecisionPresentationResponse {
  execution: ExecutionPresentation;
  aggregate: AggregatePresentation | null;
  decision_finalization: DecisionFinalizationPresentation | null;
  decisions: DecisionPresentationItem[];
}

export interface DecisionFeedbackRequest {
  feedback_type: 'HELPFUL' | 'NOT_HELPFUL';
  candidate_ordinal?: number;
  candidate_type?: string;
  comment?: string;
  source_metadata?: Record<string, unknown>;
  supersedes_feedback_id?: string;
}

export interface DecisionFeedbackResponse {
  status: 'CREATED' | 'ALREADY_EXISTS';
  feedback_id: string;
}

export type BusinessWorkflowErrorKind =
  | 'unauthorized'
  | 'dataset-unavailable'
  | 'execution-unavailable'
  | 'result-not-ready'
  | 'service-unavailable'
  | 'feedback-invalid'
  | 'network'
  | 'unknown';

export class BusinessWorkflowApiError extends Error {
  constructor(
    public readonly kind: BusinessWorkflowErrorKind,
    public readonly status?: number,
  ) {
    super(kind);
    this.name = 'BusinessWorkflowApiError';
  }
}

export function classifyBusinessWorkflowError(error: unknown, endpoint: 'start' | 'execution' | 'result' | 'decision' | 'feedback'): BusinessWorkflowApiError {
  if (!axios.isAxiosError(error)) return new BusinessWorkflowApiError('network');

  const status = (error as AxiosError).response?.status;
  if (status === 401) return new BusinessWorkflowApiError('unauthorized', status);
  if (status === 409) {
    return new BusinessWorkflowApiError(endpoint === 'result' ? 'result-not-ready' : 'dataset-unavailable', status);
  }
  if ((status === 400 || status === 422) && endpoint === 'feedback') return new BusinessWorkflowApiError('feedback-invalid', status);
  if (status === 404) return new BusinessWorkflowApiError('execution-unavailable', status);
  if (status === 503) return new BusinessWorkflowApiError('service-unavailable', status);
  if (!status) return new BusinessWorkflowApiError('network');
  return new BusinessWorkflowApiError('unknown', status);
}

export async function startBusinessWorkflow(): Promise<BusinessWorkflowStartResponse> {
  try {
    const response = await api.post<BusinessWorkflowStartResponse>('/api/v2/workflows/business', {});
    return response.data;
  } catch (error) {
    throw classifyBusinessWorkflowError(error, 'start');
  }
}

export async function getExecution(executionId: string): Promise<ExecutionDetail> {
  try {
    const response = await api.get<ExecutionDetail>(`/api/v2/executions/${encodeURIComponent(executionId)}`);
    return response.data;
  } catch (error) {
    throw classifyBusinessWorkflowError(error, 'execution');
  }
}

export async function getExecutionResult(executionId: string): Promise<BusinessWorkflowResultResponse> {
  try {
    const response = await api.get<BusinessWorkflowResultResponse>(
      `/api/v2/executions/${encodeURIComponent(executionId)}/result`,
    );
    return response.data;
  } catch (error) {
    throw classifyBusinessWorkflowError(error, 'result');
  }
}

export async function getBusinessWorkflowDecision(executionId: string): Promise<BusinessWorkflowDecisionPresentationResponse> {
  try {
    const response = await api.get<BusinessWorkflowDecisionPresentationResponse>(
      `/api/v2/executions/${encodeURIComponent(executionId)}/decision`,
    );
    return response.data;
  } catch (error) {
    throw classifyBusinessWorkflowError(error, 'decision');
  }
}

export async function recordDecisionFeedback(
  executionId: string,
  snapshotId: string,
  request: DecisionFeedbackRequest,
): Promise<DecisionFeedbackResponse> {
  try {
    const response = await api.post<DecisionFeedbackResponse>(
      `/api/v2/executions/${encodeURIComponent(executionId)}/decisions/${encodeURIComponent(snapshotId)}/feedback`,
      request,
    );
    return response.data;
  } catch (error) {
    throw classifyBusinessWorkflowError(error, 'feedback');
  }
}
