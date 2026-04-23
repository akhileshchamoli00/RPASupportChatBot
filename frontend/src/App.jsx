import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user_id');
    if (storedUser) {
      setUser(storedUser);
    }
  }, []);

  const handleLogin = (userId) => {
    localStorage.setItem('user_id', userId);
    setUser(userId);
  };

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    setUser(null);
  };

  return (
    <div className="min-h-screen bg-background text-gray-200">
      {user ? (
        <ChatPage user={user} onLogout={handleLogout} />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
