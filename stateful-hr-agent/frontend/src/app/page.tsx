"use client";
import React, { useState, useRef, useEffect } from 'react';
import { DynamicRenderer, UIConfig } from '../components/ag-ui/DynamicRenderer';
import { Send, Loader2, Bot, User, Sparkles, Activity, FileText, Users, ChevronRight, Presentation } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  const [messages, setMessages] = useState<{role: 'user'|'agent', text: string}[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uiConfig, setUiConfig] = useState<UIConfig | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Load candidates UI schema on mount so the right pane shows the table/form
  useEffect(() => {
    const loadUi = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/ui-schema/candidates');
        if (!res.ok) return;
        const ui = await res.json();
        setUiConfig(ui);
      } catch (e) {
        console.error('Failed to load UI schema', e);
      }
    };
    loadUi();
  }, []);

  const sendMessage = async (text: string, isAction: boolean = false) => {
    if (!text.trim()) return;
    
    if (!isAction) {
        setMessages(prev => [...prev, { role: 'user', text }]);
        setInput('');
    }
    
    setIsLoading(true);
    
    try {
      const res = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      
      const data = await res.json();
      
      setTimeout(() => {
          setMessages(prev => [...prev, { role: 'agent', text: data.response }]);
          if (data.ui) {
              setUiConfig(data.ui);
          }
          setIsLoading(false);
      }, 400);

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'agent', text: 'Error: Cannot connect to FastAPI backend.' }]);
      setIsLoading(false);
    }
  };

  const handleAction = async (payload: { event: string; payload: any }) => {
    // client-side action routing for dynamic UI
    const { event, payload: pl } = payload;

    // map events from DynamicTable buttons (e.g., "Create_action")
    if (event === 'Create_action') {
      // switch to create form provided by uiConfig
      if (uiConfig && uiConfig.create_form) {
        setUiConfig(uiConfig.create_form);
      }
      return;
    }

    // handle form submission action 'create_candidate'
    if (event === 'create_candidate') {
      try {
        const res = await fetch('http://localhost:8000/api/candidates/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(pl)
        });
        if (!res.ok) {
          const err = await res.text();
          console.error('Failed to create candidate', err);
          return;
        }
        const created = await res.json();
        // refresh the table UI by reloading schema
        const schemaRes = await fetch('http://localhost:8000/api/ui-schema/candidates');
        if (schemaRes.ok) setUiConfig(await schemaRes.json());
        // show confirmation in chat
        setMessages(prev => [...prev, { role: 'agent', text: `Created candidate ${created.name}` }]);
      } catch (e) {
        console.error(e);
      }
      return;
    }

    if (event === 'update_action') {
      try {
        const { id, ...updateData } = pl;
        const res = await fetch(`http://localhost:8000/api/candidates/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData)
        });
        if (!res.ok) {
          console.error('Failed to update candidate', await res.text());
          return;
        }
        const updated = await res.json();
        const schemaRes = await fetch('http://localhost:8000/api/ui-schema/candidates');
        if (schemaRes.ok) setUiConfig(await schemaRes.json());
        setMessages(prev => [...prev, { role: 'agent', text: `Updated candidate ${updated.name}` }]);
      } catch (e) {
        console.error(e);
      }
      return;
    }

    if (event === 'delete_action') {
      try {
        const { id } = pl;
        const res = await fetch(`http://localhost:8000/api/candidates/${id}`, {
          method: 'DELETE'
        });
        if (!res.ok) {
          console.error('Failed to delete candidate', await res.text());
          return;
        }
        const schemaRes = await fetch('http://localhost:8000/api/ui-schema/candidates');
        if (schemaRes.ok) setUiConfig(await schemaRes.json());
        setMessages(prev => [...prev, { role: 'agent', text: `Deleted candidate ID ${id}` }]);
      } catch (e) {
        console.error(e);
      }
      return;
    }

    // default: send event to LLM/agent as message
    setMessages(prev => [...prev, { role: 'user', text: `[System Event: ${event}]` }]);
    sendMessage(`The user executed action: ${event}. Payload: ${JSON.stringify(pl)}. Update the database and UI accordingly.`, true);
  };

  const demoPrompts = [
    "Show frontend candidates",
    "Schedule an interview for Alice",
    "Generate an offer letter for Bob",
    "Convert Alice to employee"
  ];

  return (
    <div className="flex h-screen w-full bg-[#1C1C1E] text-[#F2F2F7] font-sans overflow-hidden">
      
      {/* LEFT: Chat Interface */}
      <div className="w-[380px] border-r border-[#2C2C2E] flex flex-col bg-[#1C1C1E] flex-shrink-0 z-10 shadow-2xl">
        <div className="p-5 border-b border-[#2C2C2E] flex justify-between items-center bg-[#1C1C1E]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-sm text-[#F2F2F7]">HR Intelligence</h1>
              <p className="text-[11px] text-[#8E8E93] uppercase tracking-wider font-medium mt-0.5">Agentic Workspace</p>
            </div>
          </div>
          <Link href="/architecture" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 bg-indigo-500/10 px-2.5 py-1.5 rounded-full transition">
            Arch <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-70 mt-[-10px] animate-in fade-in duration-500">
              <Presentation className="w-12 h-12 text-indigo-400 mb-4" />
              <p className="text-sm font-medium text-[#F2F2F7] mb-3">Hackathon Demo Mode</p>
              <div className="space-y-2.5 w-full px-2">
                {demoPrompts.map((p, i) => (
                  <button 
                    key={i} 
                    onClick={() => sendMessage(p)}
                    className="w-full text-xs text-left bg-[#2C2C2E] hover:bg-[#3A3A3C] transition p-3 rounded-xl text-[#D1D1D6] border border-[#3A3A3C] hover:border-indigo-500/30"
                  >
                    "{p}"
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} transition-all`}>
              <div className={`flex gap-3 max-w-[90%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-6 h-6 flex-shrink-0 rounded-full flex items-center justify-center mt-1 ${msg.role === 'user' ? 'bg-[#2C2C2E]' : 'bg-indigo-500'}`}>
                  {msg.role === 'user' ? <User className="w-3 h-3 text-[#F2F2F7]" /> : <Bot className="w-3 h-3 text-white" />}
                </div>
                <div className={`p-3.5 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-[#2C2C2E] text-[#F2F2F7] rounded-tr-sm' : 'bg-transparent text-[#D1D1D6] rounded-tl-sm border border-[#2C2C2E]'}`}>
                  {msg.text}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex gap-3">
                <div className="w-6 h-6 flex-shrink-0 rounded-full bg-indigo-500 flex items-center justify-center mt-1">
                  <Bot className="w-3 h-3 text-white" />
                </div>
                <div className="p-3.5 flex items-center justify-center h-[48px]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-4 bg-[#1C1C1E] border-t border-[#2C2C2E]">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} className="relative flex items-center">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type a command..." 
              className="w-full bg-[#2C2C2E] text-[#F2F2F7] placeholder-[#8E8E93] rounded-xl pl-4 pr-12 py-3.5 text-sm focus:outline-none border border-[#3A3A3C] focus:border-indigo-500/50"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              disabled={isLoading || !input.trim()}
              className="absolute right-2 p-2 rounded-lg bg-indigo-500 text-white disabled:opacity-40 disabled:bg-transparent transition-colors hover:bg-indigo-600"
              aria-label="Send message"
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* RIGHT: Dynamic Workspace */}
      <div className="flex-1 bg-gradient-to-br from-[#09090B] to-[#161618] relative overflow-y-auto p-10 flex flex-col items-center justify-center">
        {!uiConfig ? (
          <div className="w-full max-w-5xl animate-in fade-in zoom-in-95 duration-500">
            <div className="mb-8 pl-2">
              <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Dashboard Overview</h2>
              <p className="text-[#8E8E93]">Welcome to the Stateful AI HR Agent Platform.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {[
                { title: 'Total Candidates', value: '142', icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                { title: 'Pending Interviews', value: '12', icon: Activity, color: 'text-purple-400', bg: 'bg-purple-400/10' },
                { title: 'Offers Sent', value: '5', icon: FileText, color: 'text-emerald-400', bg: 'bg-emerald-400/10' }
              ].map((stat, i) => (
                <div key={i} className="bg-[#1C1C1E]/80 backdrop-blur-sm border border-[#2C2C2E] p-6 rounded-3xl flex items-center gap-5 hover:border-[#3A3A3C] transition shadow-lg">
                  <div className={`w-14 h-14 rounded-full ${stat.bg} ${stat.color} flex items-center justify-center`}>
                    <stat.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                    <p className="text-sm font-medium text-[#8E8E93]">{stat.title}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="bg-[#1C1C1E]/50 border border-[#2C2C2E] rounded-3xl p-10 text-center border-dashed">
              <Sparkles className="w-10 h-10 text-indigo-500/50 mx-auto mb-4 animate-pulse" />
              <h3 className="text-lg font-medium text-[#D1D1D6]">Agentic UI Canvas</h3>
              <p className="text-[#8E8E93] text-sm mt-3 max-w-md mx-auto leading-relaxed">
                Click a demo action on the left or type a command. The LLM will autonomously plan its steps, execute MCP actions, and generate the UI in this space.
              </p>
            </div>
          </div>
        ) : (
          <div className="w-full max-w-4xl transition-all duration-500 ease-out transform translate-y-0 opacity-100">
            <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-[32px] p-8 shadow-2xl">
              <DynamicRenderer uiConfig={uiConfig} onEmitEvent={handleAction} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

