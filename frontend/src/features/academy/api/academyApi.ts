import axios, { AxiosError } from 'axios';
import { API_BASE } from '../../../services/api';
import type {
  AcademyArticleDetail,
  AcademyArticleListItem,
} from '../content/types';
import {
  AcademyPayloadError,
  parseAcademyDetail,
  parseAcademyListResponse,
} from './academyParser';
import { AcademyApiError, classifyAcademyStatus } from './academyErrors';

// Public client deliberately has no auth interceptor or Directus configuration.
const academyHttp = axios.create({
  baseURL: API_BASE,
  headers: { Accept: 'application/json' },
});

function classifyAxiosError(error: AxiosError): AcademyApiError {
  const status = error.response?.status;
  return new AcademyApiError(classifyAcademyStatus(status), status);
}

function normalizeError(error: unknown): never {
  if (error instanceof AcademyApiError) throw error;
  if (error instanceof AcademyPayloadError) {
    throw new AcademyApiError('invalidPayload', 502);
  }
  if (axios.isAxiosError(error)) throw classifyAxiosError(error);
  throw new AcademyApiError('network');
}

export async function getAcademyArticles(): Promise<AcademyArticleListItem[]> {
  try {
    const response = await academyHttp.get('/api/public/academy/articles');
    return parseAcademyListResponse(response.data).items;
  } catch (error) {
    normalizeError(error);
  }
}

export async function getAcademyArticleBySlug(slug: string): Promise<AcademyArticleDetail> {
  try {
    const response = await academyHttp.get(
      `/api/public/academy/articles/${encodeURIComponent(slug)}`
    );
    return parseAcademyDetail(response.data);
  } catch (error) {
    normalizeError(error);
  }
}
