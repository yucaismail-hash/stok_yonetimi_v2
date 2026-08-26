import { useQuery } from '@tanstack/react-query';
import { getCurrentPilotDataset } from './pilotDatasetApi';

export const pilotDatasetKeys = {
  all: ['dataset', 'pilot', 'current'] as const,
  current: (companyId: string) => ['dataset', 'pilot', 'current', companyId] as const,
};

export function useCurrentPilotDataset(companyId?: string) {
  return useQuery({
    queryKey: pilotDatasetKeys.current(companyId || 'anonymous'),
    queryFn: getCurrentPilotDataset,
    enabled: Boolean(companyId),
    staleTime: 30_000,
    retry: 1,
  });
}
