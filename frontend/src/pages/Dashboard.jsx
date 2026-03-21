/**
 * 仪表盘页面
 * 平台总览：租户数、温室数、设备状态、告警统计
 */

import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin } from 'antd'
import {
  TeamOutlined,
  ExperimentOutlined,
  AppstoreOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { tenantApi, greenhouseApi, deviceApi, alertApi } from '../api'

function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    tenantCount: 0,
    greenhouseCount: 0,
    deviceOnline: 0,
    deviceTotal: 0,
    alertCritical: 0,
    alertWarning: 0,
    alertPending: 0,
  })
  const [recentAlerts, setRecentAlerts] = useState([])
  const [recentDevices, setRecentDevices] = useState([])

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const [tenantRes, ghRes, deviceRes, alertRes] = await Promise.all([
        tenantApi.list().catch(() => ({ data: [] })),
        greenhouseApi.list().catch(() => ({ data: [] })),
        deviceApi.list().catch(() => ({ data: [] })),
        alertApi.list({ limit: 5 }).catch(() => ({ data: [] })),
      ])

      const devices = deviceRes.data || []
      const alerts = alertRes.data || []

      setStats({
        tenantCount: (tenantRes.data || []).length,
        greenhouseCount: (ghRes.data || []).length,
        deviceOnline: devices.filter((d) => d.status === 'online').length,
        deviceTotal: devices.length,
        alertCritical: alerts.filter((a) => a.level === 'critical').length,
        alertWarning: alerts.filter((a) => a.level === 'warning').length,
        alertPending: alerts.filter((a) => a.status === 'pending').length,
      })
      setRecentAlerts(alerts.slice(0, 5))
      setRecentDevices(devices.slice(0, 5))
    } catch (err) {
      console.error('Dashboard load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const alertColumns = [
    { title: '类型', dataIndex: 'alert_type', key: 'alert_type' },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level) => (
        <Tag color={level === 'critical' ? 'red' : level === 'warning' ? 'orange' : 'blue'}>
          {level}
        </Tag>
      ),
    },
    { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s) => (
        <Tag icon={s === 'pending' ? <ClockCircleOutlined /> : <CheckCircleOutlined />} color={s === 'pending' ? 'warning' : 'success'}>
          {s}
        </Tag>
      ),
    },
  ]

  const mockChartData = [
    { time: '00:00', temp: 22, humidity: 65 },
    { time: '04:00', temp: 20, humidity: 70 },
    { time: '08:00', temp: 24, humidity: 60 },
    { time: '12:00', temp: 28, humidity: 55 },
    { time: '16:00', temp: 27, humidity: 58 },
    { time: '20:00', temp: 25, humidity: 62 },
  ]

  return (
    <Spin spinning={loading}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>仪表盘</h2>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="租户数量"
              value={stats.tenantCount}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="温室数量"
              value={stats.greenhouseCount}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="设备在线"
              value={`${stats.deviceOnline} / ${stats.deviceTotal}`}
              prefix={<AppstoreOutlined />}
              valueStyle={{ color: stats.deviceOnline > 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待处理告警"
              value={stats.alertPending}
              prefix={<AlertOutlined />}
              valueStyle={{ color: stats.alertPending > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="温室温湿度趋势（示例）">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={mockChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line yAxisId="left" type="monotone" dataKey="temp" stroke="#ff4d4f" name="温度 (°C)" />
                <Line yAxisId="right" type="monotone" dataKey="humidity" stroke="#1890ff" name="湿度 (%)" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="告警级别分布">
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="严重"
                  value={stats.alertCritical}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="警告"
                  value={stats.alertWarning}
                  prefix={<AlertOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="待处理"
                  value={stats.alertPending}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 最近告警 */}
      <Card title="最近告警" style={{ marginTop: 24 }}>
        <Table
          columns={alertColumns}
          dataSource={recentAlerts}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </Spin>
  )
}

export default Dashboard
