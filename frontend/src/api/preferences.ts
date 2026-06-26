import api from './client';

export interface UserPreferences {
  id: string;
  user_id: string;
  categories: string[];
  keywords: string[];
  preferred_sources: string[];
  blocked_sources: string[];
  tracked_entities: { type: string; name: string }[];
  implicit_preferences: Record<string, number>;
}

export interface PreferenceStats {
  total_categories: number;
  total_keywords: number;
  total_preferred_sources: number;
  total_blocked_sources: number;
  total_tracked_entities: number;
}

export async function getPreferences(): Promise<UserPreferences> {
  const { data } = await api.get('/preferences');
  return data;
}

export async function updatePreferences(prefs: Partial<UserPreferences>): Promise<UserPreferences> {
  const { data } = await api.put('/preferences', prefs);
  return data;
}

export async function getPreferenceStats(): Promise<PreferenceStats> {
  const { data } = await api.get('/preferences/stats');
  return data;
}