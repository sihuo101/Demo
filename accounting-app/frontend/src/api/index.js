import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
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

export default api;
