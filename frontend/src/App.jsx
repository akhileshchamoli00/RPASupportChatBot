import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const justLoggedInRef = useRef(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (storedUser) {
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  const handleLogin = (userId) => {
    localStorage.setItem('user_id', userId);
    justLoggedInRef.current = true;
    setUser(userId);
    navigate('/chat');
  };

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    setUser(null);
  };

  // Monitor URL back-navigations to /login and clear session safely
  useEffect(() => {
    if (location.pathname === '/login' && user) {
      if (justLoggedInRef.current) {
        justLoggedInRef.current = false;
        return;
      }
      handleLogout();
    }
  }, [location.pathname, user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-[#040911] text-dayforce-blue dark:text-dayforce-cyan">
        <div className="w-8 h-8 rounded-full border-2 border-dayforce-blue dark:border-dayforce-cyan border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          user ? <Navigate to="/chat" replace /> : <LoginPage onLogin={handleLogin} onLogout={handleLogout} />
        } 
      />
      <Route 
        path="/chat" 
        element={
          user ? <ChatPage user={user} onLogout={handleLogout} /> : <Navigate to="/login" replace />
        } 
      />
      <Route 
        path="/chat/:sessionId" 
        element={
          user ? <ChatPage user={user} onLogout={handleLogout} /> : <Navigate to="/login" replace />
        } 
      />
      <Route 
        path="*" 
        element={<Navigate to={user ? "/chat" : "/login"} replace />} 
      />
    </Routes>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-background text-slate-900 dark:text-gray-200 transition-colors duration-200">
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </div>
  );
}

export default App;
