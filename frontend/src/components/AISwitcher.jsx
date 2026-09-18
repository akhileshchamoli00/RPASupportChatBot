import React from 'react';
import { Cpu, Zap, Sparkles } from 'lucide-react';

const AISwitcher = ({ aiProvider, useLocalAI, onToggle }) => {
  // Normalize active provider to 'local', 'groq', or 'chatgpt'
  let active = 'groq';
  if (aiProvider) {
    active = aiProvider.toLowerCase();
  } else if (useLocalAI !== undefined) {
    active = useLocalAI ? 'local' : 'chatgpt';
  }

  return (
    <div className="flex items-center bg-slate-200/80 dark:bg-[#070e1b] p-1 rounded-xl border border-slate-300/80 dark:border-white/10 shadow-sm dark:shadow-[0_2px_10px_rgba(0,0,0,0.3)] transition-colors duration-200">
      {/* Local AI */}
      <button
        type="button"
        onClick={() => onToggle('local')}
        className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
          active === 'local'
            ? 'bg-gradient-to-r from-purple-600/90 to-indigo-600/90 text-white shadow-[0_0_12px_rgba(147,51,234,0.4)] border border-purple-400/40'
            : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-black/5 dark:hover:bg-white/5 border border-transparent'
        }`}
        title="Use Local Ollama AI (Llama 3.1:8B) — Private & On-Device"
      >
        <Cpu className={`w-3.5 h-3.5 ${active === 'local' ? 'text-purple-200' : 'text-purple-600 dark:text-purple-400/70'}`} />
        <span className="tracking-wide">Local AI</span>
        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${active === 'local' ? 'bg-black/30 text-purple-200' : 'bg-black/5 dark:bg-white/5 text-slate-500 dark:text-gray-400'}`}>
          3.1:8B
        </span>
      </button>

      {/* Groq Cloud LPU */}
      <button
        type="button"
        onClick={() => onToggle('groq')}
        className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
          active === 'groq'
            ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-[0_0_14px_rgba(245,158,11,0.45)] border border-amber-300/60'
            : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-black/5 dark:hover:bg-white/5 border border-transparent'
        }`}
        title="Use Groq Cloud LPU (Ultra-Fast 27B / 70B) — Lightning-Fast Cloud Inference"
      >
        <Zap className={`w-3.5 h-3.5 ${active === 'groq' ? 'text-amber-100 fill-amber-200/50 animate-pulse' : 'text-orange-500 dark:text-amber-400/70'}`} />
        <span className="tracking-wide">Groq</span>
        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${active === 'groq' ? 'bg-black/30 text-amber-100' : 'bg-black/5 dark:bg-white/5 text-slate-500 dark:text-gray-400'}`}>
          Fast LPU
        </span>
      </button>

      {/* Cloud ChatGPT */}
      <button
        type="button"
        onClick={() => onToggle('chatgpt')}
        className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
          active === 'chatgpt'
            ? 'bg-gradient-to-r from-emerald-600/90 to-teal-600/90 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)] border border-emerald-400/40'
            : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-black/5 dark:hover:bg-white/5 border border-transparent'
        }`}
        title="Use Cloud ChatGPT (OpenAI GPT-4o-mini) — Fast Cloud Intelligence"
      >
        <Sparkles className={`w-3.5 h-3.5 ${active === 'chatgpt' ? 'text-emerald-200' : 'text-emerald-600 dark:text-emerald-400/70'}`} />
        <span className="tracking-wide">ChatGPT</span>
        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${active === 'chatgpt' ? 'bg-black/30 text-emerald-200' : 'bg-black/5 dark:bg-white/5 text-slate-500 dark:text-gray-400'}`}>
          GPT-4o
        </span>
      </button>
    </div>
  );
};

export default AISwitcher;

