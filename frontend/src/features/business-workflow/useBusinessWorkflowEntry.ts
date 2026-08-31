import { useCallback, useEffect, useState } from 'react';

import { useStartBusinessWorkflow } from './api';

/**
 * Keeps the existing, device-local pointer to a Business Workflow execution.
 * The API remains authoritative: a fresh start request can still resolve to
 * the company's already-active workflow.
 */
export function useBusinessWorkflowEntry(companyId?: string) {
  const startWorkflow = useStartBusinessWorkflow();
  const markerKey = companyId ? `stokonomi:business-workflow:active-execution:${companyId}` : undefined;
  const [executionId, setExecutionId] = useState<string | undefined>();
  const [duplicateExecution, setDuplicateExecution] = useState(false);

  useEffect(() => {
    setExecutionId(markerKey ? window.localStorage.getItem(markerKey) || undefined : undefined);
    setDuplicateExecution(false);
  }, [markerKey]);

  const clearUnavailableExecution = useCallback(() => {
    if (markerKey) window.localStorage.removeItem(markerKey);
    setExecutionId(undefined);
    setDuplicateExecution(false);
  }, [markerKey]);

  const startBusinessWorkflow = useCallback(() => {
    startWorkflow.mutate(undefined, {
      onSuccess: (response) => {
        if (markerKey) window.localStorage.setItem(markerKey, response.execution_id);
        setDuplicateExecution(response.duplicate);
        setExecutionId(response.execution_id);
      },
    });
  }, [markerKey, startWorkflow]);

  return {
    executionId,
    duplicateExecution,
    startWorkflow,
    startBusinessWorkflow,
    clearUnavailableExecution,
  };
}
