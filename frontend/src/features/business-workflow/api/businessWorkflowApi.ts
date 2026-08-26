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

/** The backend deliberately owns the aggregate result shape until FU-F6. */
export interface BusinessWorkflowResultResponse {
  execution_id: string;
  workflow_type: 'business_workflow';
  dataset_id: string;
  completed_at: string;
  result: Record<string, unknown>;
}

export type BusinessWorkflowErrorKind =
  | 'unauthorized'
  | 'dataset-unavailable'
  | 'execution-unavailable'
  | 'result-not-ready'
  | 'service-unavailable'
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

export function classifyBusinessWorkflowError(error: unknown, endpoint: 'start' | 'execution' | 'result'): BusinessWorkflowApiError {
  if (!axios.isAxiosError(error)) return new BusinessWorkflowApiError('network');

  const status = (error as AxiosError).response?.status;
  if (status === 401) return new BusinessWorkflowApiError('unauthorized', status);
  if (status === 409) {
    return new BusinessWorkflowApiError(endpoint === 'result' ? 'result-not-ready' : 'dataset-unavailable', status);
  }
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
