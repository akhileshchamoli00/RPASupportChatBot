import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const authAPI = {
  register: (user_id, password) => api.post('/auth/register', { user_id, password }),
  login: (user_id, password) => api.post('/auth/login', { user_id, password }),
};

export const chatAPI = {
  createSession: (title) => api.post('/chat/sessions', { title }),
  getSessions: () => api.get('/chat/sessions'),
  getSession: (session_id) => api.get(`/chat/sessions/${session_id}`),
  renameSession: (session_id, title) => api.put(`/chat/sessions/${session_id}/title`, { title }),
  deleteSession: (session_id) => api.delete(`/chat/sessions/${session_id}`),
  sendMessage: (session_id, message) => api.post(`/chat/sessions/${session_id}/message`, { message }),
};

export default api;
