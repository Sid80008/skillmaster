import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentQuest, getChallenge, startQuest, completeQuest, abandonQuest, QuestAttempt, Challenge } from '../api/quests';

export const QuestDetail = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState<QuestAttempt | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [sessionPaused, setSessionPaused] = useState(false);

  const fetchState = async () => {
    try {
      setLoading(true);
      const activeQuest = await getCurrentQuest();
      setAttempt(activeQuest);

      if (activeQuest && (activeQuest.status === 'active' || activeQuest.status === 'pending')) {
        const chal = await getChallenge(activeQuest.id);
        setChallenge(chal);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load quest.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  // Timer logic for active quest simulation
  useEffect(() => {
    let interval: any;
    if (attempt?.status === 'active' && !sessionPaused) {
      interval = setInterval(() => {
        setElapsedSec(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [attempt?.status, sessionPaused]);

  const handleStart = async () => {
    if (!attempt) return;
    try {
      await startQuest(attempt.id);
      fetchState();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start.');
    }
  };

  const handleComplete = async () => {
    if (!attempt) return;
    try {
      await completeQuest(attempt.id);
      navigate('/feedback', { state: { attemptId: attempt.id } });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete.');
    }
  };

  const handleAbandon = async () => {
    if (!attempt) return;
    if (!window.confirm('Discard current quest progress? (No skill penalties applied)')) return;
    try {
      await abandonQuest(attempt.id, 'Decided to abandon');
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to abandon.');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-on-surface-variant gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-spin text-tertiary">hourglass_empty</span>
        <p className="font-label-md uppercase tracking-widest">Loading Manifest...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <p className="text-on-surface text-xl">{error}</p>
        <button onClick={fetchState} className="mt-6 px-6 py-2 bg-primary-container text-on-primary-container rounded-lg font-bold">Try Again</button>
      </div>
    );
  }

  if (!attempt || !challenge) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center flex flex-col items-center">
        <div className="w-16 h-16 bg-surface-container-high rounded-2xl flex items-center justify-center mb-4 text-on-surface-variant">
          <span className="material-symbols-outlined text-3xl">explore_off</span>
        </div>
        <h2 className="text-headline-md font-headline-md text-on-surface">No active quest</h2>
        <p className="text-on-surface-variant font-body-lg mt-2">You don't have a weekend quest yet.</p>
        <button 
          onClick={() => navigate('/')}
          className="mt-6 bg-primary-container text-on-primary font-label-lg px-6 py-3 rounded-xl hover:brightness-110"
        >
          Find a Quest
        </button>
      </div>
    );
  }

  const formatTime = (sec: number) => {
    const h = Math.floor(sec / 3600).toString().padStart(2, '0');
    const m = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  // ACTIVE QUEST RENDER
  if (attempt.status === 'active') {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-8 w-full flex flex-col gap-6">
        <div className="w-full bg-surface-container-low rounded-xl p-5 shadow-lg relative overflow-hidden">
          <div className="absolute -right-16 -top-16 w-56 h-56 bg-primary-container/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="relative flex items-center justify-center w-12 h-12 rounded-lg bg-surface-container-high text-primary-container shrink-0">
                <span className="material-symbols-outlined text-headline-sm" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-label-sm uppercase tracking-widest text-tertiary">Active Weekend Quest</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-surface-bright"></span>
                  <span className="font-label-sm uppercase tracking-widest text-on-surface-variant">In Progress</span>
                </div>
                <h1 className="font-headline-md text-on-surface tracking-tight">{challenge.title}</h1>
              </div>
            </div>
            
            <div className="flex items-center gap-4 bg-surface-container px-4 py-2.5 rounded-lg shrink-0 self-start md:self-auto">
              <div className="flex flex-col">
                <span className="font-label-sm uppercase text-on-surface-variant tracking-wider">Elapsed Time</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-headline-sm text-on-surface tracking-tight font-mono">{formatTime(elapsedSec)}</span>
                  <span className="font-label-md text-on-surface-variant">/ ~{Math.floor(challenge.estimated_duration_minutes/60)}h {challenge.estimated_duration_minutes%60}m</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="w-full bg-surface-container rounded-xl p-6 md:p-8 shadow-xl flex flex-col gap-6 relative">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded bg-primary-container/20 text-primary-container font-label-sm uppercase tracking-widest font-bold">Priority Objective</span>
                </div>
              </div>
              
              <div className="flex flex-col gap-2">
                <h2 className="font-headline-lg text-on-surface tracking-tight">{challenge.objective}</h2>
                <p className="font-body-lg text-on-surface-variant mt-1 leading-relaxed">
                  {challenge.why_this_matters}
                </p>
              </div>

              <div className="w-full bg-surface-container-lowest rounded-xl p-6 md:p-8 flex flex-col gap-4 shadow-inner">
                 <h3 className="font-headline-sm text-on-surface tracking-tight">Execution Directive (DO)</h3>
                 <p className="font-body-md text-on-surface-variant whitespace-pre-wrap leading-relaxed">{challenge.do_content}</p>
              </div>

              <div className="w-full bg-surface-container-low rounded-lg p-4 flex items-start gap-3.5 text-on-surface">
                <span className="material-symbols-outlined text-tertiary text-headline-sm shrink-0 mt-0.5">lightbulb</span>
                <div className="flex flex-col gap-0.5">
                  <span className="font-label-md font-bold text-tertiary uppercase tracking-wider">Field Guidance (LEARN)</span>
                  <p className="font-body-md text-on-surface-variant whitespace-pre-wrap">{challenge.learn_content}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-4 flex flex-col gap-6">
            <div className="w-full bg-surface-container rounded-xl shadow-md p-5 flex flex-col gap-4">
              <div className="flex items-center gap-2.5">
                <span className="material-symbols-outlined text-secondary">assignment_turned_in</span>
                <h3 className="font-headline-sm text-on-surface">Verification Checklist</h3>
              </div>
              <div className="flex flex-col gap-2.5">
                <label className="flex items-center gap-3.5 p-3.5 rounded-lg bg-surface-container-low hover:bg-surface-container-high cursor-pointer transition-colors select-none">
                  <input type="checkbox" className="w-5 h-5 rounded accent-primary-container cursor-pointer" />
                  <span className="font-body-md text-on-surface flex-1">{challenge.finish_criteria}</span>
                </label>
              </div>
            </div>

            {challenge.stretch_goal && (
               <div className="w-full bg-surface-container rounded-xl shadow-md overflow-hidden">
                <div className="p-5 flex flex-col gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-secondary">science</span>
                    <span className="font-headline-sm text-on-surface">Optional Stretch Goals</span>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-container-low flex flex-col gap-2">
                    <span className="font-label-lg font-bold text-on-surface">Stretch Directive</span>
                    <p className="font-body-sm text-on-surface-variant">{challenge.stretch_goal}</p>
                  </div>
                </div>
               </div>
            )}
          </div>
        </div>

        <div className="sticky bottom-4 z-40 w-full mt-4 bg-surface-container-lowest/95 backdrop-blur-xl p-4 md:p-5 rounded-xl shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4 border border-surface-container">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button 
              onClick={() => setSessionPaused(!sessionPaused)}
              className="flex-1 sm:flex-none px-6 py-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface active:scale-95 transition-all font-label-lg flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-headline-sm">{sessionPaused ? 'play_circle' : 'pause_circle'}</span>
              <span>{sessionPaused ? 'Resume Session' : 'Pause Session'}</span>
            </button>
            <button 
              onClick={handleAbandon}
              className="px-4 py-4 rounded-xl text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors font-label-md flex items-center justify-center gap-1.5"
            >
              <span className="material-symbols-outlined text-label-lg">close</span>
              <span className="hidden md:inline">Abandon Quest (No Penalty)</span>
            </button>
          </div>
          <div className="w-full sm:w-auto flex items-center justify-end">
            <button 
              onClick={handleComplete}
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-primary-container hover:brightness-110 active:scale-95 transition-all text-on-primary-container font-headline-sm tracking-tight flex items-center justify-center gap-3 shadow-lg shadow-primary-container/25"
            >
              <span className="material-symbols-outlined text-headline-sm" style={{ fontVariationSettings: "'FILL' 1" }}>task_alt</span>
              <span>Complete Quest & Log Field Exp</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // PENDING RENDER
  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-8 w-full">
      <div className="relative w-full flex flex-col gap-10 pb-28">
        <div className="flex flex-col gap-6">
          <nav className="flex items-center gap-2 text-on-surface-variant">
            <button onClick={() => navigate('/')} className="flex items-center gap-1.5 font-label-md hover:text-primary transition-colors">
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>EXPLORE QUEUE</span>
            </button>
            <span className="text-on-surface-variant/40 font-mono text-xs">/</span>
            <span className="font-label-md uppercase tracking-wider text-tertiary">MANIFEST</span>
          </nav>
          
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="flex flex-col gap-3 max-w-4xl">
              <div className="flex flex-wrap items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-secondary-container/30 text-secondary font-label-sm uppercase tracking-wider">
                  FIELD DECK
                </span>
                <div className="flex items-center gap-1 text-primary-container">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container"></span>
                  <span className="font-label-sm uppercase tracking-widest">Locked In & Ready</span>
                </div>
              </div>
              <h1 className="font-display-hero text-on-surface tracking-tight leading-none uppercase">
                {challenge.title}
              </h1>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 rounded-xl bg-surface-container shadow-md">
            <div className="flex flex-col p-3 rounded-lg bg-surface-container-low">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-sm uppercase tracking-wider">Estimated Span</span>
                <span className="material-symbols-outlined text-[16px] text-tertiary">timer</span>
              </div>
              <span className="font-headline-sm text-on-surface mt-1">{challenge.estimated_duration_minutes} Minutes</span>
            </div>
            
            <div className="flex flex-col p-3 rounded-lg bg-surface-container-low">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-sm uppercase tracking-wider">Logistics</span>
                <span className="material-symbols-outlined text-[16px] text-primary-container">handyman</span>
              </div>
              <span className="font-headline-sm text-on-surface mt-1 opacity-50 text-sm">Not provided by API</span>
            </div>

            <div className="flex flex-col p-3 rounded-lg bg-surface-container-low">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-sm uppercase tracking-wider">Difficulty Level</span>
                <span className="material-symbols-outlined text-[16px] text-secondary">explore</span>
              </div>
              <span className="font-headline-sm text-on-surface mt-1">{challenge.difficulty_level}/10</span>
            </div>

            <div className="flex flex-col p-3 rounded-lg bg-surface-container-low">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-sm uppercase tracking-wider">Environment</span>
                <span className="material-symbols-outlined text-[16px] text-tertiary">wb_sunny</span>
              </div>
              <span className="font-headline-sm text-on-surface mt-1 opacity-50 text-sm">Not provided by API</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          <div className="lg:col-span-8 flex flex-col justify-between p-8 rounded-xl bg-surface-container relative overflow-hidden shadow-lg">
            <div className="relative z-10 flex flex-col gap-4">
              <div className="flex items-center gap-2 text-primary-container">
                <span className="material-symbols-outlined text-[20px]">target</span>
                <span className="font-label-sm uppercase tracking-widest font-bold">Primary Target Vector</span>
              </div>
              <h2 className="font-headline-lg text-on-surface max-w-2xl leading-tight">
                {challenge.objective}
              </h2>
              <p className="font-body-md text-on-surface-variant max-w-xl">
                {challenge.why_this_matters}
              </p>
            </div>
            <div className="absolute -right-12 -bottom-12 w-64 h-64 rounded-full bg-primary-container/10 blur-3xl pointer-events-none"></div>
          </div>
        </div>
        
        <div className="flex flex-col gap-12 mt-4">
          <section className="flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-secondary-container text-on-secondary-container flex items-center justify-center font-headline-sm">1</span>
                <div>
                  <span className="font-label-sm uppercase tracking-widest text-secondary">Theoretical Foundations</span>
                  <h3 className="font-headline-md text-on-surface">Stage 1: LEARN</h3>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-xl bg-surface-container">
               <p className="font-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">{challenge.learn_content}</p>
            </div>
          </section>
          
          <section className="flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-primary-container text-on-primary-container flex items-center justify-center font-headline-sm">2</span>
                <div>
                  <span className="font-label-sm uppercase tracking-widest text-primary-container">Hands-On Protocol</span>
                  <h3 className="font-headline-md text-on-surface">Stage 2: DO</h3>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-xl bg-surface-container">
               <p className="font-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">{challenge.do_content}</p>
            </div>
          </section>

          <section className="flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-tertiary-container text-on-tertiary-container flex items-center justify-center font-headline-sm">3</span>
                <div>
                  <span className="font-label-sm uppercase tracking-widest text-tertiary">Verification Spec</span>
                  <h3 className="font-headline-md text-on-surface">Stage 3: Finish Criteria</h3>
                </div>
              </div>
            </div>
            <div className="p-6 rounded-xl bg-surface-container">
               <p className="font-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">{challenge.finish_criteria}</p>
            </div>
          </section>

          {challenge.stretch_goal && (
             <section className="flex flex-col gap-6">
              <div className="flex items-center justify-between pb-3 border-b border-surface-container">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-surface-container-highest text-secondary flex items-center justify-center font-headline-sm">4</span>
                  <div>
                    <span className="font-label-sm uppercase tracking-widest text-secondary">Alchemical Variations</span>
                    <h3 className="font-headline-md text-on-surface">Stage 4: Stretch Goals</h3>
                  </div>
                </div>
              </div>
              <div className="p-6 rounded-xl bg-surface-container">
                 <p className="font-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">{challenge.stretch_goal}</p>
              </div>
            </section>
          )}
        </div>
      </div>

      <div className="fixed bottom-6 left-0 right-0 z-40 px-6 pointer-events-none">
        <div className="max-w-4xl mx-auto rounded-2xl bg-surface-container-highest/95 backdrop-blur-xl p-3 sm:p-4 shadow-2xl pointer-events-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center text-primary-container shrink-0">
              <span className="material-symbols-outlined text-[24px]">wb_twilight</span>
            </div>
            <div className="flex flex-col text-center md:text-left">
              <span className="font-label-md text-on-surface font-bold">Quest Window Open</span>
              <span className="font-body-sm text-on-surface-variant hidden sm:inline">Review manifest. Press start when ready.</span>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 shrink-0 w-full md:w-auto">
            <button 
              onClick={handleAbandon}
              className="hidden md:flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-surface-container hover:bg-surface-bright text-on-surface font-label-md transition-all active:scale-95"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
              <span>Abandon</span>
            </button>
            <button 
              onClick={handleStart}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary-container font-headline-sm tracking-wide transition-all active:scale-95 shadow-lg font-bold"
            >
              <span className="material-symbols-outlined text-[20px]">explore</span>
              <span>Start Quest Now</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
