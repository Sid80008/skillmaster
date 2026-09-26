import React, { useState } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { submitFeedback, RatingPayload } from '../api/quests';
import { cn } from '../components/Layout';

const ScaleButton = ({ value, label, selected, onClick }: { value: number, label: string, selected: boolean, onClick: () => void }) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "flex-1 py-3 px-2 rounded-lg font-label-md transition-all",
      selected 
        ? "bg-primary-container text-on-primary shadow-sm" 
        : "bg-surface-subtle text-on-surface-variant hover:bg-surface-container-highest"
    )}
  >
    {label}
  </button>
);

const RadioGroup = ({ 
  title, 
  description,
  value, 
  onChange, 
  options 
}: { 
  title: string, 
  description?: string,
  value: number | string | null, 
  onChange: (val: any) => void, 
  options: {value: any, label: string}[] 
}) => (
  <section className="flex flex-col gap-3">
    <div>
      <h3 className="font-headline-sm text-headline-sm text-text-primary tracking-tight">{title}</h3>
      {description && <p className="font-body-sm text-body-sm text-text-muted mt-1">{description}</p>}
    </div>
    <div className="flex gap-2">
      {options.map((opt) => (
        <ScaleButton
          key={opt.value}
          value={opt.value}
          label={opt.label}
          selected={value === opt.value}
          onClick={() => onChange(opt.value)}
        />
      ))}
    </div>
  </section>
);

export const Feedback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const attemptId = location.state?.attemptId;
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState<Partial<RatingPayload>>({});

  if (!attemptId) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async () => {
    // Basic validation
    if (
      formData.enjoyment === undefined ||
      formData.curiosity === undefined ||
      formData.deep_dive_interest === undefined ||
      formData.difficulty_felt === undefined ||
      formData.would_repeat === undefined
    ) {
      setError("Please fill out all telemetry dimensions to complete the mapping.");
      return;
    }
    
    // We didn't have pre_interest in the new UI, so default it
    const payload: RatingPayload = {
      enjoyment: formData.enjoyment as number,
      curiosity: formData.curiosity as number,
      deep_dive_interest: formData.deep_dive_interest as number,
      difficulty_felt: formData.difficulty_felt as number,
      pre_interest: formData.pre_interest || 5, // Defaulting as it was removed from UI
      would_repeat: formData.would_repeat as 'yes' | 'maybe' | 'no'
    };

    setError('');
    setLoading(true);
    try {
      await submitFeedback(attemptId, payload);
      setSuccess(true);
      setTimeout(() => {
         navigate('/profile');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback.');
      setLoading(false);
    }
  };

  const scoreOptions = [
    { value: 1, label: '1 - Low' },
    { value: 4, label: '4' },
    { value: 7, label: '7' },
    { value: 10, label: '10 - High' }
  ];

  if (success) {
    return (
      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin pt-space-xl pb-32">
        <div className="bg-surface-card rounded-xl p-space-xl shadow-sm border border-border-subtle flex flex-col items-center justify-center min-h-[400px] text-center">
            <div className="w-16 h-16 rounded-full bg-accent-spark/20 flex items-center justify-center mb-6">
               <span className="material-symbols-outlined text-[32px] text-accent-spark">check_circle</span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-text-primary mb-2">Telemetry Captured</h2>
            <p className="font-body-lg text-text-muted max-w-md">
              Reflection recorded. Your discovery graph has absorbed the session. Redirecting to exploration atelier...
            </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full">
      <div className="bg-surface-card border-b border-border-subtle py-space-xl">
        <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin flex flex-col gap-space-sm">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-subtle text-text-primary font-label-sm text-label-sm uppercase tracking-widest self-start shadow-sm">
            <span className="material-symbols-outlined text-[14px]">flag</span>
            Milestone Achieved
          </span>
          <h1 className="font-headline-lg text-headline-lg tracking-tight text-text-primary mt-2">
            Completion &amp; Reflection
          </h1>
          <p className="font-body-lg text-body-lg text-text-muted max-w-2xl">
            The experience is incomplete without integration. Record your unvarnished cognitive reaction. 
            Do not grade your performance; grade the resonance.
          </p>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-margin-mobile md:px-margin py-space-xl w-full">
        {error && (
            <div className="bg-error-container text-on-error-container p-4 rounded-xl font-label-md mb-8 flex items-center gap-3">
            <span className="material-symbols-outlined">error</span>
            <span>{error}</span>
            </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl">
          <div className="lg:col-span-7 flex flex-col gap-space-lg md:gap-space-xl bg-surface-card rounded-xl p-space-lg shadow-sm border border-border-subtle">
            <div className="flex items-center gap-3 border-b border-border-subtle pb-4">
              <span className="material-symbols-outlined text-text-muted">tune</span>
              <h2 className="font-headline-md text-headline-md text-text-primary">Experiential Telemetry</h2>
            </div>

            <RadioGroup 
              title="Dimension 1: Overall Resonance" 
              description="Did the process itself feel inherently engaging, regardless of the output?"
              value={formData.enjoyment || null} 
              onChange={(val) => setFormData(p => ({...p, enjoyment: val}))}
              options={scoreOptions}
            />

            <RadioGroup 
              title="Dimension 2: Novelty & Cognitive Curiosity" 
              description="Did this spark new mental models? Do you want to understand the underlying theory?"
              value={formData.curiosity || null} 
              onChange={(val) => setFormData(p => ({...p, curiosity: val}))}
              options={scoreOptions}
            />

            <RadioGroup 
              title="Dimension 3: Deep Dive & LOCK-IN Interest" 
              description="Could you see yourself spending the next 3-6 months mastering this specific discipline?"
              value={formData.deep_dive_interest || null} 
              onChange={(val) => setFormData(p => ({...p, deep_dive_interest: val}))}
              options={scoreOptions}
            />

            <RadioGroup 
              title="Dimension 4: Felt Difficulty & Resistance" 
              description="1 = Flow state / Effortless. 10 = Brutal cognitive/physical friction."
              value={formData.difficulty_felt || null} 
              onChange={(val) => setFormData(p => ({...p, difficulty_felt: val}))}
              options={scoreOptions}
            />

            <RadioGroup 
              title="Dimension 5: Would Repeat" 
              description="If left to your own devices with no prompts, would you return to this?"
              value={formData.would_repeat || null} 
              onChange={(val) => setFormData(p => ({...p, would_repeat: val}))}
              options={[
                { value: 'yes', label: 'Yes - Definite' },
                { value: 'maybe', label: 'Maybe - Under Right Conditions' },
                { value: 'no', label: 'No - Once Was Enough' },
              ]}
            />
          </div>

          <aside className="lg:col-span-5 flex flex-col gap-space-md">
             <div className="bg-surface-card rounded-xl p-space-lg shadow-sm border border-border-subtle flex flex-col gap-space-md">
                <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-text-primary text-[20px]">science</span>
                    <span className="font-label-md text-label-md text-text-primary uppercase tracking-wider">Atelier Integration</span>
                </div>
                <p className="font-body-sm text-body-sm text-text-muted">
                    Based on completed execution parameters, your behavioral profile is being analyzed for empirical nodes.
                </p>
                <div className="p-space-md rounded-lg bg-surface-subtle mt-space-xs flex flex-col gap-2">
                    <p className="font-body-sm text-body-sm text-text-muted">
                        Submitting this reflection will update your Skill DNA, unlocking potential new MIX Synthesis bridges in your workshop laboratory.
                    </p>
                </div>
             </div>
          </aside>
        </div>

        <div className="mt-space-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-md bg-surface-card p-space-lg rounded-xl shadow-sm border border-border-subtle">
            <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-text-muted text-[24px]">shield</span>
                <div className="flex flex-col">
                    <span className="font-label-md text-label-md text-text-primary uppercase tracking-wide">Immutable Reflection Register</span>
                    <p className="font-body-sm text-body-sm text-text-muted">
                        Stored in your personal atelier ledger. No algorithmic grading applied.
                    </p>
                </div>
            </div>
            <button 
                onClick={handleSubmit} 
                disabled={loading}
                className="w-full sm:w-auto px-space-lg py-3 rounded-lg bg-primary hover:bg-neutral-800 text-on-primary font-label-md text-label-md flex items-center justify-center gap-2 transition-all shadow-md active:scale-[0.99] disabled:opacity-50"
            >
                <span>{loading ? 'Securing Impressions...' : 'Submit Reflection & Return'}</span>
                {!loading && <span className="material-symbols-outlined text-[18px]">arrow_forward</span>}
                {loading && <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>}
            </button>
        </div>
      </div>
    </div>
  );
};
