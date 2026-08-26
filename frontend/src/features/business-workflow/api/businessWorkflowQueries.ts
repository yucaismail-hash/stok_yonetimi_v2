import { useMutation, useQuery } from '@tanstack/react-query';

import {
  BusinessWorkflowApiError,
  getExecution,
  getExecutionResult,
  startBusinessWorkflow,
  type ExecutionStatus,
} from './businessWorkflowApi';

const activeStatuses: ReadonlySet<ExecutionStatus> = new Set([
  'created',
  'queued',
  'running',
  'waiting',
  'retrying',
]);

export const businessWorkflowKeys = {
  all: ['business-workflow'] as const,
  execution: (executionId: string) => ['business-workflow', 'execution', executionId] as const,
  result: (executionId: string) => ['business-workflow', 'result', executionId] as const,
};

function retryNonClientError(failureCount: number, error: unknown) {
  const status = error instanceof BusinessWorkflowApiError ? error.status : undefined;
  if (status && status >= 400 && status < 500) return false;
  return failureCount < 1;
}

export function isActiveExecution(status?: ExecutionStatus) {
  return status !== undefined && activeStatuses.has(status);
}

export function useStartBusinessWorkflow() {
  return useMutation({ mutationFn: startBusinessWorkflow });
}

export function useExecution(executionId?: string) {
  return useQuery({
    queryKey: businessWorkflowKeys.execution(executionId || 'none'),
    queryFn: () => getExecution(executionId as string),
    enabled: Boolean(executionId),
    staleTime: 0,
    retry: retryNonClientError,
    retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 5_000),
    refetchInterval: (query) => (isActiveExecution(query.state.data?.status) ? 5_000 : false),
    refetchIntervalInBackground: false,
  });
}

export function useExecutionResult(executionId?: string, enabled = false) {
  return useQuery({
    queryKey: businessWorkflowKeys.result(executionId || 'none'),
    queryFn: () => getExecutionResult(executionId as string),
    enabled: Boolean(executionId) && enabled,
    staleTime: Infinity,
    retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 5_000),
    retry: (failureCount, error) => {
      if (error instanceof BusinessWorkflowApiError && error.kind === 'result-not-ready') return failureCount < 1;
      return retryNonClientError(failureCount, error);
    },
  });
}
