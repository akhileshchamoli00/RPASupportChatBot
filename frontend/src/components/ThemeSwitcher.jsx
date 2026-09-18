import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const ThemeSwitcher = () => {
  const { theme, setTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="flex items-center bg-slate-200/80 dark:bg-[#070e1b] p-1 rounded-xl border border-slate-300/80 dark:border-white/10 shadow-sm dark:shadow-[0_2px_10px_rgba(0,0,0,0.3)] transition-colors duration-200">
      <button
        type="button"
        onClick={() => setTheme('light')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
          !isDark
            ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-[0_0_12px_rgba(245,158,11,0.35)] border border-amber-300/50'
            : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
        }`}
        title="Switch to Light Theme"
        aria-label="Switch to Light Theme"
      >
        <Sun className={`w-3.5 h-3.5 ${!isDark ? 'text-amber-100 animate-spin-slow' : 'text-gray-400'}`} />
        <span className="tracking-wide">Light</span>
      </button>

      <button
        type="button"
        onClick={() => setTheme('dark')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
          isDark
            ? 'bg-gradient-to-r from-blue-600/90 to-cyan-600/90 text-white shadow-[0_0_12px_rgba(0,210,255,0.35)] border border-cyan-400/40'
            : 'text-slate-600 hover:text-slate-900 hover:bg-black/5 border border-transparent'
        }`}
        title="Switch to Dark Theme"
        aria-label="Switch to Dark Theme"
      >
        <Moon className={`w-3.5 h-3.5 ${isDark ? 'text-cyan-200' : 'text-slate-500'}`} />
        <span className="tracking-wide">Dark</span>
      </button>
    </div>
  );
};

export default ThemeSwitcher;
