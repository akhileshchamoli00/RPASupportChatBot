import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../services/api';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

const ChatWindow = ({ sessionId, onUpdateTitle }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchMessages = async () => {
      setLoading(true);
      try {
        const res = await chatAPI.getSession(sessionId);
        setMessages(res.data.messages || []);
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

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;
    
    // Optimistic UI update
    const tempUserMsg = { id: Date.now(), role: 'user', content: text, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const res = await chatAPI.sendMessage(sessionId, text);
      // Replace optimistic message with actual DB messages
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUserMsg.id);
        return [...filtered, res.data.user_message, res.data.ai_message];
      });
      if (messages.length <= 1) {
        onUpdateTitle(); // Triggers a refresh of the sidebar title for new chats
      }
    } catch (err) {
      console.error(err);
      // Handle error (could show a toast here)
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-16 glass border-b border-white/10 flex items-center px-6 sticky top-0 z-10">
        <h3 className="font-medium text-white/90">Support Session</h3>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 scroll-smooth scrollbar-hide">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 rounded-full border-2 border-neonBlue border-t-transparent animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6">
              <span className="text-3xl">👋</span>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Hello, I'm your Dayforce RPA Assistant</h2>
            <p className="text-gray-400">Ask me anything about RPA configurations, troubleshooting, or automation guidelines.</p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6 pb-20">
            {messages.map((msg, index) => (
              <MessageBubble key={msg.id || index} message={msg} />
            ))}
            {sending && (
              <div className="flex gap-4 max-w-[85%] sm:max-w-[75%] mr-auto">
                <div className="w-8 h-8 rounded-xl bg-neonBlue/10 border border-neonBlue/30 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="w-4 h-4 border-2 border-neonBlue border-t-transparent rounded-full animate-spin"></span>
                </div>
                <div className="glass rounded-2xl p-4 border border-white/10 flex items-center gap-1">
                  <span className="w-2 h-2 bg-neonBlue rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-neonBlue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  <span className="w-2 h-2 bg-neonBlue rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-background to-transparent relative z-20">
        <div className="max-w-4xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={sending || loading} />
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
