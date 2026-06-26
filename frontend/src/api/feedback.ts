import api from './client';

export async function submitFeedback(articleId: string, feedbackType: 'show_more' | 'show_less' | 'irrelevant') {
  const { data } = await api.post('/feedback', { article_id: articleId, feedback_type: feedbackType });
  return data;
}