import React, { useEffect, useState } from 'react';
import { getMixCandidates } from '../api/mix';

export const Mix = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mixCandidates, setMixCandidates] = useState<any[]>([]);

  const fetchMix = async () => {
    try {
      setLoading(true);
      const mixes = await getMixCandidates();
      setMixCandidates(mixes);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('MIX protocol is locked. Complete more foundational quests to unlock this feature.');
      } else {
        setError(err.response?.data?.detail || 'Failed to load MIX candidates.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMix();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-on-surface-variant gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-spin text-secondary">graphic_eq</span>
        <p className="font-label-md uppercase tracking-widest">Synthesizing MIX candidates...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-32 text-center flex flex-col items-center">
        <div className="w-16 h-16 bg-surface-subtle rounded-2xl flex items-center justify-center mb-4 text-text-muted">
          <span className="material-symbols-outlined text-3xl">lock</span>
        </div>
        <p className="text-text-primary text-xl max-w-md">{error}</p>
        <button onClick={fetchMix} className="mt-6 px-6 py-3 bg-primary text-on-primary rounded-lg font-bold">Retry</button>
      </div>
    );
  }

  const primaryCandidate = mixCandidates.length > 0 ? mixCandidates[0] : null;
  const otherCandidates = mixCandidates.slice(1);

  return (
    <div className="flex flex-col w-full relative">
      <div className="bg-surface-card border-b border-border-subtle pt-space-xl pb-10 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none opacity-5">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern height="40" id="hex" patternUnits="userSpaceOnUse" width="40">
                <path d="M20 0 L40 10 L40 30 L20 40 L0 30 L0 10 Z" fill="none" stroke="currentColor" strokeWidth="1"></path>
              </pattern>
            </defs>
            <rect fill="url(#hex)" height="100%" width="100%"></rect>
          </svg>
        </div>
        
        <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin relative z-10 flex flex-col items-center text-center gap-space-sm">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-fixed/20 text-secondary font-label-sm text-label-sm uppercase tracking-widest shadow-sm">
            <span className="material-symbols-outlined text-[14px]">graphic_eq</span>
            Laboratory Mode
          </span>
          <h1 className="font-headline-lg text-headline-lg md:text-display tracking-tight text-text-primary mt-2">
            The MIX Engine
          </h1>
          <p className="font-body-lg text-body-lg text-text-muted max-w-2xl">
            You have accrued enough latent DNA to generate cross-disciplinary bridges. 
            Algorithmic synthesis of previously learned skills to generate entirely novel territories.
          </p>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-space-xl w-full">
        {mixCandidates.length === 0 ? (
          <div className="bg-surface-card rounded-xl p-10 text-center flex flex-col items-center border border-border-subtle border-dashed">
            <span className="material-symbols-outlined text-[48px] text-border-subtle mb-3">science</span>
            <p className="font-body-md text-text-muted">No viable MIX combinations discovered yet. Expand your field horizons.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-10">
            {/* Primary Synthesis Candidate */}
            <section className="relative">
              <div className="flex flex-col items-center mb-8 relative z-10">
                <div className="flex flex-col md:flex-row items-center gap-4 md:gap-8 w-full max-w-4xl mx-auto">
                  
                  <div className="flex-1 bg-surface-card border border-border-subtle rounded-xl p-5 shadow-sm text-center w-full relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-surface-subtle px-2 py-0.5 rounded text-text-muted font-label-sm text-label-sm uppercase">Source A</span>
                    <span className="material-symbols-outlined text-text-muted mb-2 text-[24px]">category</span>
                    <h3 className="font-headline-sm text-headline-sm text-text-primary">{primaryCandidate.skill_1_name}</h3>
                    <p className="font-body-sm text-body-sm text-text-muted mt-1 truncate">Prior Exploration Vector</p>
                  </div>
                  
                  <div className="shrink-0 flex items-center justify-center relative">
                    <div className="w-12 h-12 rounded-full bg-secondary text-on-secondary flex items-center justify-center shadow-lg relative z-10">
                      <span className="material-symbols-outlined">add</span>
                    </div>
                  </div>
                  
                  <div className="flex-1 bg-surface-card border border-border-subtle rounded-xl p-5 shadow-sm text-center w-full relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-surface-subtle px-2 py-0.5 rounded text-text-muted font-label-sm text-label-sm uppercase">Source B</span>
                    <span className="material-symbols-outlined text-text-muted mb-2 text-[24px]">category</span>
                    <h3 className="font-headline-sm text-headline-sm text-text-primary">{primaryCandidate.skill_2_name}</h3>
                    <p className="font-body-sm text-body-sm text-text-muted mt-1 truncate">Prior Exploration Vector</p>
                  </div>
                </div>
              </div>

              <div className="bg-surface-card rounded-xl shadow-lg border border-border-subtle overflow-hidden">
                <div className="h-1.5 w-full bg-gradient-to-r from-surface-subtle via-secondary to-surface-subtle"></div>
                <div className="flex flex-col lg:flex-row">
                  <div className="p-space-lg lg:p-space-xl flex-1 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-border-subtle bg-surface-canvas relative overflow-hidden">
                     <span className="material-symbols-outlined text-[120px] text-surface-subtle absolute -right-10 -bottom-10 rotate-12">science</span>
                     <div className="relative z-10">
                        <span className="inline-flex px-2 py-1 bg-secondary-fixed text-on-secondary-fixed font-label-sm text-label-sm uppercase tracking-wider rounded mb-4">
                            Primary Latent Match ({primaryCandidate.mix_category.replace(/_/g, ' ')})
                        </span>
                        <h2 className="font-display text-display-mobile md:text-display text-text-primary tracking-tight leading-tight mb-4">
                            {primaryCandidate.concept}
                        </h2>
                     </div>
                  </div>
                  <div className="p-space-lg lg:p-space-xl flex-1 flex flex-col justify-between bg-surface-card">
                     <div>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="material-symbols-outlined text-secondary">token</span>
                            <h3 className="font-headline-md text-headline-md text-text-primary">Synthesis Parameters</h3>
                        </div>
                        <div className="bg-surface-subtle/70 rounded-lg p-4 mb-6">
                            <div className="flex items-center gap-1.5 font-label-md text-label-md text-text-primary uppercase mb-1">
                                <span className="material-symbols-outlined text-[16px] text-secondary">psychology</span>
                                Why this connection makes sense
                            </div>
                            <p className="font-body-md text-body-md text-on-surface-variant">
                                {primaryCandidate.explanation}
                            </p>
                        </div>
                     </div>
                     <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
                        <button 
                            disabled
                            className="flex-1 px-8 py-3.5 bg-surface-container-highest text-text-muted font-label-lg text-label-lg rounded-lg flex items-center justify-center gap-2 opacity-50 cursor-not-allowed"
                            title="MIX activation is not supported by the backend yet."
                        >
                            <span>Launch MIX Quest (Coming Soon)</span>
                            <span className="material-symbols-outlined text-[18px]">lock</span>
                        </button>
                     </div>
                  </div>
                </div>
              </div>
            </section>

            {otherCandidates.length > 0 && (
              <section className="mt-14 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase text-text-muted tracking-wider">Latent Synthesis Pool</span>
                    <h2 className="font-headline-md text-headline-md text-text-primary mt-1">Discovered Potential Connections</h2>
                  </div>
                  <p className="font-body-sm text-body-sm text-text-muted">{otherCandidates.length} candidates ready for algorithmic ignition.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {otherCandidates.map((c: any) => (
                    <article key={c.id} className="bg-surface-card rounded-xl p-6 shadow-sm border border-border-subtle flex flex-col justify-between group">
                      <div>
                        <div className="flex items-center justify-between mb-4">
                            <span className="px-2.5 py-1 rounded bg-surface-subtle text-text-muted font-label-sm text-label-sm uppercase">{c.mix_category.replace(/_/g, ' ')}</span>
                        </div>
                        <div className="flex items-center gap-3 bg-surface-subtle p-3 rounded-lg mb-4">
                            <div className="flex-1 min-w-0">
                                <span className="font-label-sm text-label-sm text-text-muted uppercase">Past Skill A</span>
                                <p className="font-headline-sm text-headline-sm text-text-primary text-[15px] truncate">{c.skill_1_name}</p>
                            </div>
                            <span className="font-display text-text-muted text-lg">+</span>
                            <div className="flex-1 min-w-0">
                                <span className="font-label-sm text-label-sm text-text-muted uppercase">Past Skill B</span>
                                <p className="font-headline-sm text-headline-sm text-text-primary text-[15px] truncate">{c.skill_2_name}</p>
                            </div>
                        </div>
                        <h3 className="font-headline-sm text-headline-sm text-text-primary">
                            {c.concept}
                        </h3>
                        <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">
                            {c.explanation}
                        </p>
                      </div>
                      <div className="pt-6 mt-6 flex items-center justify-between">
                        <button disabled className="text-text-muted font-label-md text-label-md flex items-center gap-1 cursor-not-allowed">
                            <span className="material-symbols-outlined text-[16px]">lock</span>
                            <span>Coming Soon</span>
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
