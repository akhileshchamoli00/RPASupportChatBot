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
      <div className={`flex items-center gap-2 p-2 rounded-lg border ${isActive ? 'border-neonBlue bg-neonBlue/5' : 'border-white/10 bg-white/5'}`}>
        <input
          autoFocus
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleRename()}
          className="flex-1 bg-transparent text-sm text-white focus:outline-none min-w-0"
        />
        <button onClick={handleRename} className="p-1 text-green-400 hover:bg-green-400/20 rounded">
          <Check className="w-3 h-3" />
        </button>
        <button onClick={() => { setIsEditing(false); setEditTitle(session.title); }} className="p-1 text-red-400 hover:bg-red-400/20 rounded">
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
          ? 'bg-neonBlue/10 border-neonBlue/30 text-white' 
          : 'border-transparent text-gray-400 hover:bg-white/5 hover:text-gray-200'
      }`}
    >
      <div className="flex items-center gap-3 overflow-hidden">
        <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-neonBlue' : 'opacity-50'}`} />
        <span className="text-sm truncate font-medium">{session.title}</span>
      </div>

      <div className="relative">
        <button 
          onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
          className={`p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity ${showMenu ? 'opacity-100 bg-white/10 text-white' : 'hover:bg-white/10 hover:text-white'}`}
        >
          <MoreVertical className="w-4 h-4" />
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-full mt-1 w-32 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden">
            <button 
              onClick={(e) => { e.stopPropagation(); setIsEditing(true); setShowMenu(false); }}
              className="w-full text-left px-3 py-2 text-xs text-gray-300 hover:bg-white/10 flex items-center gap-2"
            >
              <Edit2 className="w-3 h-3" /> Rename
            </button>
            <button 
              onClick={handleDelete}
              className="w-full text-left px-3 py-2 text-xs text-red-400 hover:bg-red-400/10 flex items-center gap-2"
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
