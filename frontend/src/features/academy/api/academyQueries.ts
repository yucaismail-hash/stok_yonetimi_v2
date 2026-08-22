import { useQuery } from '@tanstack/react-query';
import {
  getAcademyArticleBySlug,
  getAcademyArticles,
} from './academyApi';
import { AcademyApiError } from './academyErrors';
import { academyQueryKeys } from './academyQueryKeys';

const STALE_TIME_MS = 60_000;

function retryAcademyQuery(failureCount: number, error: Error): boolean {
  if (!(error instanceof AcademyApiError)) return false;
  if (
    error.kind === 'notFound' ||
    error.kind === 'validation' ||
    error.kind === 'invalidPayload'
  ) {
    return false;
  }
  return failureCount < 2;
}

export function useAcademyArticles() {
  return useQuery({
    queryKey: academyQueryKeys.articles,
    queryFn: getAcademyArticles,
    staleTime: STALE_TIME_MS,
    retry: retryAcademyQuery,
  });
}

export function useAcademyArticle(slug: string | undefined) {
  return useQuery({
    queryKey: academyQueryKeys.article(slug ?? ''),
    queryFn: () => getAcademyArticleBySlug(slug!),
    enabled: Boolean(slug),
    staleTime: STALE_TIME_MS,
    retry: retryAcademyQuery,
  });
}
