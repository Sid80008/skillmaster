import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateRecommendation, acceptRecommendation, rejectRecommendation, presentRecommendation, Recommendation } from '../api/recommendations';
import { getCurrentQuest } from '../api/quests';

export const Explore = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rec, setRec] = useState<Recommendation | null>(null);

  const fetchExploreState = async () => {
    try {
      setLoading(true);
      const activeQuest = await getCurrentQuest();
      if (activeQuest && (activeQuest.status === 'active' || activeQuest.status === 'pending')) {
        navigate('/quest');
        return;
      }
      
      const newRec = await generateRecommendation();
      setRec(newRec);
      
      if (newRec.status === 'pending') {
        presentRecommendation(newRec.id).catch(console.error);
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError("You've explored everything we have for now! Check back later.");
      } else {
        setError(err.response?.data?.detail || 'Failed to generate recommendation.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExploreState();
  }, []);

  const handleAccept = async (skillId: string) => {
    if (!rec) return;
    try {
      await acceptRecommendation(rec.id, skillId);
      navigate('/quest');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to accept.');
    }
  };

  const handleReject = async () => {
    if (!rec) return;
    try {
      setLoading(true);
      await rejectRecommendation(rec.id);
      await fetchExploreState();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-on-surface-variant gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-spin text-tertiary">explore</span>
        <p className="font-label-md uppercase tracking-widest">Generating Horizon...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <p className="text-on-surface text-xl">{error}</p>
        <button onClick={fetchExploreState} className="mt-6 px-6 py-2 bg-primary-container text-on-primary-container rounded-lg font-bold">Try Again</button>
      </div>
    );
  }

  if (!rec || rec.candidates.length === 0) return null;

  const candidate = rec.candidates[0]; // Highest ranked candidate

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-8 w-full">
      <div className="flex flex-col w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8">
          <div className="flex flex-col gap-3">
            <div className="inline-flex items-center gap-2 self-start px-3 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm uppercase tracking-widest shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse"></span>
              <span>Exploration Horizon</span>
            </div>
            <h1 className="font-headline-lg text-headline-lg tracking-tight text-on-surface">
              What will you try this weekend?
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">
              A fresh venture chosen to break routine and explore uncharted territory.
            </p>
          </div>
          <div className="flex items-center gap-3 self-start md:self-auto shrink-0 bg-surface-container-lowest px-4 py-2.5 rounded-xl shadow-md">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-tertiary-container/20 text-tertiary">
              <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>explore</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-sm text-label-sm text-tertiary uppercase tracking-wider">Field Horizon Status</span>
              <span className="font-label-lg text-label-lg text-on-surface font-semibold">{candidate.novelty_category.replace(/_/g, ' ')}</span>
            </div>
          </div>
        </div>

        <section className="relative w-full rounded-2xl bg-surface-container p-6 md:p-10 shadow-xl overflow-hidden">
          <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-primary-container/10 blur-3xl pointer-events-none"></div>
          <div className="absolute -bottom-24 -left-20 w-80 h-80 rounded-full bg-secondary-container/15 blur-3xl pointer-events-none"></div>
          
          <div className="relative grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 flex flex-col gap-6">
              <div className="relative group rounded-xl overflow-hidden bg-surface-container-lowest shadow-lg aspect-[4/3] lg:aspect-[5/4] w-full flex items-center justify-center">
                {/* Fallback pattern since we don't have images per skill in DB yet */}
                <span className="material-symbols-outlined text-9xl text-surface-container-high">explore</span>
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent pointer-events-none"></div>
                <div className="absolute top-4 left-4 flex flex-wrap gap-2">
                  <span className="px-2.5 py-1 rounded-md bg-secondary-container/80 backdrop-blur-md text-on-secondary-container font-label-sm uppercase tracking-wider">
                    {candidate.novelty_category.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                  <span className="font-label-sm text-on-surface-variant font-mono tracking-widest uppercase">
                    SKILL REF // SQ-{candidate.skill_id.substring(0, 4)}
                  </span>
                  <span className="font-label-sm text-primary font-mono tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span> NEW HORIZON
                  </span>
                </div>
              </div>
              <div className="bg-surface-container-low rounded-xl p-5 shadow-sm flex flex-col gap-3">
                <div className="flex items-center gap-2 text-primary-container">
                  <span className="material-symbols-outlined text-sm">nature_people</span>
                  <span className="font-label-sm uppercase tracking-widest font-bold">Field Catalyst Note</span>
                </div>
                <p className="font-body-md text-on-surface leading-relaxed">
                  {candidate.explanation || "This skill represents a totally new intersection of interests for your profile."}
                </p>
              </div>
            </div>

            <div className="lg:col-span-7 flex flex-col justify-between h-full gap-8">
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-on-surface-variant font-label-md">
                    <span className="text-tertiary font-semibold uppercase tracking-wider">Discipline Focus</span>
                    <span>•</span>
                    <span>Match Score: {(candidate.score * 100).toFixed(0)}%</span>
                  </div>
                  <h2 className="font-display-hero text-headline-lg md:text-display-hero text-on-surface tracking-tight leading-none">
                    {candidate.skill_name}
                  </h2>
                </div>
                
                <p className="font-body-lg text-on-surface-variant leading-relaxed">
                  Accept this quest to reveal the full step-by-step field manifest. You can always abandon it with no penalty if it doesn't fit your weekend.
                </p>
              </div>

              <div className="flex flex-col gap-4 pt-4">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                  <button 
                    onClick={() => handleAccept(candidate.skill_id)}
                    className="flex-1 px-4 sm:px-8 py-4 rounded-xl bg-primary-container text-on-primary font-headline-sm font-bold flex items-center justify-center gap-3 transition-all transform active:scale-95 shadow-xl hover:shadow-[0_0_30px_rgba(255,107,53,0.45)] text-center"
                  >
                    <span className="material-symbols-outlined shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>flag</span>
                    <span>Accept Quest <span className="hidden sm:inline">- Reserve This Weekend</span></span>
                  </button>
                  <button 
                    onClick={handleReject}
                    className="px-4 sm:px-6 py-4 rounded-xl bg-surface-container-highest text-on-surface font-label-lg font-semibold hover:bg-surface-bright transition-all shadow-md flex items-center justify-center gap-2 shrink-0"
                  >
                    <span className="material-symbols-outlined text-lg shrink-0">redo</span>
                    <span>Skip</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
