import React from 'react';
import { MoreHorizontal, Plus, Mail, Phone, Calendar, CheckCircle2, Clock } from 'lucide-react';

interface KanbanProps {
  title?: string;
  columns: {
    id: string;
    title: string;
    color: string;
  }[];
  items: any[];
  onAction: (event: string, payload: any) => void;
}

export const DynamicKanban: React.FC<KanbanProps> = ({ title = "Candidate Pipeline Kanban", columns, items, onAction }) => {
  const getItemsByStatus = (statusId: string) => {
    return items.filter(item => {
      const itemStatus = (item.status || 'applied').toLowerCase();
      return itemStatus === statusId.toLowerCase();
    });
  };

  return (
    <div className="w-full h-full flex flex-col bg-white rounded-xl shadow-sm border border-[#e5e5e5] overflow-hidden">
      <div className="px-5 py-4 border-b border-[#e5e5e5] flex items-center justify-between bg-white">
        <div>
          <h2 className="text-[16px] font-semibold text-black">{title}</h2>
          <p className="text-[12px] text-[#737373] mt-0.5">Dynamically generated Kanban pipeline</p>
        </div>
        <button 
          onClick={() => onAction('create_candidate', {})}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-black text-white rounded-lg text-[12px] font-medium hover:bg-[#1f1f1f] transition-all"
        >
          <Plus className="w-3.5 h-3.5" /> Add Candidate
        </button>
      </div>

      <div className="flex-1 overflow-x-auto p-5 bg-[#fafafa]">
        <div className="flex gap-5 h-full min-w-max">
          {columns.map(col => {
            const colItems = getItemsByStatus(col.id);
            return (
              <div key={col.id} className="w-[300px] flex flex-col bg-[#f0f0f0]/50 rounded-xl border border-[#e5e5e5]/50 overflow-hidden shrink-0">
                <div className={`px-4 py-3 border-b border-[#e5e5e5] bg-white flex items-center justify-between`}>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${col.color}`} />
                    <h3 className="text-[13px] font-semibold text-black uppercase tracking-wider">{col.title}</h3>
                  </div>
                  <span className="text-[11px] font-mono bg-[#f5f5f5] text-[#737373] px-2 py-0.5 rounded-full">
                    {colItems.length}
                  </span>
                </div>
                
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {colItems.map((item, idx) => (
                    <div 
                      key={item.id || idx}
                      className="bg-white p-3.5 rounded-lg border border-[#e5e5e5] shadow-sm hover:shadow-md hover:border-[#d4d4d4] transition-all group cursor-pointer"
                      onClick={() => onAction('edit_candidate', { id: item.id })}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-[14px] font-medium text-black leading-tight group-hover:text-blue-600 transition-colors">
                          {item.name}
                        </h4>
                        <button 
                          onClick={(e) => { e.stopPropagation(); onAction('edit_candidate', { id: item.id }); }}
                          className="text-[#a3a3a3] hover:text-black opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                      </div>
                      
                      {item.role && (
                        <div className="text-[11px] font-medium text-[#525252] bg-[#f5f5f5] px-2 py-1 rounded inline-block mb-3">
                          {item.role}
                        </div>
                      )}
                      
                      <div className="space-y-1.5 mt-1">
                        {item.email && (
                          <div className="flex items-center gap-2 text-[11px] text-[#737373]">
                            <Mail className="w-3 h-3 text-[#a3a3a3]" />
                            <span className="truncate">{item.email}</span>
                          </div>
                        )}
                        {item.phone && (
                          <div className="flex items-center gap-2 text-[11px] text-[#737373]">
                            <Phone className="w-3 h-3 text-[#a3a3a3]" />
                            <span>{item.phone}</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-3 pt-3 border-t border-[#f0f0f0] flex gap-2">
                        {col.id.toLowerCase() === 'applied' && (
                          <button onClick={(e) => { e.stopPropagation(); onAction('workflow', { message: `Schedule an interview for ${item.name} and update their status to interviewing` }); }} className="flex-1 py-1.5 bg-blue-50 text-blue-600 rounded text-[10px] font-semibold hover:bg-blue-100 transition-colors flex items-center justify-center gap-1">
                            <Calendar className="w-3 h-3" /> Interview
                          </button>
                        )}
                        {col.id.toLowerCase() === 'interviewing' && (
                          <button onClick={(e) => { e.stopPropagation(); onAction('workflow', { message: `Update ${item.name}'s status to selected` }); }} className="flex-1 py-1.5 bg-green-50 text-green-600 rounded text-[10px] font-semibold hover:bg-green-100 transition-colors flex items-center justify-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Select
                          </button>
                        )}
                        {col.id.toLowerCase() === 'selected' && (
                          <button onClick={(e) => { e.stopPropagation(); onAction('workflow', { message: `Generate an offer letter and convert ${item.name} to employee` }); }} className="flex-1 py-1.5 bg-purple-50 text-purple-600 rounded text-[10px] font-semibold hover:bg-purple-100 transition-colors flex items-center justify-center gap-1">
                            <Clock className="w-3 h-3" /> Hire
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {colItems.length === 0 && (
                    <div className="h-20 border-2 border-dashed border-[#e5e5e5] rounded-lg flex items-center justify-center text-[#a3a3a3] text-[11px] font-medium">
                      Drop here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
