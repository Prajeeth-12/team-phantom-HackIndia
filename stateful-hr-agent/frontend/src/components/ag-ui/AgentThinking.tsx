"use client";
import React, { useEffect, useState } from 'react';

interface ThinkingStep {
  emoji: string;
  label: string;
}

const DEFAULT_STEPS: ThinkingStep[] = [
  { emoji: '🧠', label: 'Understanding your request' },
  { emoji: '🔍', label: 'Searching records' },
  { emoji: '⚡', label: 'Executing tools' },
  { emoji: '✨', label: 'Preparing workspace' },
];

interface AgentThinkingProps {
  steps?: ThinkingStep[];
}

export const AgentThinking: React.FC<AgentThinkingProps> = ({ steps }) => {
  const displaySteps = steps && steps.length > 0 ? steps : DEFAULT_STEPS;
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < displaySteps.length - 1) return prev + 1;
        return prev;
      });
    }, 1800);
    return () => clearInterval(interval);
  }, [displaySteps.length]);

  return (
    <div className="flex flex-col gap-1 py-1">
      {displaySteps.map((step, idx) => {
        const isActive = idx === activeStep;
        const isPast = idx < activeStep;
        const isFuture = idx > activeStep;

        return (
          <div key={idx} className="flex items-center gap-2">
            {/* Connector line */}
            {idx > 0 && (
              <div className="ml-[9px] -mt-2.5 -mb-1 w-px h-3" style={{ background: isPast || isActive ? '#16a34a' : '#e5e5e5' }} />
            )}
            <div className={`flex items-center gap-2 transition-all duration-500 ${isFuture ? 'opacity-30' : 'opacity-100'}`}>
              <span className={`text-[13px] ${isActive ? 'thinking-pulse' : ''}`}>{step.emoji}</span>
              <span className={`text-[12px] ${isPast ? 'text-[#16a34a] font-medium' : isActive ? 'text-black font-medium' : 'text-[#a3a3a3]'}`}>
                {step.label}
                {isActive && (
                  <span className="inline-flex gap-0.5 ml-1">
                    <span className="dot-flash-1">.</span>
                    <span className="dot-flash-2">.</span>
                    <span className="dot-flash-3">.</span>
                  </span>
                )}
                {isPast && <span className="ml-1 text-[#16a34a]">✓</span>}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AgentThinking;
