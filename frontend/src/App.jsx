/**
 * App 根组件
 * 路由配置
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import BasicLayout from './layouts/BasicLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TenantList from './pages/TenantList'
import FarmList from './pages/FarmList'
import GreenhouseList from './pages/GreenhouseList'
import GreenhouseDetail from './pages/GreenhouseDetail'
import DeviceList from './pages/DeviceList'
import AlertList from './pages/AlertList'
import ContractList from './pages/ContractList'
import PaymentList from './pages/PaymentList'
import useAuthStore from './stores/authStore'

// 受保护的路由包装器
const ProtectedRoute = ({ children }) => {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <BasicLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="tenants" element={<TenantList />} />
        <Route path="farms" element={<FarmList />} />
        <Route path="greenhouses" element={<GreenhouseList />} />
        <Route path="greenhouses/:id" element={<GreenhouseDetail />} />
        <Route path="devices" element={<DeviceList />} />
        <Route path="alerts" element={<AlertList />} />
        <Route path="contracts" element={<ContractList />} />
        <Route path="payments" element={<PaymentList />} />
      </Route>
    </Routes>
  )
}

export default App
