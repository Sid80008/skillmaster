import { apiClient } from './client';

export interface QuestAttempt {
  id: string;
  user_id: string;
  quest_id: string;
  skill_id: string;
  skill_name?: string;
  activity_family_name?: string;
  category_name?: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Challenge {
  id: string;
  skill_id: string;
  title: string;
  objective: string;
  learn_content: string | null;
  do_content: string;
  finish_criteria: string;
  stretch_goal: string | null;
  why_this_matters: string | null;
  resources: string | null;
  estimated_duration_minutes: number;
  difficulty_level: number;
}

export interface RatingPayload {
  enjoyment: number;
  curiosity: number;
  deep_dive_interest: number;
  would_repeat: "yes" | "maybe" | "no";
  difficulty_felt: number;
  pre_interest: number;
}

export const getQuestHistory = async () => {
  const { data } = await apiClient.get<QuestAttempt[]>('/quests/attempts/');
  return data;
};

export const getCurrentQuest = async () => {
  const { data } = await apiClient.get<QuestAttempt | null>('/quests/current');
  return data;
};

export const getChallenge = async (attemptId: string) => {
  const { data } = await apiClient.get<Challenge>(`/quests/attempts/${attemptId}/challenge`);
  return data;
};

export const startQuest = async (attemptId: string) => {
  const { data } = await apiClient.post<QuestAttempt>(`/quests/attempts/${attemptId}/start`);
  return data;
};

export const completeQuest = async (attemptId: string) => {
  const { data } = await apiClient.post<QuestAttempt>(`/quests/attempts/${attemptId}/complete`);
  return data;
};

export const abandonQuest = async (attemptId: string, reason?: string) => {
  const { data } = await apiClient.post<QuestAttempt>(`/quests/attempts/${attemptId}/abandon`, { reason });
  return data;
};

export const submitFeedback = async (attemptId: string, payload: RatingPayload) => {
  const { data } = await apiClient.post(`/quests/attempts/${attemptId}/feedback`, payload);
  return data;
};
