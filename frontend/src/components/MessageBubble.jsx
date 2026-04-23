import React from 'react';
import { motion } from 'framer-motion';
import { Bot, UserRound } from 'lucide-react';

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-4 w-full ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div 
        className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 ${
          isUser 
            ? 'bg-white/10 border border-white/20' 
            : 'bg-neonBlue/10 border border-neonBlue/30 shadow-[0_0_10px_rgba(0,243,255,0.2)]'
        }`}
      >
        {isUser ? (
          <UserRound className="w-4 h-4 text-white/80" />
        ) : (
          <Bot className="w-4 h-4 text-neonBlue" />
        )}
      </div>

      <div 
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 leading-relaxed ${
          isUser 
            ? 'bg-white/10 border border-white/10 text-white rounded-tr-sm' 
            : 'glass border border-white/10 text-gray-200 rounded-tl-sm'
        }`}
      >
        <div className="whitespace-pre-wrap font-sans text-[15px]">
          {message.content}
        </div>
        <div className={`text-[10px] mt-2 opacity-50 ${isUser ? 'text-right text-gray-300' : 'text-left text-neonBlue'}`}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
