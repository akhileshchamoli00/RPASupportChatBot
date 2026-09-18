import React, { useState } from 'react';
import { MessageSquare, MoreVertical, Edit2, Trash2, X, Check } from 'lucide-react';
import { chatAPI } from '../services/api';

const SessionItem = ({ session, isActive, onSelect, refreshSessions }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title);
  const [showMenu, setShowMenu] = useState(false);

  const handleRename = async (e) => {
    e?.preventDefault();
    if (!editTitle.trim() || editTitle === session.title) {
      setIsEditing(false);
      return;
    }
    try {
      await chatAPI.renameSession(session.id, editTitle);
      setIsEditing(false);
      refreshSessions();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    try {
      await chatAPI.deleteSession(session.id);
      refreshSessions();
    } catch (err) {
      console.error(err);
    }
  };

  if (isEditing) {
    return (
      <div className={`flex items-center gap-2 p-2 rounded-lg border ${isActive ? 'border-dayforce-blue dark:border-dayforce-cyan bg-blue-50 dark:bg-dayforce-cyan/5' : 'border-slate-300 dark:border-white/10 bg-slate-100 dark:bg-white/5'}`}>
        <input
          autoFocus
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleRename()}
          className="flex-1 bg-transparent text-sm text-slate-900 dark:text-white focus:outline-none min-w-0 font-sans"
        />
        <button onClick={handleRename} className="p-1 text-emerald-600 dark:text-green-400 hover:bg-emerald-500/20 rounded cursor-pointer">
          <Check className="w-3 h-3" />
        </button>
        <button onClick={() => { setIsEditing(false); setEditTitle(session.title); }} className="p-1 text-red-500 hover:bg-red-500/20 rounded cursor-pointer">
          <X className="w-3 h-3" />
        </button>
      </div>
    );
  }

  return (
    <div 
      onClick={onSelect}
      onMouseLeave={() => setShowMenu(false)}
      className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border ${
        isActive 
          ? 'bg-blue-50 dark:bg-dayforce-blue/10 border-blue-200 dark:border-dayforce-blue/30 text-dayforce-blue dark:text-white font-semibold shadow-xs' 
          : 'border-transparent text-slate-600 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-gray-200'
      }`}
    >
      <div className="flex items-center gap-3 overflow-hidden">
        <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-dayforce-blue dark:text-dayforce-cyan' : 'opacity-50'}`} />
        <span className="text-sm truncate">{session.title}</span>
      </div>

      <div className="relative">
        <button 
          onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
          className={`p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer ${showMenu ? 'opacity-100 bg-slate-200 dark:bg-white/10 text-slate-900 dark:text-white' : 'hover:bg-slate-200 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white'}`}
        >
          <MoreVertical className="w-4 h-4" />
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-[#0c1322] border border-slate-200 dark:border-white/10 rounded-xl shadow-xl z-50 overflow-hidden">
            <button 
              onClick={(e) => { e.stopPropagation(); setIsEditing(true); setShowMenu(false); }}
              className="w-full text-left px-3 py-2.5 text-xs text-slate-700 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-white/5 flex items-center gap-2 cursor-pointer"
            >
              <Edit2 className="w-3 h-3" /> Rename
            </button>
            <button 
              onClick={handleDelete}
              className="w-full text-left px-3 py-2.5 text-xs text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-400/10 flex items-center gap-2 cursor-pointer"
            >
              <Trash2 className="w-3 h-3" /> Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionItem;
