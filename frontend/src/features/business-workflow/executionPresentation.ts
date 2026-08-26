import type { ExecutionStatus } from './api';

export interface ExecutionStatusPresentation {
  title: string;
  description: string;
  terminal: boolean;
}

export const executionStatusPresentation: Record<ExecutionStatus, ExecutionStatusPresentation> = {
  created: { title: 'Analiz hazırlanıyor', description: 'İşlem güvenli biçimde oluşturuluyor.', terminal: false },
  queued: { title: 'Analiz sıraya alındı', description: 'Analiz arka planda başlayacak.', terminal: false },
  running: { title: 'Analiz çalışıyor', description: 'Analiz arka planda devam ediyor.', terminal: false },
  waiting: { title: 'Analiz bekliyor', description: 'Bir bağımlılığın veya sıradaki adımın tamamlanması bekleniyor.', terminal: false },
  retrying: { title: 'Bir adım yeniden deneniyor', description: 'Geçici bir durum nedeniyle analiz devam ediyor.', terminal: false },
  completed: { title: 'Analiz tamamlandı', description: 'Sonuç paketi hazır.', terminal: true },
  failed: { title: 'Analiz tamamlanamadı', description: 'İşlem güvenli şekilde durduruldu.', terminal: true },
  cancelled: { title: 'Analiz iptal edildi', description: 'Bu işlem artık çalışmıyor.', terminal: true },
};

const stageLabels: Record<string, string> = {
  planning: 'Analiz planı hazırlanıyor',
  forecast: 'Talep Tahmini',
  safety_stock: 'Emniyet Stoku',
  simulation: 'Senaryo Simülasyonu',
  backtest: 'Geçmiş Performans Testi',
  supplier: 'Tedarikçi Analizi',
};

/** Only labels a stage actually returned by the backend. */
export function presentWorkflowStage(stage: string | null) {
  if (!stage) return null;
  return stageLabels[stage] || stage;
}

/** Backend normally returns a controlled failure code; never surface arbitrary internals. */
export function safeFailureSummary(value: string | null) {
  if (!value) return null;
  return /^[A-Z0-9_ -]{1,120}$/.test(value) ? value : 'WORKFLOW_EXECUTION_FAILED';
}
