import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { authAPI } from '../services/api';
import { Bot, UserRound, ArrowRight } from 'lucide-react';

const LoginPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await authAPI.login(userId, password);
        onLogin(res.data.user_id);
      } else {
        await authAPI.register(userId, password);
        const res = await authAPI.login(userId, password);
        onLogin(res.data.user_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen relative overflow-hidden bg-background">
      {/* Background glow elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neonBlue/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-neonPurple/20 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="glass rounded-2xl p-8 w-full max-w-md relative z-10 neon-border"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 neon-text" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Dayforce <span className="neon-text">Support</span>
          </h1>
          <p className="text-sm text-gray-400 mt-2">
            Sign in to access your RPA assistant
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1 ml-1 uppercase tracking-wider">
              User ID
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <UserRound className="h-4 w-4 text-gray-500" />
              </div>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-neonBlue focus:ring-1 focus:ring-neonBlue transition-all"
                placeholder="Enter your ID"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1 ml-1 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white placeholder-gray-500 focus:outline-none focus:border-neonBlue focus:ring-1 focus:ring-neonBlue transition-all"
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
            className="w-full bg-neonBlue/10 hover:bg-neonBlue/20 text-neonBlue border border-neonBlue/50 hover:border-neonBlue py-3 rounded-xl font-medium flex items-center justify-center transition-all group disabled:opacity-50"
          >
            {loading ? 'Processing...' : isLogin ? 'Initialize Session' : 'Create Access'}
            {!loading && <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            {isLogin ? "Don't have access? Register" : "Already have access? Login"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
