/**
 * 登录页面
 */

import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

function Login() {
  const navigate = useNavigate()
  const { login, loading } = useAuthStore()
  const [form] = Form.useForm()

  const handleSubmit = async (values) => {
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/dashboard')
    } catch (err) {
      const detail = err.response?.data?.detail || '登录失败'
      message.error(detail)
    }
  }

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        title={<span style={{ fontSize: 20, fontWeight: 'bold' }}>🌾 智慧农业平台</span>}
        style={{ width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }}
        headStyle={{ textAlign: 'center', borderBottom: 'none' }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
