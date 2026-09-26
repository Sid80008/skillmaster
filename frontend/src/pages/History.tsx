import React, { useEffect, useState } from 'react';
import { getQuestHistory, QuestAttempt } from '../api/quests';
import { useNavigate } from 'react-router-dom';
import { cn } from '../components/Layout';

export const History = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QuestAttempt[]>([]);
  const [viewMode, setViewMode] = useState<'timeline' | 'matrix'>('timeline');
  const navigate = useNavigate();

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await getQuestHistory();
      setHistory(data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full text-text-muted gap-4 py-32">
        <span className="material-symbols-outlined text-4xl animate-spin text-text-primary">history</span>
        <p className="font-label-md uppercase tracking-widest">Accessing Logs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <p className="text-text-primary text-xl">{error}</p>
        <button onClick={fetchHistory} className="mt-6 px-6 py-2 bg-text-primary text-on-primary rounded-lg font-bold">Try Again</button>
      </div>
    );
  }

  const totalExpeditions = history.length;
  const categories = new Set(history.map(h => h.category_name || 'Unknown')).size;
  const completedCount = history.filter(h => h.status === 'completed').length;
  const noveltyRatio = totalExpeditions > 0 ? Math.round((completedCount / totalExpeditions) * 100) : 0;

  return (
    <div className="flex flex-col w-full">
      <div className="bg-surface-card border-b border-border-subtle py-space-xl">
        <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin">
          <div className="flex flex-col gap-space-sm">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-subtle text-text-primary font-label-sm text-label-sm uppercase tracking-widest self-start shadow-sm">
              <span className="material-symbols-outlined text-[14px]">history</span>
              Atelier Logs
            </span>
            <h1 className="font-headline-lg text-headline-lg tracking-tight text-text-primary mt-2">
              Exploration History
            </h1>
            <p className="font-body-lg text-body-lg text-text-muted max-w-2xl">
              A chronological ledger of every territory ventured, skill acquired, and artifact synthesized. 
              The foundation of your creative architecture.
            </p>
          </div>
          <div className="mt-space-lg grid grid-cols-2 md:grid-cols-4 gap-space-sm">
            <div className="bg-surface-subtle p-space-md rounded-lg flex flex-col gap-1">
              <span className="font-label-md text-label-md text-text-muted">Total Expeditions</span>
              <span className="font-headline-md text-headline-md text-text-primary">{totalExpeditions}</span>
            </div>
            <div className="bg-surface-subtle p-space-md rounded-lg flex flex-col gap-1">
              <span className="font-label-md text-label-md text-text-muted">Territories Traversed</span>
              <span className="font-headline-md text-headline-md text-text-primary">{categories}</span>
            </div>
            <div className="bg-surface-subtle p-space-md rounded-lg flex flex-col gap-1">
              <span className="font-label-md text-label-md text-text-muted">Dominant Horizon</span>
              <span className="font-headline-md text-headline-md text-text-primary">Various</span>
            </div>
            <div className="bg-surface-subtle p-space-md rounded-lg flex flex-col gap-1">
              <span className="font-label-md text-label-md text-text-muted">Novelty Prime Ratio</span>
              <span className="font-headline-md text-headline-md text-text-primary">{noveltyRatio}%</span>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-space-xl w-full">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md mb-space-lg">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 sm:pb-0 hide-scrollbar mask-edges">
            <button className="horizon-filter-pill px-4 py-1.5 rounded-full bg-text-primary text-on-primary font-label-md text-label-md whitespace-nowrap shadow-sm transition-colors" data-filter="all">All Horizons</button>
          </div>
          <div className="flex items-center gap-1 bg-surface-subtle p-1 rounded-lg shrink-0">
            <button onClick={() => setViewMode('timeline')} className={cn("px-3 py-1.5 rounded font-label-md text-label-md flex items-center gap-1.5 transition-colors", viewMode === 'timeline' ? "bg-surface-card text-text-primary shadow-sm" : "text-text-muted hover:text-text-primary")}>
              <span className="material-symbols-outlined text-[18px]">calendar_view_day</span>
              Stream
            </button>
            <button onClick={() => setViewMode('matrix')} className={cn("px-3 py-1.5 rounded font-label-md text-label-md flex items-center gap-1.5 transition-colors", viewMode === 'matrix' ? "bg-surface-card text-text-primary shadow-sm" : "text-text-muted hover:text-text-primary")}>
              <span className="material-symbols-outlined text-[18px]">grid_view</span>
              Matrix
            </button>
          </div>
        </div>
        
        {viewMode === 'timeline' ? (
          <div id="timelineContainer" className="flex flex-col gap-space-lg relative before:content-[''] before:absolute before:left-[15px] md:before:left-[120px] before:top-2 before:bottom-2 before:w-px before:bg-border-subtle before:z-0">
            {history.length === 0 ? (
                <div className="bg-surface-card rounded-xl p-10 text-center flex flex-col items-center border border-border-subtle border-dashed">
                  <p className="font-body-md text-text-muted">No history recorded. Accept a quest to start your journey.</p>
                </div>
            ) : (
                history.map((attempt, index) => {
                  const date = new Date(attempt.started_at || attempt.created_at).toLocaleDateString('en-US', {
                    month: 'short', day: 'numeric', year: 'numeric'
                  });
                  return (
                    <article key={attempt.id} className="relative z-10 flex flex-col md:flex-row gap-space-md md:gap-space-lg group">
                      <div className="flex items-center md:items-start gap-4 md:w-[120px] shrink-0 md:pt-4">
                        <div className="w-8 h-8 rounded-full bg-surface-card border-2 border-surface-subtle shadow-sm flex items-center justify-center relative z-10 shrink-0 group-hover:border-accent-spark transition-colors">
                          <span className={cn("w-2 h-2 rounded-full", attempt.status === 'completed' ? "bg-text-primary" : attempt.status === 'active' ? "bg-accent-spark animate-pulse" : "bg-text-muted")}></span>
                        </div>
                        <div className="font-label-sm text-label-sm text-text-muted uppercase tracking-wider">{date}</div>
                      </div>
                      <div onClick={() => navigate(`/quest/${attempt.id}`)} className="flex-1 bg-surface-card hover:bg-surface-subtle transition-colors rounded-xl p-space-lg shadow-sm border border-border-subtle cursor-pointer">
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-space-md">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-label-sm text-label-sm text-text-muted uppercase tracking-wider">{attempt.category_name || 'Unknown Category'}</span>
                              <span className="w-1 h-1 rounded-full bg-border-subtle"></span>
                              <span className="font-label-sm text-label-sm text-text-muted uppercase tracking-wider">{attempt.activity_family_name || 'Unknown Family'}</span>
                            </div>
                            <h3 className="font-headline-sm text-headline-sm text-text-primary tracking-tight">{attempt.skill_name || 'Unknown Skill'}</h3>
                            <p className="font-body-sm text-body-sm text-text-muted mt-2 max-w-2xl line-clamp-2">Attempt #{attempt.id.substring(0, 8)}</p>
                          </div>
                          <div className="shrink-0 flex flex-col items-start sm:items-end gap-2">
                            <span className={cn("px-2.5 py-1 rounded font-label-sm text-label-sm uppercase tracking-widest", attempt.status === 'completed' ? "bg-surface-subtle text-text-primary" : attempt.status === 'active' ? "bg-accent-spark/10 text-accent-spark" : "bg-surface-subtle text-text-muted")}>
                              {attempt.status === 'completed' ? 'Synthesized' : attempt.status === 'active' ? 'Active' : attempt.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </article>
                  );
                })
            )}
          </div>
        ) : (
          <div id="matrixContainer" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-md">
            {history.map(attempt => (
                <div key={attempt.id} onClick={() => navigate(`/quest/${attempt.id}`)} className="p-space-md rounded-lg bg-surface-subtle flex flex-col justify-between cursor-pointer hover:bg-surface-card hover:shadow-sm border border-transparent hover:border-border-subtle transition-all">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-label-md text-label-md uppercase font-semibold text-text-primary">{attempt.category_name || 'Unknown'}</span>
                      <span className={cn("font-label-sm text-label-sm px-2 py-0.5 rounded", attempt.status === 'completed' ? 'bg-surface-card text-text-primary' : 'bg-surface-card text-text-muted')}>{attempt.status}</span>
                    </div>
                    <p className="font-headline-sm text-text-primary">{attempt.skill_name || 'Unknown Skill'}</p>
                  </div>
                  <div className="mt-space-md pt-space-xs text-text-muted font-label-sm text-label-sm">{new Date(attempt.started_at || attempt.created_at).toLocaleDateString()}</div>
                </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
