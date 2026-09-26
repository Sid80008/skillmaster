import { apiClient } from './client';

export interface RecommendationCandidate {
  id: string;
  skill_id: string;
  skill_name: string;
  skill_catalog_version: number;
  rank: number;
  score: number;
  novelty_category: string;
  explanation: string;
}

export interface Recommendation {
  id: string;
  status: string;
  candidates: RecommendationCandidate[];
}

export const generateRecommendation = async () => {
  const { data } = await apiClient.post<Recommendation>('/recommendations/');
  return data;
};

export const presentRecommendation = async (id: string) => {
  const { data } = await apiClient.post(`/recommendations/${id}/present`);
  return data;
};

export const acceptRecommendation = async (id: string, skillId: string) => {
  const { data } = await apiClient.post(`/recommendations/${id}/accept`, {
    selected_skill_id: skillId,
  });
  return data;
};

export const rejectRecommendation = async (id: string, reason?: string) => {
  const { data } = await apiClient.post(`/recommendations/${id}/reject`, { reason });
  return data;
};
