export type AcademyErrorKind =
  | 'notFound'
  | 'validation'
  | 'invalidPayload'
  | 'upstream'
  | 'unavailable'
  | 'timeout'
  | 'network';

export class AcademyApiError extends Error {
  readonly kind: AcademyErrorKind;
  readonly status?: number;

  constructor(kind: AcademyErrorKind, status?: number) {
    super(`Academy API request failed: ${kind}`);
    this.name = 'AcademyApiError';
    this.kind = kind;
    this.status = status;
  }
}

export function classifyAcademyStatus(status?: number): AcademyErrorKind {
  if (status === 404) return 'notFound';
  if (status === 502) return 'upstream';
  if (status === 503) return 'unavailable';
  if (status === 504) return 'timeout';
  if (status && status >= 400 && status < 500) return 'validation';
  return 'network';
}
