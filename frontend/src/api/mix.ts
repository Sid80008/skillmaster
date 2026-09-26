import { apiClient } from './client';

export interface MixCandidate {
  id: string;
  skill_1_id: string;
  skill_1_name: string;
  skill_2_id: string;
  skill_2_name: string;
  mix_category: string;
  overlap_score: number;
}

export const getMixCandidates = async () => {
  const { data } = await apiClient.get<MixCandidate[]>('/mix/candidates');
  return data;
};
