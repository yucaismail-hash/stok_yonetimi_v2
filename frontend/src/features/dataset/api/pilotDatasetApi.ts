import api from '../../../services/api';

export interface PilotIssue { code: string; sheet?: string | null; row?: number | null; column?: string | null; severity: string; message: string; }
export interface PilotUploadResponse {
  dataset_id: string; status: string; same_file_retry: boolean; issues: PilotIssue[]; warnings: PilotIssue[];
  summary: { record_count: number; material_count: number };
  READY_FOR_ACCEPTANCE: boolean;
}
export interface PilotAcceptResponse { status: 'READY_FOR_WORKFLOW'; dataset_id: string; version_id?: string; ledger?: unknown; idempotent: boolean; }
export interface CurrentPilotDataset {
  dataset_id: string;
  status: 'READY_FOR_WORKFLOW';
  accepted: true;
  accepted_at: string;
  created_at: string;
  source_name: string | null;
  record_count: number;
  material_count: number;
}

export interface PilotUploadOptions { demandType: 'sales' | 'consumption'; serviceLevel: { mode: 'automatic' } | { mode: 'manual'; value: number }; }
export async function uploadPilotDataset(file: File, options: PilotUploadOptions): Promise<PilotUploadResponse> {
  const form = new FormData(); form.append('file', file); form.append('demand_type', options.demandType); form.append('service_level_mode', options.serviceLevel.mode);
  if (options.serviceLevel.mode === 'manual') form.append('service_level_value', String(options.serviceLevel.value));
  const response = await api.post<PilotUploadResponse>('/api/v2/dataset/pilot/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  return response.data;
}
export async function downloadPilotTemplate(): Promise<void> {
  const response = await api.get('/api/v2/dataset/pilot/template', { responseType: 'blob' });
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'Stokonomi_Resmi_Veri_Sablonu_v3.xlsx'; anchor.click();
  URL.revokeObjectURL(url);
}
export async function acceptPilotDataset(datasetId: string): Promise<PilotAcceptResponse> {
  const response = await api.post<PilotAcceptResponse>(`/api/v2/dataset/pilot/${encodeURIComponent(datasetId)}/accept`);
  return response.data;
}
export async function getCurrentPilotDataset(): Promise<CurrentPilotDataset | null> {
  const response = await api.get<CurrentPilotDataset | null>('/api/v2/dataset/pilot/current');
  return response.data;
}
