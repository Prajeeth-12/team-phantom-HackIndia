import React from 'react';
import { FileText, Download, Send, ExternalLink, Calendar, User, Briefcase, Mail } from 'lucide-react';

interface DynamicDocumentProps {
  title: string;
  content: string;
  url?: string;
  candidate_name?: string;
  candidate_role?: string;
  candidate_email?: string;
  generated_date?: string;
  onAction: (event: string, payload: any) => void;
}

export const DynamicDocument: React.FC<DynamicDocumentProps> = ({
  title,
  content,
  url,
  candidate_name,
  candidate_role,
  candidate_email,
  generated_date,
  onAction
}) => {
  const finalDate = generated_date || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <div className="w-full max-w-3xl rounded-xl bg-white border border-[#e5e5e5] shadow-sm overflow-hidden mb-6 animate-fade-in">
      {/* Header section */}
      <div className="border-b border-[#e5e5e5] bg-[#fafafa] px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 text-[#404040]">
          <div className="p-1.5 bg-[#f5f5f5] rounded-md border border-[#e5e5e5]">
            <FileText className="w-4 h-4 text-[#737373]" strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-[13px] font-semibold text-black">
              {title || 'Document Preview'}
            </h2>
            <div className="flex items-center gap-1 text-[10px] text-[#737373] mt-0.5 font-mono">
              <Calendar className="w-3 h-3" />
              <span>Generated on {finalDate}</span>
            </div>
          </div>
        </div>

        {/* Action Panel */}
        <div className="flex items-center gap-2">
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[11px] font-medium text-[#2563eb] hover:text-[#1d4ed8] bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md px-2.5 py-1.5 transition-colors"
            >
              <ExternalLink className="w-3 h-3" strokeWidth={2} />
              Open Doc
            </a>
          )}
          <button
            onClick={() => onAction('send_offer_email', { email: candidate_email || 'candidate@example.com', name: candidate_name || 'Candidate', content })}
            className="flex items-center gap-1.5 text-[11px] font-medium text-white bg-black hover:bg-neutral-800 rounded-md px-2.5 py-1.5 transition-colors"
          >
            <Send className="w-3 h-3" strokeWidth={2} />
            Send Email
          </button>
          <button
            onClick={() => onAction('download_pdf', { title, content })}
            className="flex items-center gap-1.5 text-[11px] font-medium text-[#404040] hover:text-black bg-white hover:bg-[#f5f5f5] border border-[#d4d4d4] rounded-md px-2.5 py-1.5 transition-colors"
          >
            <Download className="w-3 h-3" strokeWidth={2} />
            PDF
          </button>
        </div>
      </div>

      {/* Candidate Metadata Summary */}
      {(candidate_name || candidate_role || candidate_email) && (
        <div className="bg-[#fcfcfc] border-b border-[#e5e5e5] px-6 py-3 grid grid-cols-1 sm:grid-cols-3 gap-2">
          {candidate_name && (
            <div className="flex items-center gap-2 text-[11px]">
              <User className="w-3.5 h-3.5 text-[#a3a3a3]" />
              <span className="text-[#737373]">Candidate:</span>
              <span className="font-medium text-black">{candidate_name}</span>
            </div>
          )}
          {candidate_role && (
            <div className="flex items-center gap-2 text-[11px]">
              <Briefcase className="w-3.5 h-3.5 text-[#a3a3a3]" />
              <span className="text-[#737373]">Role:</span>
              <span className="font-medium text-black">{candidate_role}</span>
            </div>
          )}
          {candidate_email && (
            <div className="flex items-center gap-2 text-[11px]">
              <Mail className="w-3.5 h-3.5 text-[#a3a3a3]" />
              <span className="text-[#737373]">Email:</span>
              <span className="font-medium text-black">{candidate_email}</span>
            </div>
          )}
        </div>
      )}

      {/* Document letter container */}
      <div className="px-8 py-10 bg-[#f5f5f5] flex justify-center border-b border-[#e5e5e5]">
        <div className="w-full max-w-2xl bg-white border border-[#e5e5e5] shadow-lg rounded p-8 min-h-[400px] text-left">
          <div className="text-[13px] font-sans text-neutral-800 whitespace-pre-wrap leading-relaxed space-y-4">
            {content || 'No document content preview available.'}
          </div>
        </div>
      </div>
    </div>
  );
};





