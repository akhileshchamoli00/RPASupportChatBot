import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { authAPI } from '../services/api';
import { Bot, UserRound, ArrowRight } from 'lucide-react';
import FloatingLines from '../components/FloatingLines';

const FLOATING_LINES_WAVES = ["top", "middle", "bottom"];

// Completely isolated, memoized background that never re-renders when typing credentials
const LoginPageBackground = React.memo(() => (
  <div className="absolute inset-0 w-full h-full z-0 pointer-events-none bg-[#040911]">
    <FloatingLines 
      enabledWaves={FLOATING_LINES_WAVES}
      lineCount={8}
      lineDistance={8}
      bendRadius={8}
      bendStrength={-2}
      interactive
      parallax={true}
      animationSpeed={1}
      gradientStart="#0062ff" // Dayforce Royal Blue
      gradientMid="#00d2ff"   // Dayforce Bright Cyan
      gradientEnd="#0036b3"   // Dayforce Dark Blue/Navy
    />
  </div>
));

const LoginPage = ({ onLogin, onLogout }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Ensure dark theme class is applied on login page
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
    const storedUser = localStorage.getItem('user_id');
    if (storedUser) {
      localStorage.removeItem('user_id');
      if (onLogout) {
        onLogout();
      }
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await authAPI.login(userId, password);
        localStorage.setItem('user_id', res.data.user_id);
        onLogin(res.data.user_id);
      } else {
        await authAPI.register(userId, password);
        const res = await authAPI.login(userId, password);
        localStorage.setItem('user_id', res.data.user_id);
        onLogin(res.data.user_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen relative overflow-hidden bg-[#040911]">
      <LoginPageBackground />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="bg-[#050c18]/93 backdrop-blur-xl rounded-3xl p-8 md:p-10 w-full max-w-md relative z-10 border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-full h-20 rounded-xl overflow-hidden flex items-center justify-center relative mb-5 border border-white/10 shadow-[0_4px_25px_rgba(0,98,255,0.15)] bg-[#0062ff]">
            <img 
              src="/dayforce_logo.jpg" 
              alt="Dayforce Logo" 
              className="w-full h-full object-cover scale-[1.7] opacity-95" 
            />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white mt-2">
            Automation <span className="text-dayforce-blue">Atlas</span>
          </h1>
          <p className="text-xs text-gray-300 mt-1.5 text-center font-medium">
            Secure enterprise access to automation knowledge
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5 ml-1 uppercase tracking-wider">
              User ID
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <UserRound className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full bg-black/45 border border-white/15 rounded-xl py-3.5 pl-10 pr-4 text-white placeholder-gray-550 focus:outline-none focus:border-dayforceCyan focus:ring-1 focus:ring-dayforceCyan focus:bg-[#050c18] transition-all text-sm font-medium"
                placeholder="Enter your ID"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5 ml-1 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-black/45 border border-white/15 rounded-xl py-3.5 px-4 text-white placeholder-gray-550 focus:outline-none focus:border-dayforceCyan focus:ring-1 focus:ring-dayforceCyan focus:bg-[#050c18] transition-all text-sm font-medium"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="text-red-400 text-sm text-center bg-red-400/10 py-2 rounded-lg border border-red-400/20"
            >
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-dayforce-blue to-dayforce-cyan hover:opacity-95 active:scale-[0.98] text-white py-3.5 rounded-xl font-semibold flex items-center justify-center transition-all group disabled:opacity-50 cursor-pointer shadow-[0_4px_15px_rgba(0,98,255,0.15)] border-0"
          >
            {loading ? 'Processing...' : isLogin ? 'Initialize Session' : 'Create Access'}
            {!loading && <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setUserId('');
              setPassword('');
              setError('');
            }}
            className="text-xs text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            {isLogin ? "Don't have access? Register" : "Already have access? Login"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
