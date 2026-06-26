import api from './client';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post('/auth/register', { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post('/auth/login', { email, password });
  return data;
}

export async function getMe(): Promise<{ id: string; email: string; is_active: boolean }> {
  const { data } = await api.get('/auth/me');
  return data;
}