import React from 'react';
import { Plus, LogOut, Bot, MessageSquare } from 'lucide-react';
import SessionItem from './SessionItem';

const Sidebar = ({ sessions, activeSessionId, onSelectSession, onNewChat, onLogout, user, refreshSessions, isOpen }) => {
  return (
    <aside className={`flex-shrink-0 glass border-slate-200/80 dark:border-white/10 flex flex-col h-full relative z-20 transition-all duration-300 ${isOpen ? 'w-72 border-r opacity-100' : 'w-0 overflow-hidden opacity-0 border-r-0'}`}>
      <div className="p-4 border-b border-slate-200/80 dark:border-white/10">
        <div className="flex flex-col mb-6 px-2">
          <div className="w-32 h-8 rounded-lg overflow-hidden flex items-center justify-center relative border border-slate-200/50 dark:border-white/5 bg-[#0062ff] self-start shadow-[0_2px_8px_rgba(0,98,255,0.15)]">
            <img 
              src="/dayforce_logo.jpg" 
              alt="Dayforce Logo" 
              className="w-full h-full object-cover scale-[1.7] opacity-95" 
            />
          </div>
          <div className="flex items-center gap-1.5 mt-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-green-400 animate-pulse"></span>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 font-bold uppercase tracking-wider">
              Automation <span className="text-dayforce-blue">Atlas</span>
            </p>
          </div>
        </div>
        
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-dayforceBlue to-dayforceCyan hover:opacity-95 active:scale-[0.98] text-white py-3.5 rounded-xl transition-all font-semibold text-sm shadow-[0_4px_15px_rgba(0,98,255,0.2)] cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar py-4 px-2 space-y-1">
        {sessions.length === 0 ? (
          <div className="text-center text-slate-400 dark:text-gray-500 text-sm mt-8 flex flex-col items-center">
            <MessageSquare className="w-8 h-8 mb-2 opacity-30" />
            <p>No chat history</p>
          </div>
        ) : (
          sessions.map(session => (
            <SessionItem
              key={session.id}
              session={session}
              isActive={session.id === activeSessionId}
              onSelect={() => onSelectSession(session.id)}
              refreshSessions={refreshSessions}
            />
          ))
        )}
      </div>

      <div className="p-4 border-t border-slate-200/80 dark:border-white/10">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-slate-200/70 dark:bg-white/10 border border-slate-300/60 dark:border-transparent flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-slate-700 dark:text-white uppercase">{user?.slice(0,2)}</span>
            </div>
            <span className="text-sm text-slate-700 dark:text-gray-300 font-medium truncate">{user}</span>
          </div>
          <button 
            onClick={onLogout}
            className="p-2 text-slate-400 dark:text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
