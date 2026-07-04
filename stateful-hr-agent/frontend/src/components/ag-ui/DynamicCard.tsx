import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface CardAction {
  label: string;
  event: string;
}

interface DynamicCardProps {
  title: string;
  content?: string;
  message?: string;
  status?: 'success' | 'error' | 'warning' | 'info';
  data?: any;
  actions?: (string | CardAction)[];
  onAction: (event: string, payload: any) => void;
}

export const DynamicCard: React.FC<DynamicCardProps> = ({ title, content, message, status, data, actions, onAction }) => {
  const displayMessage = message || content;
  const isSuccess = status === 'success' || title.toLowerCase().includes('success') || title.toLowerCase().includes('complete') || title.toLowerCase().includes('deleted') || title.toLowerCase().includes('scheduled');

  return (
    <div className="w-full max-w-md rounded-xl bg-white border border-[#e5e5e5] shadow-sm overflow-hidden mb-4 animate-fade-in">
      <div className="px-5 py-5">
        <div className="flex items-start gap-3">
          {isSuccess ? (
            <CheckCircle2 className="w-5 h-5 text-[#16a34a] mt-0.5 flex-shrink-0" />
          ) : status === 'error' ? (
            <AlertCircle className="w-5 h-5 text-[#dc2626] mt-0.5 flex-shrink-0" />
          ) : null}
          <div>
            <h3 className="text-[14px] font-semibold text-black">{title}</h3>
            {displayMessage && (
              <p className="text-[12px] text-[#404040] mt-1 leading-relaxed">
                {displayMessage}
              </p>
            )}
          </div>
        </div>

        {data && typeof data === 'object' && (
          <div className="mt-4 rounded-lg bg-[#fafafa] border border-[#f0f0f0] p-4">
            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
              {Object.entries(data).map(([key, val]) => (
                <div key={key} className="flex flex-col">
                  <span className="text-[9px] font-mono text-[#8c8c8c] uppercase tracking-wider">{key.replace(/_/g, ' ')}</span>
                  <span className="text-[12px] text-black font-medium mt-0.5">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {actions && actions.length > 0 && (
        <div className="px-5 py-3 bg-[#fafafa] border-t border-[#e5e5e5] flex gap-2 flex-wrap">
          {actions.map((action, idx) => {
            const isObj = typeof action === 'object' && action !== null;
            const label = isObj ? (action as CardAction).label : (action as string);
            const eventName = isObj ? (action as CardAction).event : (action as string);
            
            return (
              <button
                key={`${label}-${idx}`}
                onClick={() => onAction(eventName, data || {})}
                className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-white text-[#404040] border border-[#d4d4d4] hover:bg-[#f5f5f5] hover:text-black transition-colors"
              >
                {label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};





