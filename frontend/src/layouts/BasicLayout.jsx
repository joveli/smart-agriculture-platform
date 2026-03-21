/**
 * 管理后台基础布局
 * 侧边栏 + 顶部栏 + 内容区
 */

import { useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  HomeOutlined,
  ExperimentOutlined,
  AppstoreOutlined,
  AlertOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useNavigate, Outlet, useLocation } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/tenants', icon: <TeamOutlined />, label: '租户管理' },
  { key: '/farms', icon: <HomeOutlined />, label: '农场管理' },
  { key: '/greenhouses', icon: <ExperimentOutlined />, label: '温室管理' },
  { key: '/devices', icon: <AppstoreOutlined />, label: '设备管理' },
  { key: '/alerts', icon: <AlertOutlined />, label: '告警管理' },
]

function BasicLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleMenuClick = ({ key }) => navigate(key)
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人信息' },
    { type: 'divider' },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        theme="dark"
        breakpoint="lg"
        collapsedWidth="0"
        width={220}
        style={{ position: 'fixed', left: 0, top: 0, bottom: 0 }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            fontWeight: 'bold',
            letterSpacing: 2,
          }}
        >
          🌾 智慧农业平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      {/* 右侧主区域 */}
      <Layout style={{ marginLeft: 220 }}>
        {/* 顶部栏 */}
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
        >
          <Dropdown
            menu={{
              items: userMenuItems,
              onClick: ({ key }) => key === 'logout' && handleLogout(),
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} src={user?.avatar} />
              <span>{user?.full_name || user?.username || '用户'}</span>
            </Space>
          </Dropdown>
        </Header>

        {/* 内容区 */}
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default BasicLayout
