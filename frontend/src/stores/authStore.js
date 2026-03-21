/**
 * 认证状态管理
 * 使用 Zustand 管理全局登录状态
 */

import { create } from 'zustand'
import { authApi } from '../api'

const useAuthStore = create((set, get) => ({
  token: localStorage.getItem('access_token') || null,
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  loading: false,

  // 登录
  login: async (username, password) => {
    set({ loading: true })
    try {
      const res = await authApi.login(username, password)
      const { access_token } = res.data
      localStorage.setItem('access_token', access_token)
      
      // 获取用户信息
      const userRes = await authApi.getMe()
      const user = userRes.data
      localStorage.setItem('user', JSON.stringify(user))
      
      set({ token: access_token, user, loading: false })
      return true
    } catch (err) {
      set({ loading: false })
      throw err
    }
  },

  // 登出
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  },

  // 是否有 Token
  isAuthenticated: () => !!get().token,
}))

export default useAuthStore
