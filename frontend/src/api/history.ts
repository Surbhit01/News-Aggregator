import api from './client';

export interface HistoryEntry {
  id: string;
  article_id: string;
  read_time_seconds: number;
  clicked_at: string;
}

export async function logReading(articleId: string, readTimeSeconds: number = 0) {
  const { data } = await api.post('/history/log', { article_id: articleId, read_time_seconds: readTimeSeconds });
  return data;
}

export async function getHistory(limit: number = 50): Promise<HistoryEntry[]> {
  const { data } = await api.get('/history', { params: { limit } });
  return data;
}