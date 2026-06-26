import api from './client';

export interface ArticleSummary {
  id: string;
  title: string;
  source_name: string | null;
  source_url: string;
  tl_dr: string | null;
  key_takeaways: string[] | null;
  bias_rating: string | null;
  estimated_read_time_minutes: number | null;
  published_at: string | null;
  categories: string[];
  relevance_score: number;
  is_read: boolean;
  impact_radar: string[];
}

export interface DigestResponse {
  id: string;
  digest_type: string;
  title: string | null;
  content: string;
  articles: ArticleSummary[];
  generated_at: string;
  delivered_at: string | null;
}

export async function getDigest(type: string = 'daily', topic?: string): Promise<DigestResponse> {
  const params: Record<string, string> = { type };
  if (topic) params.topic = topic;
  const { data } = await api.get('/digest', { params });
  return data;
}

export async function getArticles(params?: {
  skip?: number;
  limit?: number;
  max_minutes?: number;
}): Promise<ArticleSummary[]> {
  const { data } = await api.get('/digest/articles', { params });
  return data;
}

export async function getArticleTLDR(articleId: string): Promise<any> {
  const { data } = await api.get(`/digest/articles/${articleId}/tldr`);
  return data;
}