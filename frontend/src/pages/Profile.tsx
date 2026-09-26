import React, { useEffect, useState } from 'react';
import { getExplorationState, getDNA, getCategoryProfiles } from '../api/profile';
import { cn } from '../components/Layout';

export const Profile = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [state, setState] = useState<any>(null);
  const [dna, setDna] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const [sData, dData, cData] = await Promise.all([
        getExplorationState(),
        getDNA(),
        getCategoryProfiles()
      ]);
      setState(sData);
      setDna(dData);
      setCategories(cData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-text-muted gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-spin text-text-primary">fingerprint</span>
        <p className="font-label-md uppercase tracking-widest">Accessing Cartography...</p>
      </div>
    );
  }

  if (error || !state) {
    return (
      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-32 text-center flex flex-col items-center">
        <div className="w-16 h-16 bg-error-container text-on-error-container rounded-2xl flex items-center justify-center mb-4">
          <span className="material-symbols-outlined text-3xl">error</span>
        </div>
        <p className="text-text-primary text-xl max-w-md">{error}</p>
        <button onClick={fetchProfile} className="mt-6 px-6 py-3 bg-primary text-on-primary rounded-lg font-bold">Try Again</button>
      </div>
    );
  }

  const topDna = dna.filter(d => d.sample_count >= 1).sort((a, b) => b.affinity_value - a.affinity_value);

  return (
    <div className="flex flex-col w-full relative">
      <div className="bg-surface-card border-b border-border-subtle pt-space-xl pb-10 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none opacity-[0.03]">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern height="60" id="dots" patternUnits="userSpaceOnUse" width="60">
                <circle cx="2" cy="2" fill="currentColor" r="2"></circle>
              </pattern>
            </defs>
            <rect fill="url(#dots)" height="100%" width="100%"></rect>
          </svg>
        </div>
        
        <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin relative z-10 flex flex-col gap-space-sm">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-subtle text-text-primary font-label-sm text-label-sm uppercase tracking-widest self-start shadow-sm">
            <span className="material-symbols-outlined text-[14px]">fingerprint</span>
            Discovery Profile
          </span>
          <h1 className="font-headline-lg text-headline-lg md:text-display tracking-tight text-text-primary mt-2">
            Cartography Engine
          </h1>
          <p className="font-body-lg text-body-lg text-text-muted max-w-2xl">
            Mapping your latent interests through direct empirical experience. The algorithm understands what you enjoy before you do.
          </p>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-space-xl w-full flex flex-col gap-space-xl">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-space-md">
          <div className="bg-surface-card rounded-xl p-6 shadow-sm border border-border-subtle flex flex-col gap-2 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <span className="material-symbols-outlined text-[48px]">flag</span>
            </div>
            <span className="font-label-md uppercase tracking-wider text-text-muted">Missions Cleared</span>
            <span className="font-display text-display-mobile text-text-primary leading-none mt-1">{state.total_completed}</span>
          </div>
          <div className="bg-surface-card rounded-xl p-6 shadow-sm border border-border-subtle flex flex-col gap-2 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <span className="material-symbols-outlined text-[48px]">explore</span>
            </div>
            <span className="font-label-md uppercase tracking-wider text-text-muted">Families Explored</span>
            <span className="font-display text-display-mobile text-text-primary leading-none mt-1">{state.explored_families_count}</span>
          </div>
          <div className="bg-surface-card rounded-xl p-6 shadow-sm border border-border-subtle flex flex-col gap-2 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity text-error">
              <span className="material-symbols-outlined text-[48px]">close</span>
            </div>
            <span className="font-label-md uppercase tracking-wider text-text-muted">Missions Aborted</span>
            <span className="font-display text-display-mobile text-text-primary leading-none mt-1">{state.total_abandoned}</span>
          </div>
          <div className="bg-surface-subtle border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col justify-center items-center gap-2 text-center">
            <span className="font-label-md uppercase tracking-wider text-text-muted">Exploration Mode</span>
            <span className={cn("font-headline-sm uppercase tracking-widest", state.is_locked_in ? "text-error" : "text-text-primary")}>
              {state.is_locked_in ? "LOCKED-IN" : "NOVELTY PRIME"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-lg items-start">
          <section className="flex flex-col gap-space-md">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-secondary text-[24px]">biotech</span>
              <h2 className="font-headline-md text-text-primary tracking-tight">Extracted Skill DNA</h2>
            </div>
            {topDna.length > 0 ? (
              <div className="flex flex-col gap-3">
                {topDna.map(d => (
                  <div key={d.characteristic_slug} className="bg-surface-card rounded-xl p-5 flex items-center justify-between shadow-sm border border-border-subtle group hover:border-secondary transition-colors">
                    <div className="flex flex-col">
                      <span className="font-headline-sm text-text-primary capitalize">{d.characteristic_slug.replace(/_/g, ' ')}</span>
                      <span className="font-label-sm text-text-muted uppercase tracking-wider mt-1">
                        Based on {d.sample_count} experiences
                      </span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-display text-[24px] text-secondary">{(d.affinity_value * 10).toFixed(1)}</span>
                      <span className="font-label-sm text-text-muted uppercase tracking-wider">Affinity</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-surface-card rounded-xl p-10 text-center flex flex-col items-center border border-border-subtle border-dashed shadow-sm">
                <span className="material-symbols-outlined text-[48px] text-text-muted mb-3 opacity-50">science</span>
                <p className="font-body-md text-text-muted">Insufficient telemetry. Complete missions to reveal latent patterns.</p>
              </div>
            )}
          </section>

          <section className="flex flex-col gap-space-md">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-text-primary text-[24px]">battery_charging_full</span>
              <h2 className="font-headline-md text-text-primary tracking-tight">Category Fatigue Index</h2>
            </div>
            {categories.length > 0 ? (
              <div className="bg-surface-card rounded-xl p-space-lg shadow-sm border border-border-subtle flex flex-col gap-6">
                <p className="font-body-sm text-text-muted leading-relaxed">
                  High fatigue triggers the anti-bubble algorithm to forcibly pivot your vector toward uncharted territory.
                </p>
                <div className="flex flex-col gap-5">
                  {categories.map(c => (
                    <div key={c.category_id} className="flex flex-col gap-2">
                      <div className="flex justify-between font-label-md uppercase tracking-wider">
                        <span className="text-text-primary">{c.category_name || 'Unknown'}</span>
                        <span className={cn(c.fatigue_level > 0.7 ? "text-error" : "text-text-muted")}>
                          {Math.round(c.fatigue_level * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-surface-subtle rounded-full h-1.5 overflow-hidden border border-border-subtle">
                        <div 
                          className={cn("h-full rounded-full transition-all", c.fatigue_level > 0.7 ? "bg-error" : "bg-text-primary")}
                          style={{ width: `${c.fatigue_level * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-surface-card rounded-xl p-10 text-center flex flex-col items-center border border-border-subtle border-dashed shadow-sm">
                <span className="material-symbols-outlined text-[48px] text-text-muted mb-3 opacity-50">timeline</span>
                <p className="font-body-md text-text-muted">No category exposure logged yet.</p>
              </div>
            )}
          </section>
        </div>

        {state.unexplored_categories.length > 0 && (
          <section className="flex flex-col gap-space-md mt-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-text-muted text-[24px]">map</span>
              <h2 className="font-headline-md text-text-primary tracking-tight">Uncharted Horizons</h2>
            </div>
            <div className="flex flex-wrap gap-3 p-6 rounded-xl bg-surface-subtle border border-border-subtle">
              {state.unexplored_categories.map((c: string) => (
                <span key={c} className="px-4 py-2 rounded-lg bg-surface-card text-text-primary font-label-md uppercase tracking-widest shadow-sm border border-border-subtle">
                  {c.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};
