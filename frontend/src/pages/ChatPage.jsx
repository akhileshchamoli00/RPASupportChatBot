import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ThemeSwitcher from '../components/ThemeSwitcher';
import AISwitcher from '../components/AISwitcher';
import { chatAPI } from '../services/api';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

const ChatPage = ({ user, onLogout }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [aiProvider, setAiProvider] = useState(() => {
    return localStorage.getItem('ai_provider') || 'groq';
  });

  useEffect(() => {
    chatAPI.getSettings().then(res => {
      if (res.data && res.data.ai_provider) {
        setAiProvider(res.data.ai_provider);
        localStorage.setItem('ai_provider', res.data.ai_provider);
        localStorage.setItem('use_local_ai', res.data.ai_provider === 'local' ? 'true' : 'false');
      }
    }).catch(err => console.error('Failed to get AI settings:', err));
  }, []);

  const handleToggleAI = async (val) => {
    setAiProvider(val);
    localStorage.setItem('ai_provider', val);
    localStorage.setItem('use_local_ai', val === 'local' ? 'true' : 'false');
    try {
      await chatAPI.updateSettings(val);
    } catch (err) {
      console.error('Failed to update AI provider setting:', err);
    }
  };

  
  const { sessionId } = useParams();
  const navigate = useNavigate();

  // Parse session ID from URL route param
  const activeSessionId = sessionId || null;

  const fetchSessions = async () => {
    try {
      const res = await chatAPI.getSessions();
      setSessions(res.data);
      
      // If a session ID is in the URL but doesn't exist in the database, redirect to base chat
      if (sessionId) {
        const exists = res.data.some(s => s.id === sessionId);
        if (!exists) {
          navigate('/chat');
        }
      }
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [user]);

  const handleNewChat = async () => {
    try {
      const res = await chatAPI.createSession('New Chat', null, user);
      setSessions([res.data, ...sessions]);
      navigate(`/chat/${res.data.id}`);
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  const handleSelectSession = (id) => {
    navigate(`/chat/${id}`);
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-background overflow-hidden relative transition-colors duration-200">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-dayforce-blue/5 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-dayforce-cyan/5 rounded-full blur-[150px] pointer-events-none" />

      <Sidebar 
        sessions={sessions} 
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onLogout={onLogout}
        user={user}
        refreshSessions={fetchSessions}
        isOpen={sidebarOpen}
      />
      <main className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {activeSessionId ? (
          <ChatWindow 
            sessionId={activeSessionId} 
            onUpdateTitle={fetchSessions} 
            sidebarOpen={sidebarOpen}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            aiProvider={aiProvider}
            onToggleAI={handleToggleAI}
          />
        ) : (
          <div className="flex-1 flex flex-col h-full bg-slate-50/50 dark:bg-[#040911]/30 transition-colors duration-200">
            {/* Top Bar for empty state */}
            <div className="h-16 px-6 flex items-center justify-between border-b border-slate-200/80 dark:border-white/10 bg-white/70 dark:bg-[#040911]/80 backdrop-blur-xl transition-colors duration-200">
              <button 
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-white/5 rounded-lg transition-colors cursor-pointer"
                title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              >
                {sidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
              </button>
              <div className="flex items-center gap-2.5">
                <ThemeSwitcher />
                <AISwitcher aiProvider={aiProvider} onToggle={handleToggleAI} />
              </div>
            </div>


            <div className="flex-1 flex flex-col items-center justify-center text-center max-w-lg mx-auto px-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-dayforce-blue/20 to-dayforce-cyan/20 border border-dayforce-blue/30 flex items-center justify-center mb-6 shadow-[0_0_20px_rgba(0,98,255,0.15)] animate-pulse">
                <span className="text-3xl">🤖</span>
              </div>
              <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white mb-2 tracking-tight">
                Dayforce Automation <span className="text-dayforce-blue">Atlas</span>
              </h2>
              <p className="text-sm text-slate-600 dark:text-gray-400 mb-8 max-w-md leading-relaxed">
                Welcome back! Select an existing support session from the sidebar, or create a new workspace below to target specific documents.
              </p>
              <button 
                onClick={handleNewChat}
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-dayforce-blue to-dayforce-cyan hover:opacity-95 active:scale-[0.98] text-white font-semibold shadow-[0_4px_15px_rgba(0,98,255,0.2)] cursor-pointer transition-all"
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
