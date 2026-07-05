import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Edit2,
  Plus,
  Trash2,
  Users,
  Video,
  X,
} from 'lucide-react';

interface DynamicCalendarProps {
  title?: string;
  events: any[];
  onAction: (event: string, payload: any) => void;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: Date | null;
  end: Date | null;
  attendees: string[];
  meetingLink?: string;
  description?: string;
}

interface CalendarDayCell {
  key: string;
  date: Date;
  inCurrentMonth: boolean;
}

const WEEKDAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const EVENT_COLORS = ['#1a73e8', '#0b8043', '#d50000', '#e67c73', '#f6bf26', '#8e24aa'];

const startOfMonth = (date: Date) => new Date(date.getFullYear(), date.getMonth(), 1);
const endOfMonth = (date: Date) => new Date(date.getFullYear(), date.getMonth() + 1, 0);
const startOfDay = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

const toDateOrNull = (value: unknown): Date | null => {
  if (!value || typeof value !== 'string') return null;
  const dt = new Date(value);
  return Number.isNaN(dt.getTime()) ? null : dt;
};

const toDateTimeLocalValue = (date: Date | null) => {
  if (!date) return '';
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const mi = String(date.getMinutes()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
};

const prettyDateTime = (date: Date | null) => {
  if (!date) return 'No date set';
  return date.toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

const buildMonthGrid = (viewDate: Date): CalendarDayCell[] => {
  const monthStart = startOfMonth(viewDate);
  const firstGridDate = new Date(monthStart);
  firstGridDate.setDate(monthStart.getDate() - monthStart.getDay());

  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(firstGridDate);
    d.setDate(firstGridDate.getDate() + i);
    return {
      key: `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`,
      date: d,
      inCurrentMonth: d.getMonth() === viewDate.getMonth() && d.getFullYear() === viewDate.getFullYear(),
    };
  });
};

const normalizeEvent = (evt: any): CalendarEvent => {
  const start = toDateOrNull(evt.start_time || evt.start || evt.date || evt.time);
  const end = toDateOrNull(evt.end_time || evt.end);

  return {
    id: String(evt.id ?? `${evt.title || 'event'}-${evt.start_time || evt.start || Math.random()}`),
    title: String(evt.title || 'Untitled event'),
    start,
    end,
    attendees: Array.isArray(evt.attendees) ? evt.attendees.filter(Boolean) : [],
    meetingLink: evt.meeting_link || evt.meet_link || evt.link,
    description: evt.description || evt.notes,
  };
};

export const DynamicCalendar: React.FC<DynamicCalendarProps> = ({ title, events, onAction }) => {
  const today = startOfDay(new Date());
  const [viewDate, setViewDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(today);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createStart, setCreateStart] = useState('');
  const [createAttendees, setCreateAttendees] = useState('');

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isEditingEvent, setIsEditingEvent] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editStart, setEditStart] = useState('');

  const normalizedEvents = useMemo(() => {
    const safeEvents = Array.isArray(events) ? events : [];
    return safeEvents
      .map(normalizeEvent)
      .sort((a, b) => (a.start?.getTime() || 0) - (b.start?.getTime() || 0));
  }, [events]);

  const gridCells = useMemo(() => buildMonthGrid(viewDate), [viewDate]);

  const eventsByDate = useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {};

    normalizedEvents.forEach((evt) => {
      if (!evt.start) return;
      const key = `${evt.start.getFullYear()}-${evt.start.getMonth()}-${evt.start.getDate()}`;
      if (!map[key]) map[key] = [];
      map[key].push(evt);
    });

    return map;
  }, [normalizedEvents]);

  const monthLabel = viewDate.toLocaleString([], { month: 'long', year: 'numeric' });

  const selectedDateKey = `${selectedDate.getFullYear()}-${selectedDate.getMonth()}-${selectedDate.getDate()}`;
  const selectedDayEvents = eventsByDate[selectedDateKey] || [];

  const openCreateModalForDate = (date: Date) => {
    const start = new Date(date);
    start.setHours(12, 0, 0, 0);
    setCreateStart(toDateTimeLocalValue(start));
    setCreateTitle('');
    setCreateAttendees('');
    setShowCreateModal(true);
  };

  const openEventPanel = (evt: CalendarEvent) => {
    setSelectedEvent(evt);
    setIsEditingEvent(false);
    setEditTitle(evt.title);
    setEditStart(toDateTimeLocalValue(evt.start));
  };

  const submitCreate = (e: React.FormEvent) => {
    e.preventDefault();
    onAction('create_event', {
      title: createTitle,
      start_time: new Date(createStart).toISOString(),
      attendees: createAttendees
        ? createAttendees.split(',').map((x) => x.trim()).filter(Boolean)
        : [],
    });
    setShowCreateModal(false);
  };

  const submitEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvent) return;

    onAction('update_event', {
      event_id: selectedEvent.id,
      title: editTitle,
      start_time: new Date(editStart).toISOString(),
    });
    setSelectedEvent(null);
    setIsEditingEvent(false);
  };

  return (
    <div className="w-full overflow-hidden rounded-xl border border-[#dadce0] bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-[#eceff1] px-4 py-3 md:flex-row md:items-center md:justify-between md:px-5">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-1 rounded-lg border border-[#dadce0] bg-white p-1">
            <button
              type="button"
              onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1))}
              className="rounded-md p-1.5 text-[#5f6368] hover:bg-[#f1f3f4]"
              aria-label="Previous month"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => {
                const now = new Date();
                setViewDate(now);
                setSelectedDate(startOfDay(now));
              }}
              className="rounded-md px-3 py-1 text-[12px] font-medium text-[#3c4043] hover:bg-[#f1f3f4]"
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1))}
              className="rounded-md p-1.5 text-[#5f6368] hover:bg-[#f1f3f4]"
              aria-label="Next month"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4 text-[#1a73e8]" />
            <h3 className="text-[18px] font-medium text-[#202124]">{title || monthLabel}</h3>
            <span className="text-[14px] text-[#5f6368]">{monthLabel}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onAction('get_events', {
              start_date: startOfMonth(viewDate).toISOString(),
              end_date: endOfMonth(viewDate).toISOString(),
            })}
            className="rounded-md border border-[#dadce0] px-3 py-1.5 text-[12px] font-medium text-[#3c4043] hover:bg-[#f8f9fa]"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={() => openCreateModalForDate(selectedDate)}
            className="inline-flex items-center gap-1.5 rounded-full bg-[#1a73e8] px-3.5 py-2 text-[12px] font-medium text-white hover:bg-[#1765cc]"
          >
            <Plus className="h-4 w-4" />
            Create
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_280px]">
        <div className="border-r border-[#eceff1]">
          <div className="grid grid-cols-7 border-b border-[#eceff1] bg-[#fff]">
            {WEEKDAY_NAMES.map((name) => (
              <div key={name} className="py-2 text-center text-[11px] font-medium uppercase tracking-wide text-[#5f6368]">
                {name}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {gridCells.map((cell) => {
              const key = `${cell.date.getFullYear()}-${cell.date.getMonth()}-${cell.date.getDate()}`;
              const dayEvents = eventsByDate[key] || [];
              const isToday = sameDay(cell.date, today);
              const isSelected = sameDay(cell.date, selectedDate);

              return (
                <button
                  key={cell.key}
                  type="button"
                  onClick={() => setSelectedDate(startOfDay(cell.date))}
                  onDoubleClick={() => openCreateModalForDate(cell.date)}
                  className={`group min-h-[112px] border-b border-r border-[#eceff1] p-1.5 text-left align-top transition-colors md:min-h-[128px] ${
                    cell.inCurrentMonth ? 'bg-white hover:bg-[#f8f9fa]' : 'bg-[#f8f9fa] text-[#9aa0a6]'
                  } ${isSelected ? 'bg-[#e8f0fe]' : ''}`}
                >
                  <div className="mb-1 flex justify-end">
                    <span
                      className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-[11px] ${
                        isToday ? 'bg-[#1a73e8] font-semibold text-white' : 'text-[#3c4043]'
                      }`}
                    >
                      {cell.date.getDate()}
                    </span>
                  </div>

                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map((evt, idx) => {
                      const color = EVENT_COLORS[idx % EVENT_COLORS.length];
                      return (
                        <div
                          key={`${evt.id}-${idx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            openEventPanel(evt);
                          }}
                          className="truncate rounded px-1.5 py-0.5 text-[10px] font-medium text-white"
                          style={{ backgroundColor: color }}
                          title={`${evt.title} - ${prettyDateTime(evt.start)}`}
                        >
                          {evt.start ? `${evt.start.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} ` : ''}
                          {evt.title}
                        </div>
                      );
                    })}
                    {dayEvents.length > 3 && (
                      <div className="text-[10px] font-medium text-[#5f6368]">+{dayEvents.length - 3} more</div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <aside className="h-full bg-white p-4">
          <div className="mb-3 text-[12px] font-semibold text-[#5f6368]">Selected Date</div>
          <div className="mb-4 text-[16px] font-medium text-[#202124]">
            {selectedDate.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })}
          </div>

          <button
            type="button"
            onClick={() => openCreateModalForDate(selectedDate)}
            className="mb-5 inline-flex items-center gap-1.5 rounded-md border border-[#dadce0] px-3 py-2 text-[12px] font-medium text-[#3c4043] hover:bg-[#f8f9fa]"
          >
            <Plus className="h-4 w-4" />
            Create on this day
          </button>

          <div className="space-y-2">
            {selectedDayEvents.length === 0 && (
              <p className="rounded-lg border border-dashed border-[#dadce0] p-3 text-[12px] text-[#5f6368]">
                No events scheduled.
              </p>
            )}

            {selectedDayEvents.map((evt, idx) => (
              <button
                key={`${evt.id}-sidebar-${idx}`}
                type="button"
                onClick={() => openEventPanel(evt)}
                className="w-full rounded-lg border border-[#eceff1] p-3 text-left hover:bg-[#f8f9fa]"
              >
                <div className="mb-1 text-[12px] font-semibold text-[#202124]">{evt.title}</div>
                <div className="text-[11px] text-[#5f6368]">{prettyDateTime(evt.start)}</div>
              </button>
            ))}
          </div>
        </aside>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-3">
          <div className="w-full max-w-lg rounded-xl border border-[#dadce0] bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-[#eceff1] px-4 py-3">
              <h4 className="text-[16px] font-medium text-[#202124]">Create event</h4>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="rounded-md p-1 text-[#5f6368] hover:bg-[#f1f3f4]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={submitCreate} className="space-y-4 px-4 py-4">
              <input
                type="text"
                required
                autoFocus
                value={createTitle}
                onChange={(e) => setCreateTitle(e.target.value)}
                placeholder="Add title"
                className="w-full rounded-md border border-[#dadce0] px-3 py-2 text-[14px] text-[#202124] outline-none focus:border-[#1a73e8]"
              />

              <div className="flex items-center gap-2 rounded-md border border-[#dadce0] px-3 py-2">
                <Clock className="h-4 w-4 text-[#5f6368]" />
                <input
                  type="datetime-local"
                  required
                  value={createStart}
                  onChange={(e) => setCreateStart(e.target.value)}
                  className="w-full text-[13px] text-[#202124] outline-none"
                />
              </div>

              <div className="flex items-center gap-2 rounded-md border border-[#dadce0] px-3 py-2">
                <Users className="h-4 w-4 text-[#5f6368]" />
                <input
                  type="text"
                  value={createAttendees}
                  onChange={(e) => setCreateAttendees(e.target.value)}
                  placeholder="Guests (comma separated emails)"
                  className="w-full text-[13px] text-[#202124] outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-md px-3 py-1.5 text-[12px] font-medium text-[#3c4043] hover:bg-[#f1f3f4]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-[#1a73e8] px-4 py-1.5 text-[12px] font-medium text-white hover:bg-[#1765cc]"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 px-3">
          <div className="w-full max-w-lg rounded-xl border border-[#dadce0] bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-[#eceff1] px-4 py-3">
              <div className="text-[16px] font-medium text-[#202124]">Event details</div>
              <div className="flex items-center gap-1">
                {!isEditingEvent && (
                  <>
                    <button
                      type="button"
                      onClick={() => setIsEditingEvent(true)}
                      className="rounded-md p-1.5 text-[#5f6368] hover:bg-[#f1f3f4]"
                      title="Edit"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        onAction('cancel_event', { event_id: selectedEvent.id });
                        setSelectedEvent(null);
                      }}
                      className="rounded-md p-1.5 text-[#d93025] hover:bg-[#fce8e6]"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </>
                )}
                <button
                  type="button"
                  onClick={() => setSelectedEvent(null)}
                  className="rounded-md p-1.5 text-[#5f6368] hover:bg-[#f1f3f4]"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {isEditingEvent ? (
              <form onSubmit={submitEdit} className="space-y-4 px-4 py-4">
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full rounded-md border border-[#dadce0] px-3 py-2 text-[14px] text-[#202124] outline-none focus:border-[#1a73e8]"
                />
                <div className="flex items-center gap-2 rounded-md border border-[#dadce0] px-3 py-2">
                  <Clock className="h-4 w-4 text-[#5f6368]" />
                  <input
                    type="datetime-local"
                    required
                    value={editStart}
                    onChange={(e) => setEditStart(e.target.value)}
                    className="w-full text-[13px] text-[#202124] outline-none"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsEditingEvent(false)}
                    className="rounded-md px-3 py-1.5 text-[12px] font-medium text-[#3c4043] hover:bg-[#f1f3f4]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="rounded-md bg-[#1a73e8] px-4 py-1.5 text-[12px] font-medium text-white hover:bg-[#1765cc]"
                  >
                    Save changes
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4 px-4 py-4">
                <div>
                  <h5 className="text-[18px] font-medium text-[#202124]">{selectedEvent.title}</h5>
                  <p className="mt-1 text-[13px] text-[#5f6368]">{prettyDateTime(selectedEvent.start)}</p>
                  {selectedEvent.end && (
                    <p className="text-[13px] text-[#5f6368]">Ends: {prettyDateTime(selectedEvent.end)}</p>
                  )}
                </div>

                {selectedEvent.meetingLink && (
                  <div className="flex items-center gap-2 text-[13px]">
                    <Video className="h-4 w-4 text-[#5f6368]" />
                    <a
                      href={selectedEvent.meetingLink}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[#1a73e8] hover:underline"
                    >
                      Join meeting
                    </a>
                  </div>
                )}

                {selectedEvent.attendees.length > 0 && (
                  <div>
                    <div className="mb-1 text-[12px] font-semibold text-[#5f6368]">Guests</div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedEvent.attendees.map((att, idx) => (
                        <span
                          key={`${att}-${idx}`}
                          className="rounded-full bg-[#f1f3f4] px-2 py-0.5 text-[11px] text-[#3c4043]"
                        >
                          {att}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedEvent.description && (
                  <div>
                    <div className="mb-1 text-[12px] font-semibold text-[#5f6368]">Description</div>
                    <p className="whitespace-pre-wrap text-[13px] text-[#3c4043]">{selectedEvent.description}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
