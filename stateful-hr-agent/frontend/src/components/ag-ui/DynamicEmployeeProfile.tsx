import React from 'react';
import { Mail, Briefcase, Building, ShieldCheck, Calendar } from 'lucide-react';

interface Employee {
  name: string;
  email: string;
  department: string;
  position: string;
  status?: string;
  date_of_conversion?: string;
}

interface DynamicEmployeeProfileProps {
  title: string;
  employee: Employee;
  onAction?: (event: string, payload: any) => void;
}

export const DynamicEmployeeProfile: React.FC<DynamicEmployeeProfileProps> = ({ title, employee, onAction }) => {
  if (!employee) return null;
  const initial = employee.name ? employee.name.charAt(0).toUpperCase() : 'E';

  return (
    <div className="w-full max-w-md rounded-xl bg-white border border-[#e5e5e5] shadow-sm overflow-hidden mb-4 animate-fade-in">
      <div className="bg-gradient-to-r from-neutral-50 to-neutral-100 px-5 py-4 border-b border-[#e5e5e5] flex justify-between items-center">
        <h3 className="text-[13px] font-semibold text-black">{title || 'Employee Profile'}</h3>
        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 bg-[#dcfce7] text-[#16a34a] rounded-full flex items-center gap-1">
          <ShieldCheck className="w-3 h-3" />
          {employee.status || 'Active'}
        </span>
      </div>
      
      <div className="p-5 flex gap-4 items-center border-b border-[#e5e5e5]">
        <div className="w-12 h-12 rounded-full bg-neutral-950 flex items-center justify-center text-white text-[18px] font-semibold">
          {initial}
        </div>
        <div>
          <h4 className="text-[15px] font-bold text-black">{employee.name}</h4>
          <p className="text-[11px] text-[#737373] mt-0.5">{employee.position}</p>
        </div>
      </div>

      <div className="p-5 space-y-3 bg-white">
        <div className="flex items-center gap-2.5 text-[12px] text-[#404040]">
          <Mail className="w-4 h-4 text-[#a3a3a3]" />
          <span className="text-[#737373] w-20 flex-shrink-0">Email:</span>
          <span className="text-black font-medium">{employee.email}</span>
        </div>
        <div className="flex items-center gap-2.5 text-[12px] text-[#404040]">
          <Building className="w-4 h-4 text-[#a3a3a3]" />
          <span className="text-[#737373] w-20 flex-shrink-0">Department:</span>
          <span className="text-black font-medium">{employee.department || 'Engineering'}</span>
        </div>
        <div className="flex items-center gap-2.5 text-[12px] text-[#404040]">
          <Briefcase className="w-4 h-4 text-[#a3a3a3]" />
          <span className="text-[#737373] w-20 flex-shrink-0">Position:</span>
          <span className="text-black font-medium">{employee.position}</span>
        </div>
        <div className="flex items-center gap-2.5 text-[12px] text-[#404040]">
          <Calendar className="w-4 h-4 text-[#a3a3a3]" />
          <span className="text-[#737373] w-20 flex-shrink-0">Converted:</span>
          <span className="text-black font-medium">{employee.date_of_conversion || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
        </div>
      </div>

      {onAction && (
        <div className="px-5 py-3 bg-[#fafafa] border-t border-[#e5e5e5] flex gap-2">
          <button
            onClick={() => onAction('open_employee_record', employee)}
            className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-white text-[#404040] border border-[#d4d4d4] hover:bg-[#f5f5f5] hover:text-black transition-colors w-full text-center"
          >
            Manage HR Profile
          </button>
        </div>
      )}
    </div>
  );
};
