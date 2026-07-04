import React from 'react';

export interface UIConfig {
  type: string;
  [key: string]: any;
}

interface DynamicRendererProps {
  uiConfig: UIConfig | null;
  actionState?: { isBusy: boolean; event: string | null };
  onEmitEvent: (eventPayload: { event: string; payload: any }) => void;
}

// Lazy imports to keep the file clean
import { DynamicTable } from './DynamicTable';
import { DynamicForm } from './DynamicForm';
import { DynamicCalendar } from './DynamicCalendar';
import { DynamicCard } from './DynamicCard';
import { DynamicDocument } from './DynamicDocument';
import { DynamicWorkspaceOverview } from './DynamicWorkspaceOverview';
import { DynamicAgentTrace } from './DynamicAgentTrace';
import { DynamicDataExplorer } from './DynamicDataExplorer';
import { DynamicMailView } from './DynamicMailView';
import { DynamicEmployeeProfile } from './DynamicEmployeeProfile';

export const DynamicRenderer: React.FC<DynamicRendererProps> = ({ uiConfig, actionState, onEmitEvent }) => {
  if (!uiConfig) return null;

  const handleAction = (eventName: string, payload: any) => {
    onEmitEvent({
      event: eventName,
      payload
    });
  };

  switch (uiConfig.type) {
    case 'workspace_overview':
      return <DynamicWorkspaceOverview {...(uiConfig as any)} onAction={handleAction} />;
    case 'agent_trace':
      return <DynamicAgentTrace {...(uiConfig as any)} />;
    case 'data_explorer':
      return <DynamicDataExplorer {...(uiConfig as any)} onAction={handleAction} />;
    case 'mail_view':
      return <DynamicMailView {...(uiConfig as any)} onAction={handleAction} />;
    case 'table':
      return <DynamicTable {...(uiConfig as any)} actionState={actionState} onAction={handleAction} />;
    case 'form':
      return <DynamicForm {...(uiConfig as any)} onAction={handleAction} />;
    case 'calendar':
      return <DynamicCalendar {...(uiConfig as any)} onAction={handleAction} />;
    case 'dashboard_card':
      return <DynamicCard {...(uiConfig as any)} onAction={handleAction} />;
    case 'employee_profile':
      return <DynamicEmployeeProfile {...(uiConfig as any)} onAction={handleAction} />;
    case 'document_preview':
      return <DynamicDocument {...(uiConfig as any)} onAction={handleAction} />;
    case 'timeline':
      return (
        <div className="rounded-xl bg-white border border-[#e5e5e5] shadow-sm p-5">
          <p className="text-[13px] font-medium text-black mb-3">{uiConfig.title || 'Timeline'}</p>
          <pre className="text-[11px] font-mono text-[#404040] bg-[#fafafa] border border-[#f0f0f0] p-3 rounded-md overflow-x-auto">
            {JSON.stringify(uiConfig.events, null, 2)}
          </pre>
        </div>
      );
    default:
      return (
        <div className="rounded-xl border border-dashed border-[#d4d4d4] bg-[#fafafa] p-5 text-center">
          <p className="text-[12px] text-[#737373]">
            Unsupported component: <span className="bg-white border border-[#e5e5e5] px-1.5 py-0.5 rounded text-[#404040] ml-1">{uiConfig.type}</span>
          </p>
        </div>
      );
  }
};





