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
      className="relative flex items-end gap-2 p-2 rounded-2xl glass border border-white/10 focus-within:border-neonBlue/50 focus-within:shadow-[0_0_15px_rgba(0,243,255,0.15)] transition-all"
    >
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask something about Dayforce RPA..."
        disabled={disabled}
        className="w-full bg-transparent text-white placeholder-gray-500 py-3 px-4 focus:outline-none resize-none max-h-[120px] scrollbar-hide text-[15px]"
        rows={1}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className={`p-3 rounded-xl flex-shrink-0 transition-all ${
          text.trim() && !disabled
            ? 'bg-neonBlue/20 text-neonBlue border border-neonBlue hover:bg-neonBlue hover:text-black hover:shadow-[0_0_15px_rgba(0,243,255,0.5)]'
            : 'bg-white/5 text-gray-500 border border-transparent'
        }`}
      >
        <Send className="w-5 h-5" />
      </button>
    </form>
  );
};

export default ChatInput;
