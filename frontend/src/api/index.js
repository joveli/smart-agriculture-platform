/**
 * API 请求封装
 * 带有 JWT Token 自动注入和统一错误处理
 */

import axios from 'axios'
import { message } from 'antd'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
})

// 请求拦截器：注入 Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：错误处理 + Token 过期处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      } else if (status === 403) {
        message.error('无权限访问')
      } else if (status >= 500) {
        message.error('服务器错误，请稍后重试')
      } else {
        message.error(data?.detail || '请求失败')
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default api

// ============ Auth API ============
export const authApi = {
  login: (username, password) =>
    api.post('/api/v1/auth/login', new URLSearchParams({ username, password }), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }),
  register: (data) =>
    api.post('/api/v1/auth/register', data),
  getMe: () =>
    api.get('/api/v1/auth/me'),
}

// ============ Tenant API ============
export const tenantApi = {
  list: () => api.get('/api/v1/tenants/'),
  get: (id) => api.get(`/api/v1/tenants/${id}`),
  create: (data) => api.post('/api/v1/tenants/', data),
  update: (id, data) => api.patch(`/api/v1/tenants/${id}`, data),
  delete: (id) => api.delete(`/api/v1/tenants/${id}`),
}

// ============ Farm API ============
export const farmApi = {
  list: (params) => api.get('/api/v1/farms/', { params }),
  get: (id) => api.get(`/api/v1/farms/${id}`),
  create: (data) => api.post('/api/v1/farms/', data),
  update: (id, data) => api.patch(`/api/v1/farms/${id}`, data),
  delete: (id) => api.delete(`/api/v1/farms/${id}`),
}

// ============ Greenhouse API ============
export const greenhouseApi = {
  list: (params) => api.get('/api/v1/greenhouses/', { params }),
  get: (id) => api.get(`/api/v1/greenhouses/${id}`),
  create: (data) => api.post('/api/v1/greenhouses/', data),
  update: (id, data) => api.patch(`/api/v1/greenhouses/${id}`, data),
  delete: (id) => api.delete(`/api/v1/greenhouses/${id}`),
}

// ============ Device API ============
export const deviceApi = {
  list: (params) => api.get('/api/v1/devices/', { params }),
  get: (id) => api.get(`/api/v1/devices/${id}`),
  create: (data) => api.post('/api/v1/devices/', data),
  update: (id, data) => api.patch(`/api/v1/devices/${id}`, data),
  delete: (id) => api.delete(`/api/v1/devices/${id}`),
  sendCommand: (id, data) => api.post(`/api/v1/devices/${id}/command`, data),
}

// ============ Alert API ============
export const alertApi = {
  listRules: (params) => api.get('/api/v1/alerts/rules', { params }),
  createRule: (data) => api.post('/api/v1/alerts/rules', data),
  updateRule: (id, data) => api.patch(`/api/v1/alerts/rules/${id}`, data),
  deleteRule: (id) => api.delete(`/api/v1/alerts/rules/${id}`),
  list: (params) => api.get('/api/v1/alerts/', { params }),
  acknowledge: (id, data) => api.post(`/api/v1/alerts/${id}/acknowledge`, data),
  resolve: (id) => api.post(`/api/v1/alerts/${id}/resolve`),
}

// ============ Admin API ============
export const adminApi = {
  auditLogs: (params) => api.get('/api/v1/admin/audit-logs', { params }),
  tenantStats: () => api.get('/api/v1/admin/tenants/stats'),
}

// ============ Contract API ============
export const contractApi = {
  list: (params) => api.get('/api/v1/contracts/', { params }),
  get: (id) => api.get(`/api/v1/contracts/${id}`),
  create: (data) => api.post('/api/v1/contracts/', data),
  update: (id, data) => api.patch(`/api/v1/contracts/${id}`, data),
  delete: (id) => api.delete(`/api/v1/contracts/${id}`),
};

// ============ Payment API ============
export const paymentApi = {
  list: (params) => api.get('/api/v1/payments/', { params }),
  get: (id) => api.get(`/api/v1/payments/${id}`),
  create: (data) => api.post('/api/v1/payments/', data),
  complete: (id) => api.post(`/api/v1/payments/${id}/complete`),
  stats: () => api.get('/api/v1/payments/stats'),
};
