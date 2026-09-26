import { apiClient } from './client';

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
}

export const getCurrentUser = async () => {
  const { data } = await apiClient.get<User>('/auth/me');
  return data;
};

export const login = async (email: string, password: string) => {
  const params = new URLSearchParams();
  params.append('username', email); // The backend OAuth2 uses username for email
  params.append('password', password);
  
  const { data } = await apiClient.post<{access_token: string}>('/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return data;
};

export const register = async (email: string, username: string, password: string) => {
  const { data } = await apiClient.post<User>('/auth/register', { email, username, password });
  return data;
};
