import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="relative flex items-end gap-2 p-2 rounded-3xl bg-white/95 dark:bg-[#0c1322]/80 backdrop-blur-xl border border-slate-200/90 dark:border-white/10 shadow-lg dark:shadow-none focus-within:border-dayforce-blue/50 dark:focus-within:border-dayforce-cyan/40 focus-within:shadow-[0_0_25px_rgba(0,98,255,0.12)] dark:focus-within:shadow-[0_0_20px_rgba(0,210,255,0.08)] transition-all"
    >
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Message Dayforce Automation Atlas..."
        disabled={disabled}
        className="w-full bg-transparent text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-gray-500 py-3.5 px-5 focus:outline-none resize-none max-h-[120px] scrollbar-hide text-[15px] leading-relaxed font-sans"
        rows={1}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className={`p-2.5 rounded-full flex-shrink-0 transition-all ${
          text.trim() && !disabled
            ? 'bg-dayforce-blue hover:bg-dayforce-dark-blue text-white dark:bg-white dark:text-black dark:hover:bg-white/90 shadow-md scale-100 active:scale-95 cursor-pointer'
            : 'bg-slate-100 text-slate-300 dark:bg-white/10 dark:text-gray-500 cursor-not-allowed'
        }`}
      >
        <Send className="w-4 h-4" />
      </button>
    </form>
  );
};

export default ChatInput;
