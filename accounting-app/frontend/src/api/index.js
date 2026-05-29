import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 增加超时时间，智能体响应可能较慢
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ==================== 分类接口 ====================

export const getCategories = (type) => {
  return api.get('/categories', { params: { type } });
};

export const createCategory = (data) => {
  return api.post('/categories', data);
};

// ==================== 账单接口 ====================

export const getTransactions = (params) => {
  return api.get('/transactions', { params });
};

export const createTransaction = (data) => {
  return api.post('/transactions', data);
};

export const deleteTransaction = (id) => {
  return api.delete(`/transactions/${id}`);
};

// ==================== 统计接口 ====================

export const getStatistics = (year) => {
  return api.get('/statistics', { params: { year } });
};

// ==================== 对话接口 ====================

export const getConversations = () => {
  return api.get('/conversations');
};

export const createConversation = (data) => {
  return api.post('/conversations', data);
};

export const deleteConversation = (id) => {
  return api.delete(`/conversations/${id}`);
};

export const updateConversation = (id, data) => {
  return api.patch(`/conversations/${id}`, data);
};

export const getMessages = (conversationId) => {
  return api.get(`/conversations/${conversationId}/messages`);
};

// ==================== 聊天接口 ====================

export const sendMessage = (conversationId, content) => {
  return api.post('/chat', {
    conversation_id: conversationId,
    content: content
  });
};

export const getChatStatus = () => {
  return api.get('/chat/status');
};

// ==================== 语音识别接口 ====================

export const getSTTStatus = () => {
  return api.get('/stt/status');
};

export default api;
