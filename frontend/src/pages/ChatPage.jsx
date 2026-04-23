import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import { chatAPI } from '../services/api';

const ChatPage = ({ user, onLogout }) => {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSessions = async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data);
      if (res.data.length > 0 && !activeSessionId) {
        setActiveSessionId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleNewChat = async () => {
    try {
      const res = await chatAPI.createSession('New Chat');
      setSessions([res.data, ...sessions]);
      setActiveSessionId(res.data.id);
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden relative">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-neonBlue/5 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-neonPurple/5 rounded-full blur-[150px] pointer-events-none" />

      <Sidebar 
        sessions={sessions} 
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={handleNewChat}
        onLogout={onLogout}
        user={user}
        refreshSessions={fetchSessions}
      />
      <main className="flex-1 flex flex-col relative z-10">
        {activeSessionId ? (
          <ChatWindow sessionId={activeSessionId} onUpdateTitle={fetchSessions} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-xl mb-4">No active session</p>
              <button 
                onClick={handleNewChat}
                className="px-6 py-2 rounded-xl bg-white/5 border border-white/10 hover:border-neonBlue hover:text-neonBlue transition-all"
              >
                Start a new chat
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ChatPage;
