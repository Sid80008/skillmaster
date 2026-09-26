import { apiClient } from './client';

export interface SkillDNA {
  characteristic_slug: string;
  affinity_value: number;
  confidence: number;
  sample_count: number;
}

export interface UserCategoryProfile {
  category_id: string;
  category_name?: string;
  exposure_count: number;
  affinity_score: number;
  fatigue_level: number;
}

export interface ExplorationState {
  total_completed: number;
  total_abandoned: number;
  explored_families_count: number;
  unexplored_categories: string[];
  current_exploration_mode: string;
  is_locked_in: boolean;
}

export const getDNA = async () => {
  const { data } = await apiClient.get<SkillDNA[]>('/profile/dna');
  return data;
};

export const getCategoryProfiles = async () => {
  const { data } = await apiClient.get<UserCategoryProfile[]>('/profile/categories');
  return data;
};

export const getExplorationState = async () => {
  const { data } = await apiClient.get<ExplorationState>('/exploration/');
  return data;
};
