import React from 'react';
import { Plus, LogOut, Bot, MessageSquare } from 'lucide-react';
import SessionItem from './SessionItem';

const Sidebar = ({ sessions, activeSessionId, onSelectSession, onNewChat, onLogout, user, refreshSessions }) => {
  return (
    <aside className="w-72 flex-shrink-0 glass border-r border-white/10 flex flex-col h-full relative z-20">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-3 mb-6 px-2">
          <div className="w-10 h-10 rounded-xl bg-neonBlue/10 border border-neonBlue/30 flex items-center justify-center">
            <Bot className="w-6 h-6 neon-text" />
          </div>
          <div>
            <h2 className="font-bold text-white tracking-wide">RPA Core</h2>
            <p className="text-xs text-neonBlue">Online</p>
          </div>
        </div>
        
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-neonBlue/10 border border-white/10 hover:border-neonBlue/50 text-white hover:text-neonBlue py-3 rounded-xl transition-all group"
        >
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-300" />
          <span className="font-medium text-sm">New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide py-4 px-2 space-y-1">
        {sessions.length === 0 ? (
          <div className="text-center text-gray-500 text-sm mt-8 flex flex-col items-center">
            <MessageSquare className="w-8 h-8 mb-2 opacity-20" />
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

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white uppercase">{user?.slice(0,2)}</span>
            </div>
            <span className="text-sm text-gray-300 truncate">{user}</span>
          </div>
          <button 
            onClick={onLogout}
            className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
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
