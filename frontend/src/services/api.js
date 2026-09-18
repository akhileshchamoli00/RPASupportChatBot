import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '5173' ? 'http://localhost:8000/api' : '/api'),
});

// Automatically inject logged-in user identity header to all outgoing API requests
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('user_id');
  if (userId) {
    config.headers['X-User-Id'] = userId;
  }
  return config;
});

export const authAPI = {
  register: (user_id, password) => api.post('/auth/register', { user_id, password }),
  login: (user_id, password) => api.post('/auth/login', { user_id, password }),
};

export const chatAPI = {
  createSession: (title, automation, user_id = null) => {
    const currentUserId = user_id || localStorage.getItem('user_id');
    return api.post('/chat/sessions', { title, automation, user_id: currentUserId });
  },
  getSessions: () => api.get('/chat/sessions'),
  getSession: (session_id) => api.get(`/chat/sessions/${session_id}`),
  renameSession: (session_id, title) => api.put(`/chat/sessions/${session_id}/title`, { title }),
  deleteSession: (session_id) => api.delete(`/chat/sessions/${session_id}`),
  sendMessage: (session_id, message, ai_provider = null) => {
    const isLocal = typeof ai_provider === 'boolean' ? ai_provider : (ai_provider === 'local');
    const providerStr = typeof ai_provider === 'string' ? ai_provider : (ai_provider ? 'local' : 'chatgpt');
    return api.post(`/chat/sessions/${session_id}/message`, {
      message,
      ai_provider: providerStr,
      use_local_ai: isLocal,
    });
  },
  resumeSession: (session_id) => api.post(`/chat/sessions/${session_id}/resume`),
  selectAutomation: (session_id, automation, ai_provider = null) => {
    const isLocal = typeof ai_provider === 'boolean' ? ai_provider : (ai_provider === 'local');
    const providerStr = typeof ai_provider === 'string' ? ai_provider : (ai_provider ? 'local' : 'chatgpt');
    return api.post(`/chat/sessions/${session_id}/select_automation`, {
      automation,
      ai_provider: providerStr,
      use_local_ai: isLocal,
    });
  },
  getSettings: () => api.get('/chat/settings'),
  updateSettings: (ai_provider) => {
    const isLocal = typeof ai_provider === 'boolean' ? ai_provider : (ai_provider === 'local');
    const providerStr = typeof ai_provider === 'string' ? ai_provider : (ai_provider ? 'local' : 'chatgpt');
    return api.post('/chat/settings', {
      ai_provider: providerStr,
      use_local_ai: isLocal,
    });
  },
};

export default api;
