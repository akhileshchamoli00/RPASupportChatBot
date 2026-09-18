import React, { useState, useEffect, useRef } from 'react';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { chatAPI } from '../services/api';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import AISwitcher from './AISwitcher';
import ThemeSwitcher from './ThemeSwitcher';

const ChatWindow = ({ sessionId, onUpdateTitle, sidebarOpen, onToggleSidebar }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [automation, setAutomation] = useState(null);
  const [aiProvider, setAiProvider] = useState(() => {
    const saved = localStorage.getItem('ai_provider');
    if (saved) return saved;
    const legacyLocal = localStorage.getItem('use_local_ai');
    if (legacyLocal !== null) return legacyLocal === 'true' ? 'local' : 'chatgpt';
    return 'groq';
  });
  const scrollRef = useRef(null);

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

  useEffect(() => {
    const fetchMessages = async () => {
      setLoading(true);
      try {
        const res = await chatAPI.getSession(sessionId);
        const msgs = res.data.messages || [];
        setMessages(msgs);
        setAutomation(res.data.automation || null);

        // If the last message is from the user, auto-resume generation to recover from page reloads
        if (msgs.length > 0 && msgs[msgs.length - 1].role === 'user') {
          setSending(true);
          try {
            const resumeRes = await chatAPI.resumeSession(sessionId);
            const resumedMsg = {
              ...resumeRes.data.ai_message,
              sources: resumeRes.data.sources || resumeRes.data.ai_message?.sources || [],
              prompt_tokens: resumeRes.data.ai_message?.prompt_tokens ?? resumeRes.data.token_usage?.prompt_tokens,
              completion_tokens: resumeRes.data.ai_message?.completion_tokens ?? resumeRes.data.token_usage?.completion_tokens,
              total_tokens: resumeRes.data.ai_message?.total_tokens ?? resumeRes.data.token_usage?.total_tokens,
              model_used: resumeRes.data.ai_message?.model_used ?? resumeRes.data.token_usage?.model,
            };
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last && last.role === 'user') {
                return [...prev, resumedMsg];
              }
              return prev;
            });
          } catch (resumeErr) {
            console.error('Failed to resume session:', resumeErr);
          } finally {
            setSending(false);
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (sessionId) fetchMessages();
  }, [sessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, sending]);

  const handleSelectAutomation = async (automationType) => {
    // Optimistically update the UI to hide buttons and show the selected workspace badge instantly
    const workspaceNames = {
      ROE: "Record of Employment (ROE)",
      Overpayment: "Overpayment Support",
      SyncPay: "SyncPay Support",
      "Monthly Hourly Update": "Monthly Hourly Update (MHU)",
      "Invoice Supplimental Details": "Invoice Supplemental Details (ISD)",
      Infrastructure: "Infrastructure Support",
      General: "General Support"
    };
    const selectedName = workspaceNames[automationType] || automationType;
    
    setMessages(prev => {
      if (prev.length === 0) return prev;
      const copy = [...prev];
      const last = copy[copy.length - 1];
      if (last && last.role === 'assistant' && last.content.startsWith('[AUTOMATION_SELECT]')) {
        copy[copy.length - 1] = { ...last, content: `[AUTOMATION_SELECTED] ${selectedName}` };
      }
      return copy;
    });

    setSending(true);
    try {
      await chatAPI.selectAutomation(sessionId, automationType, aiProvider);
      // Reload history to show the actual RAG response
      const historyRes = await chatAPI.getSession(sessionId);
      setMessages(historyRes.data.messages || []);
      setAutomation(automationType === 'General' ? null : automationType);
      onUpdateTitle();
    } catch (err) {
      console.error(err);
      // Rollback on failure
      const historyRes = await chatAPI.getSession(sessionId);
      setMessages(historyRes.data.messages || []);
    } finally {
      setSending(false);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    const tempUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const res = await chatAPI.sendMessage(sessionId, text, aiProvider);
      const incomingAiMsg = {
        ...res.data.ai_message,
        sources: res.data.sources || res.data.ai_message?.sources || [],
        prompt_tokens: res.data.ai_message?.prompt_tokens ?? res.data.token_usage?.prompt_tokens,
        completion_tokens: res.data.ai_message?.completion_tokens ?? res.data.token_usage?.completion_tokens,
        total_tokens: res.data.ai_message?.total_tokens ?? res.data.token_usage?.total_tokens,
        model_used: res.data.ai_message?.model_used ?? res.data.token_usage?.model,
      };
      setMessages(prev => [...prev, incomingAiMsg]);
      onUpdateTitle();
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ Error communicating with AI server: ${err.response?.data?.detail || err.message}`,
        created_at: new Date().toISOString()
      }]);
    } finally {
      setSending(false);
    }
  };

  const getWelcomeContent = () => {
    switch (automation) {
      case 'ROE':
        return {
          desc: 'Ask me anything about RPA workflows, troubleshooting guidelines, or specific Record of Employment (ROE) process documentation.',
          suggestions: [
            { title: 'Explore ROE Process', text: 'How is the ROE process structured?' },
            { title: 'Credentials Security', text: 'Are Dayforce credentials encrypted?' }
          ]
        };
      case 'Overpayment':
        return {
          desc: 'Ask me anything about RPA workflows, troubleshooting guidelines, or specific Overpayment process documentation.',
          suggestions: [
            { title: 'Overpayment Process', text: 'How is the Lifeworks Overpayment process structured?' },
            { title: 'IT Operations Support', text: 'What are standard support hours for Overpayments?' }
          ]
        };
      case 'SyncPay':
        return {
          desc: 'Ask me anything about RPA workflows, troubleshooting guidelines, or specific SyncPay process documentation.',
          suggestions: [
            { title: 'SyncPay Process', text: 'How is the SyncPay AMEX process structured?' },
            { title: 'Managed Services Planning', text: 'What is the support planning for SyncPay managed services?' }
          ]
        };
      default:
        return {
          desc: 'Ask me anything about RPA workflows, troubleshooting guidelines, or general automation documentation.',
          suggestions: [
            { title: 'Explore ROE Process', text: 'How is the ROE process structured?' },
            { title: 'SyncPay Process', text: 'How is the SyncPay AMEX process structured?' }
          ]
        };
    }
  };

  const welcomeContent = getWelcomeContent();

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-[#040911]/30 transition-colors duration-200">
      {/* Header */}
      <header className="h-16 bg-white/80 dark:bg-[#040911]/80 backdrop-blur-xl border-b border-slate-200/80 dark:border-white/10 flex items-center justify-between px-6 sticky top-0 z-10 transition-colors duration-200">
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-white/5 rounded-lg transition-colors cursor-pointer flex items-center justify-center border-0"
            title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            {sidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-dayforce-blue dark:bg-dayforce-cyan shadow-[0_0_10px_rgba(0,98,255,0.4)] dark:shadow-[0_0_10px_rgba(0,210,255,0.6)] animate-pulse"></div>
            <h3 className="font-bold text-slate-800 dark:text-white/90 text-xs tracking-wider uppercase">RPA Support Session</h3>
            {automation && (
              <span className="text-[9px] bg-blue-50 text-blue-600 border border-blue-200 dark:bg-dayforce-blue/20 dark:text-dayforce-cyan dark:border-dayforce-blue/40 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider animate-fadeIn">
                {automation}
              </span>
            )}
          </div>
        </div>

        {/* Theme and AI Provider Switchers */}
        <div className="flex items-center gap-2.5">
          <ThemeSwitcher />
          <AISwitcher aiProvider={aiProvider} onToggle={handleToggleAI} />
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 scroll-smooth custom-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 rounded-full border-2 border-dayforce-blue dark:border-dayforce-cyan border-t-transparent animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto px-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-dayforce-blue/20 to-dayforce-cyan/20 border border-dayforce-blue/30 flex items-center justify-center mb-6 shadow-[0_0_15px_rgba(0,98,255,0.15)]">
              <span className="text-2xl">🤖</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2 tracking-tight font-sans">
              Dayforce Automation <span className="text-dayforce-blue">Atlas</span>
            </h2>
            <p className="text-sm text-slate-600 dark:text-gray-400 mb-8 max-w-md leading-relaxed font-sans">
              {welcomeContent.desc}
            </p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
              {welcomeContent.suggestions.map((sug, idx) => (
                <button 
                  key={idx}
                  onClick={() => handleSendMessage(sug.text)}
                  className="text-left p-3.5 rounded-xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:border-dayforce-blue/50 dark:hover:border-dayforce-cyan/30 hover:bg-blue-50/50 dark:hover:bg-dayforce-blue/5 text-xs text-slate-700 dark:text-gray-300 shadow-sm dark:shadow-none transition-all cursor-pointer hover:-translate-y-0.5"
                >
                  <p className="font-semibold text-slate-900 dark:text-white mb-0.5">{sug.title}</p>
                  <p className="text-[10px] text-slate-500 dark:text-gray-500">"{sug.text}"</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6 pb-20">
            {messages.map((msg, index) => (
              <MessageBubble 
                key={msg.id || index} 
                message={msg} 
                onSelectAutomation={handleSelectAutomation} 
              />
            ))}
            {sending && (
              <div className="flex gap-4 max-w-3xl w-full py-1">
                <div className="w-8 h-8 rounded-full bg-dayforce-blue/15 dark:bg-dayforce-cyan/15 border border-dayforce-blue/30 dark:border-dayforce-cyan/30 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm text-dayforce-blue dark:text-dayforce-cyan">
                  <span className="w-3.5 h-3.5 border-2 border-dayforce-blue dark:border-dayforce-cyan border-t-transparent rounded-full animate-spin"></span>
                </div>
                <div className="bg-transparent text-slate-700 dark:text-gray-100 px-1 py-2.5 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-dayforce-blue dark:bg-dayforce-cyan/60 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-dayforce-blue dark:bg-dayforce-cyan/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  <span className="w-1.5 h-1.5 bg-dayforce-blue dark:bg-dayforce-cyan/60 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-slate-100 via-slate-100/80 to-transparent dark:from-[#040911] dark:via-[#040911]/80 dark:to-transparent relative z-20 transition-colors duration-200">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={sending || loading} />
          <p className="text-[10px] text-slate-500 dark:text-gray-500 mt-2 text-center tracking-wide font-medium">
            Dayforce Automation Atlas may make mistakes. Verify important info.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
