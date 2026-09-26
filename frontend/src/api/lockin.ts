import { apiClient } from './client';

export interface LockInSession {
  id: string;
  user_id: string;
  skill_id: string;
  status: string;
  started_at: string;
}

export const activateLockIn = async (skillId: string) => {
  const { data } = await apiClient.post<LockInSession>('/lock-in/activate', {
    skill_id: skillId
  });
  return data;
};

export const getCurrentLockIn = async () => {
  const { data } = await apiClient.get<LockInSession | null>('/lock-in/current');
  return data;
};

export const exitLockIn = async (reason?: string) => {
  const { data } = await apiClient.post('/lock-in/exit', { reason });
  return data;
};
