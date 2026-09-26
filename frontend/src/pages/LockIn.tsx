import React, { useEffect, useState } from 'react';
import { getCurrentLockIn, activateLockIn, exitLockIn, LockInSession } from '../api/lockin';
import { cn } from '../components/Layout';

export const LockIn = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [session, setSession] = useState<LockInSession | null>(null);
  const [activating, setActivating] = useState(false);
  const [exiting, setExiting] = useState(false);

  const fetchSession = async () => {
    try {
      setLoading(true);
      const data = await getCurrentLockIn();
      setSession(data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setSession(null);
      } else {
        setError(err.response?.data?.detail || 'Failed to load LOCK-IN status.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, []);

  const handleExit = async () => {
    try {
      setExiting(true);
      await exitLockIn('User explicitly requested exit via Lock-In console.');
      await fetchSession();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to exit LOCK-IN.');
    } finally {
      setExiting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-text-muted gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-pulse text-error">lock</span>
        <p className="font-label-md uppercase tracking-widest">Verifying Protocol...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-32 text-center flex flex-col items-center">
        <div className="w-16 h-16 bg-error-container text-on-error-container rounded-2xl flex items-center justify-center mb-4">
          <span className="material-symbols-outlined text-3xl">error</span>
        </div>
        <p className="text-text-primary text-xl max-w-md">{error}</p>
        <button onClick={fetchSession} className="mt-6 px-6 py-3 bg-primary text-on-primary rounded-lg font-bold">Try Again</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full relative">
      <div className="bg-surface-card border-b border-border-subtle pt-space-xl pb-10 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none opacity-5">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern height="20" id="grid" patternUnits="userSpaceOnUse" width="20">
                <rect fill="none" height="20" stroke="currentColor" strokeWidth="1" width="20"></rect>
              </pattern>
            </defs>
            <rect fill="url(#grid)" height="100%" width="100%"></rect>
          </svg>
        </div>
        
        <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin relative z-10 flex flex-col items-center text-center gap-space-sm">
          <div className={cn(
            "inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-label-sm uppercase tracking-widest shadow-sm",
            session ? "bg-error/10 text-error border border-error/20" : "bg-surface-subtle text-text-muted border border-border-subtle"
          )}>
            <span className="material-symbols-outlined text-[16px]">
              {session ? 'lock' : 'lock_open'}
            </span>
            <span>{session ? 'ACTIVE PROTOCOL' : 'STANDBY MODE'}</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg md:text-display tracking-tight text-text-primary mt-2">
            LOCK-IN
          </h1>
          <p className="font-body-lg text-body-lg text-text-muted max-w-2xl">
            Override the exploration engine and commit to deep mastery of a single discipline. 
            Once activated, all novelty recommendations are suspended.
          </p>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-space-xl w-full flex justify-center">
        {session ? (
          <div className="w-full max-w-4xl bg-surface-card rounded-2xl p-space-lg md:p-space-xl shadow-lg border border-error/30 relative overflow-hidden flex flex-col gap-10">
            <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-error/5 blur-3xl pointer-events-none"></div>
            
            <div className="relative z-10 flex flex-col gap-2 items-center text-center">
              <span className="material-symbols-outlined text-[48px] text-error mb-2">vpn_key</span>
              <h2 className="font-display text-display-mobile md:text-display text-text-primary leading-none">Protocol Active</h2>
              <p className="font-body-lg text-text-muted max-w-lg mt-2">
                You are currently locked into mastering <strong className="text-text-primary">{session.skill_id}</strong>.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
              <div className="bg-surface-subtle p-6 rounded-xl border border-border-subtle flex flex-col items-center text-center">
                <span className="font-label-sm uppercase tracking-wider text-text-muted mb-2">Initiated</span>
                <span className="material-symbols-outlined text-text-muted mb-2">calendar_today</span>
                <p className="font-headline-sm text-text-primary">
                  {new Date(session.started_at).toLocaleDateString()}
                </p>
              </div>
              <div className="bg-surface-subtle p-6 rounded-xl border border-border-subtle flex flex-col items-center text-center">
                <span className="font-label-sm uppercase tracking-wider text-text-muted mb-2">Target Vector</span>
                <span className="material-symbols-outlined text-text-muted mb-2">my_location</span>
                <p className="font-mono text-sm text-text-primary overflow-hidden text-ellipsis w-full">
                  {session.skill_id}
                </p>
              </div>
              <div className="bg-surface-subtle p-6 rounded-xl border border-border-subtle flex flex-col items-center text-center opacity-70">
                <span className="font-label-sm uppercase tracking-wider text-text-muted mb-2">Progression</span>
                <span className="material-symbols-outlined text-text-muted mb-2">trending_up</span>
                <p className="font-headline-sm text-text-primary">Data Unmapped</p>
                <p className="font-label-sm text-text-muted mt-2">Endpoint pending</p>
              </div>
            </div>

            <div className="flex items-center justify-center mt-4 relative z-10">
              <button 
                onClick={handleExit}
                disabled={exiting}
                className="px-8 py-4 rounded-xl bg-surface-card border-2 border-error hover:bg-error text-error hover:text-on-error font-headline-sm font-bold shadow-sm transition-all flex items-center gap-3 disabled:opacity-50"
              >
                {exiting ? (
                  <span className="material-symbols-outlined animate-spin">refresh</span>
                ) : (
                  <span className="material-symbols-outlined">eject</span>
                )}
                <span>Disengage LOCK-IN</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="w-full max-w-3xl bg-surface-card rounded-2xl p-space-lg md:p-space-xl text-center flex flex-col items-center border border-border-subtle shadow-sm">
            <div className="w-20 h-20 bg-surface-subtle rounded-full flex items-center justify-center mb-6 border border-border-subtle">
              <span className="material-symbols-outlined text-[40px] text-text-primary">psychology</span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-text-primary mb-3">Ready for Mastery?</h2>
            <p className="font-body-lg text-text-muted max-w-lg mb-10">
              Enter the target skill ID below to commit to deep mastery and override the exploration engine. 
              This will suspend all novelty recommendations.
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-4 w-full max-w-lg">
              <input 
                type="text" 
                id="skillIdInput"
                placeholder="Enter Target Skill ID (UUID)"
                className="flex-1 px-5 py-4 rounded-xl bg-surface-subtle border border-border-subtle text-text-primary focus:outline-none focus:border-text-primary focus:ring-1 focus:ring-text-primary font-mono text-sm w-full transition-all"
              />
              <button 
                onClick={async () => {
                  const input = document.getElementById('skillIdInput') as HTMLInputElement;
                  if (!input.value.trim()) return alert('Skill ID required');
                  try {
                    setActivating(true);
                    await activateLockIn(input.value.trim());
                    await fetchSession();
                  } catch (err: any) {
                    alert(err.response?.data?.detail || 'Activation failed');
                  } finally {
                    setActivating(false);
                  }
                }}
                disabled={activating}
                className="px-8 py-4 rounded-xl bg-primary hover:bg-neutral-800 text-on-primary font-label-lg font-bold transition-colors flex items-center justify-center gap-2 w-full sm:w-auto shadow-md disabled:opacity-50"
              >
                {activating ? (
                  <span className="material-symbols-outlined animate-spin">refresh</span>
                ) : (
                  <span className="material-symbols-outlined text-[20px]">key</span>
                )}
                <span>Activate</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
