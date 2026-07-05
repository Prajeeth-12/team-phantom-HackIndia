import React from 'react';
import { CheckCircle2, AlertCircle, TrendingUp, TrendingDown, Clock, Activity } from 'lucide-react';

interface CardAction {
  label: string;
  event: string;
}

interface Metric {
  label: string;
  value: string | number;
  trend?: string;
}

interface ActivityItem {
  description: string;
  timestamp?: string;
}

interface DynamicCardProps {
  title: string;
  content?: string;
  message?: string;
  status?: 'success' | 'error' | 'warning' | 'info';
  data?: any;
  metrics?: Metric[];
  recent_activity?: ActivityItem[];
  actions?: (string | CardAction)[];
  onAction: (event: string, payload: any) => void;
}

export const DynamicCard: React.FC<DynamicCardProps> = ({ title, content, message, status, data, metrics, recent_activity, actions, onAction }) => {
  const displayMessage = message || content;
  const isSuccess = status === 'success' || title.toLowerCase().includes('success') || title.toLowerCase().includes('complete') || title.toLowerCase().includes('deleted') || title.toLowerCase().includes('scheduled');

  return (
    <div className="w-full rounded-xl bg-white border border-[#e5e5e5] shadow-sm overflow-hidden mb-4 animate-fade-in">
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

        {metrics && metrics.length > 0 && (
          <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {metrics.map((m, i) => (
              <div key={i} className="p-3 bg-[#fafafa] border border-[#f0f0f0] rounded-lg flex flex-col">
                <span className="text-[10px] font-medium text-[#737373] uppercase tracking-wide">{m.label}</span>
                <div className="flex items-end gap-2 mt-1">
                  <span className="text-[18px] font-bold text-black leading-none">{m.value}</span>
                  {m.trend && (
                    <span className={`text-[10px] font-medium flex items-center mb-0.5 ${m.trend.startsWith('-') ? 'text-[#dc2626]' : 'text-[#16a34a]'}`}>
                      {m.trend.startsWith('-') ? <TrendingDown className="w-3 h-3 mr-0.5" /> : <TrendingUp className="w-3 h-3 mr-0.5" />}
                      {m.trend}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {recent_activity && recent_activity.length > 0 && (
          <div className="mt-5 border-t border-[#f0f0f0] pt-4">
            <h4 className="text-[11px] font-semibold text-black uppercase tracking-wider mb-3 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-[#737373]" /> Recent Activity
            </h4>
            <div className="space-y-3">
              {recent_activity.map((act, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <div className="mt-1 flex-shrink-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#d4d4d4]" />
                  </div>
                  <div>
                    <p className="text-[12px] text-[#404040] leading-snug">{act.description}</p>
                    {act.timestamp && (
                      <p className="text-[10px] text-[#8c8c8c] mt-0.5 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {act.timestamp}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data && typeof data === 'object' && !metrics && (
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




