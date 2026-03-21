/**
 * 温室详情页面
 * 实时数据展示 + 历史数据图表
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Statistic, Button, Spin, Descriptions, Tag } from 'antd'
import { ArrowLeftOutlined, ThermometerOutlined, DropletOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { greenhouseApi } from '../api'

function GreenhouseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [greenhouse, setGreenhouse] = useState(null)
  const [loading, setLoading] = useState(true)

  // 模拟实时数据（实际应从 WebSocket 或轮询获取）
  const [sensorData, setSensorData] = useState([])

  useEffect(() => {
    loadData()
  }, [id])

  useEffect(() => {
    // 模拟 5 秒更新一次实时数据
    const interval = setInterval(() => {
      const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      setSensorData(prev => {
        const newPoint = {
          time: now,
          temperature: +(20 + Math.random() * 10).toFixed(1),
          humidity: +(55 + Math.random() * 20).toFixed(1),
          light: +(3000 + Math.random() * 5000).toFixed(0),
          co2: +(400 + Math.random() * 200).toFixed(0),
        }
        const updated = [...prev.slice(-11), newPoint]
        return updated
      })
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await greenhouseApi.get(id)
      setGreenhouse(res.data)
    } catch {}
    setLoading(false)
  }

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />

  if (!greenhouse) return <div>温室不存在</div>

  const latest = sensorData[sensorData.length - 1] || {}

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/greenhouses')}>返回</Button>
        <h2 style={{ margin: 0 }}>{greenhouse.name}</h2>
        <Tag color={greenhouse.status === 'active' ? 'green' : 'orange'}>{greenhouse.status}</Tag>
      </div>

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: 24 }}>
        <Descriptions column={3}>
          <Descriptions.Item label="温室名称">{greenhouse.name}</Descriptions.Item>
          <Descriptions.Item label="面积">{greenhouse.area_sqm} m²</Descriptions.Item>
          <Descriptions.Item label="位置">{greenhouse.location || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">{greenhouse.status}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{greenhouse.created_at ? new Date(greenhouse.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 实时数据卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="温度"
              value={latest.temperature || '-'}
              suffix="°C"
              prefix={<ThermometerOutlined />}
              valueStyle={{ color: latest.temperature > 30 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="湿度"
              value={latest.humidity || '-'}
              suffix="%"
              prefix={<DropletOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="光照"
              value={latest.light || '-'}
              suffix="lux"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="CO₂"
              value={latest.co2 || '-'}
              suffix="ppm"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 温湿度趋势图 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="温度趋势">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="temperature" stroke="#ff4d4f" strokeWidth={2} dot={false} name="温度 (°C)" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="湿度趋势">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="humidity" stroke="#1890ff" strokeWidth={2} dot={false} name="湿度 (%)" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default GreenhouseDetail
