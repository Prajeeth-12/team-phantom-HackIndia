import React, { useState, useMemo } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, Clock, Edit2, Trash2, X, MapPin, Users, AlignLeft, Video } from 'lucide-react';

interface DynamicCalendarProps {
  title: string;
  events: any[];
  onAction: (event: string, payload: any) => void;
}

const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
const getFirstDayOfMonth = (year: number, month: number) => new Date(year, month, 1).getDay();

export const DynamicCalendar: React.FC<DynamicCalendarProps> = ({ title, events, onAction }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createDate, setCreateDate] = useState<string>('');
  const [createTitle, setCreateTitle] = useState('');
  const [createAttendees, setCreateAttendees] = useState('');

  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editStart, setEditStart] = useState('');

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);

  const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const goToday = () => setCurrentDate(new Date());

  const monthName = currentDate.toLocaleString('default', { month: 'long' });
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const eventsByDay = useMemo(() => {
    const map: Record<number, any[]> = {};
    if (!events) return map;
    
    events.forEach(evt => {
      const dStr = evt.start || evt.date || evt.time;
      if (!dStr) return;
      const d = new Date(dStr);
      if (d.getFullYear() === year && d.getMonth() === month) {
        const dateNum = d.getDate();
        if (!map[dateNum]) map[dateNum] = [];
        map[dateNum].push(evt);
      }
    });
    return map;
  }, [events, year, month]);

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAction('create_event', { 
      title: createTitle, 
      start_time: createDate,
      attendees: createAttendees ? createAttendees.split(',').map(a => a.trim()) : []
    });
    setShowCreateModal(false);
    setCreateTitle('');
    setCreateAttendees('');
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAction('update_event', {
      event_id: selectedEvent.id,
      title: editTitle,
      start_time: editStart
    });
    setIsEditing(false);
    setSelectedEvent(null);
  };

  const openCreateModal = (dateStr: string) => {
    setCreateDate(dateStr);
    setShowCreateModal(true);
  };

  const openEventModal = (evt: any) => {
    setSelectedEvent(evt);
    setIsEditing(false);
    setEditTitle(evt.title);
    setEditStart(evt.start);
  };

  const renderCells = () => {
    const cells = [];
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const currentDay = today.getDate();

    for (let i = 0; i < firstDay; i++) {
      cells.push(<div key={`empty-${i}`} className="min-h-[120px] bg-[#fafafa] border border-[#f0f0f0]" />);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dayEvents = eventsByDay[day] || [];
      const isToday = isCurrentMonth && day === currentDay;

      cells.push(
        <div 
          key={`day-${day}`} 
          onClick={() => {
             const selectedDateStr = new Date(year, month, day, 12, 0, 0).toISOString();
             openCreateModal(selectedDateStr);
          }}
          className={`min-h-[120px] border border-[#f0f0f0] p-1.5 transition-colors cursor-pointer hover:bg-[#fafafa] group ${isToday ? 'bg-blue-50/20' : 'bg-white'}`}
        >
          <div className="flex justify-between items-start">
            <span className={`text-[12px] font-medium flex items-center justify-center w-6 h-6 rounded-full ${isToday ? 'bg-[#2563eb] text-white shadow-sm' : 'text-[#737373] group-hover:text-black'}`}>
              {day}
            </span>
          </div>
          
          <div className="mt-1 space-y-1">
            {dayEvents.map((evt, idx) => {
              const timeStr = evt.start ? new Date(evt.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
              return (
                <div 
                  key={idx} 
                  onClick={(e) => {
                    e.stopPropagation();
                    openEventModal(evt);
                  }}
                  className="relative bg-[#2563eb] text-white hover:bg-[#1d4ed8] rounded px-1.5 py-1 text-[11px] leading-tight transition-colors shadow-sm cursor-pointer"
                >
                  <div className="font-medium truncate">{evt.title}</div>
                  {timeStr && <div className="text-blue-100 mt-0.5 text-[10px]">{timeStr}</div>}
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    const totalCells = cells.length;
    const remainingSlots = (7 - (totalCells % 7)) % 7;
    for (let i = 0; i < remainingSlots; i++) {
      cells.push(<div key={`end-empty-${i}`} className="min-h-[120px] bg-[#fafafa] border border-[#f0f0f0]" />);
    }

    return cells;
  };

  return (
    <div className="w-full bg-white rounded-xl border border-[#e5e5e5] shadow-sm overflow-hidden relative">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#e5e5e5] bg-white">
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-1 bg-white border border-[#e5e5e5] rounded-lg p-0.5 shadow-sm">
            <button onClick={prevMonth} className="p-1.5 text-[#737373] hover:text-black hover:bg-[#f5f5f5] rounded transition-colors"><ChevronLeft className="w-4 h-4" /></button>
            <button onClick={goToday} className="px-3 py-1 text-[12px] font-medium text-[#404040] hover:text-black hover:bg-[#f5f5f5] rounded transition-colors">Today</button>
            <button onClick={nextMonth} className="p-1.5 text-[#737373] hover:text-black hover:bg-[#f5f5f5] rounded transition-colors"><ChevronRight className="w-4 h-4" /></button>
          </div>
          <span className="text-[18px] font-medium text-black">
            {monthName} {year}
          </span>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => onAction('get_events', {})}
            className="text-[13px] font-medium text-[#737373] hover:text-black transition-colors"
          >
            Refresh
          </button>
          <button 
            onClick={() => openCreateModal(new Date().toISOString())}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#2563eb] text-white rounded-lg text-[13px] font-medium hover:bg-[#1d4ed8] transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Create
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="bg-white">
        <div className="grid grid-cols-7 border-t border-l border-[#f0f0f0]">
          {dayNames.map(day => (
            <div key={day} className="py-2.5 text-center text-[11px] font-medium text-[#737373] uppercase tracking-wider border-b border-r border-[#f0f0f0]">
              {day}
            </div>
          ))}
          {renderCells().map((cell, idx) => (
            <div key={idx} className="border-b border-r border-[#f0f0f0]">
              {cell}
            </div>
          ))}
        </div>
      </div>

      {/* Create Event Modal Overlay */}
      {showCreateModal && (
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#e5e5e5] bg-[#fafafa]">
              <h3 className="text-[15px] font-semibold text-black">Create Event</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 text-[#737373] hover:text-black hover:bg-[#e5e5e5] rounded-md transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleCreateSubmit} className="p-5 space-y-4">
              <div>
                <input 
                  type="text" 
                  autoFocus
                  placeholder="Add title"
                  value={createTitle}
                  onChange={(e) => setCreateTitle(e.target.value)}
                  className="w-full text-[18px] font-medium text-black border-b border-[#e5e5e5] pb-2 focus:outline-none focus:border-[#2563eb] transition-colors placeholder:text-[#a3a3a3]"
                  required
                />
              </div>
              <div className="flex items-center gap-3 text-[#525252]">
                <Clock className="w-4 h-4 text-[#a3a3a3]" />
                <input 
                  type="datetime-local" 
                  value={createDate.slice(0, 16)} 
                  onChange={(e) => setCreateDate(new Date(e.target.value).toISOString())}
                  className="text-[13px] focus:outline-none bg-transparent"
                  required
                />
              </div>
              <div className="flex items-center gap-3 text-[#525252]">
                <Users className="w-4 h-4 text-[#a3a3a3]" />
                <input 
                  type="text"
                  placeholder="Add guests (comma separated emails)"
                  value={createAttendees}
                  onChange={(e) => setCreateAttendees(e.target.value)}
                  className="w-full text-[13px] focus:outline-none placeholder:text-[#a3a3a3]"
                />
              </div>
              <div className="pt-4 flex justify-end gap-2">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-[13px] font-medium text-[#525252] hover:bg-[#f5f5f5] rounded-lg transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 text-[13px] font-medium bg-[#2563eb] text-white hover:bg-[#1d4ed8] rounded-lg transition-colors shadow-sm">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Event Details / Edit Modal Overlay */}
      {selectedEvent && (
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-end px-3 py-2 bg-[#fafafa] border-b border-[#e5e5e5] gap-1">
              {!isEditing && (
                <>
                  <button onClick={() => setIsEditing(true)} className="p-1.5 text-[#737373] hover:text-black hover:bg-[#e5e5e5] rounded-md transition-colors" title="Edit Event"><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => { onAction('cancel_event', { event_id: selectedEvent.id }); setSelectedEvent(null); }} className="p-1.5 text-[#737373] hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" title="Delete Event"><Trash2 className="w-4 h-4" /></button>
                </>
              )}
              <button onClick={() => setSelectedEvent(null)} className="p-1.5 text-[#737373] hover:text-black hover:bg-[#e5e5e5] rounded-md transition-colors ml-2"><X className="w-4 h-4" /></button>
            </div>
            
            {isEditing ? (
              <form onSubmit={handleEditSubmit} className="p-5 space-y-4">
                <div>
                  <input 
                    type="text" 
                    autoFocus
                    placeholder="Add title"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full text-[18px] font-medium text-black border-b border-[#e5e5e5] pb-2 focus:outline-none focus:border-[#2563eb] transition-colors placeholder:text-[#a3a3a3]"
                    required
                  />
                </div>
                <div className="flex items-center gap-3 text-[#525252]">
                  <Clock className="w-4 h-4 text-[#a3a3a3]" />
                  <input 
                    type="datetime-local" 
                    value={editStart ? editStart.slice(0, 16) : ''} 
                    onChange={(e) => setEditStart(new Date(e.target.value).toISOString())}
                    className="text-[13px] focus:outline-none bg-transparent"
                    required
                  />
                </div>
                <div className="pt-4 flex justify-end gap-2">
                  <button type="button" onClick={() => setIsEditing(false)} className="px-4 py-2 text-[13px] font-medium text-[#525252] hover:bg-[#f5f5f5] rounded-lg transition-colors">Cancel</button>
                  <button type="submit" className="px-4 py-2 text-[13px] font-medium bg-[#2563eb] text-white hover:bg-[#1d4ed8] rounded-lg transition-colors shadow-sm">Save</button>
                </div>
              </form>
            ) : (
              <div className="p-6">
                <div className="flex items-start gap-4 mb-5">
                  <div className="w-4 h-4 mt-1 rounded-sm bg-[#2563eb] flex-shrink-0" />
                  <div>
                    <h3 className="text-[20px] font-medium text-black leading-tight">{selectedEvent.title}</h3>
                    <div className="text-[13px] text-[#525252] mt-1">
                      {selectedEvent.start ? new Date(selectedEvent.start).toLocaleString([], { weekday: 'long', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'No date specified'}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4 ml-8">
                  {selectedEvent.meeting_link && (
                    <div className="flex items-center gap-3 text-[13px]">
                      <Video className="w-4 h-4 text-[#a3a3a3]" />
                      <a href={selectedEvent.meeting_link} target="_blank" rel="noreferrer" className="text-[#2563eb] hover:underline font-medium">Join Google Meet</a>
                    </div>
                  )}
                  {selectedEvent.description && (
                    <div className="flex items-start gap-3 text-[13px]">
                      <AlignLeft className="w-4 h-4 text-[#a3a3a3] mt-0.5" />
                      <p className="text-[#525252] leading-relaxed whitespace-pre-wrap">{selectedEvent.description}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};





