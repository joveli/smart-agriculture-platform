/**
 * 告警管理页面
 */

import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Badge, Modal, Form, Input, Select, InputNumber, Tabs } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, AlertOutlined } from '@ant-design/icons'
import { alertApi } from '../api'

const LEVEL_OPTIONS = [
  { label: '严重', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '通知', value: 'info' },
]

function AlertList() {
  const [alerts, setAlerts] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(false)
  const [ruleModalVisible, setRuleModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadAlerts()
    loadRules()
  }, [])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const res = await alertApi.list({ limit: 100 })
      setAlerts(res.data)
    } catch { message.error('加载失败') }
    finally { setLoading(false) }
  }

  const loadRules = async () => {
    try {
      const res = await alertApi.listRules()
      setRules(res.data)
    } catch {}
  }

  const handleAcknowledge = async (id) => {
    try { await alertApi.acknowledge(id, {}); message.success('已确认'); loadAlerts() }
    catch { message.error('操作失败') }
  }

  const handleResolve = async (id) => {
    try { await alertApi.resolve(id); message.success('已解决'); loadAlerts() }
    catch { message.error('操作失败') }
  }

  const handleRuleSubmit = async () => {
    try {
      await form.validateFields()
      const values = form.getFieldsValue()
      await alertApi.createRule(values)
      message.success('规则创建成功')
      setRuleModalVisible(false)
      loadRules()
    } catch (err) { if (err.errorFields) return; message.error('操作失败') }
  }

  const alertColumns = [
    { title: '类型', dataIndex: 'alert_type', key: 'alert_type' },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (l) => {
        const colors = { critical: 'red', warning: 'orange', info: 'blue' }
        return <Tag color={colors[l]}>{l === 'critical' ? '严重' : l === 'warning' ? '警告' : '通知'}</Tag>
      },
    },
    { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s) => {
        if (s === 'pending') return <Badge status="warning" text="待处理" />
        if (s === 'acknowledged') return <Badge status="processing" text="已确认" />
        return <Badge status="success" text="已解决" />
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: v => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          {record.status === 'pending' && (
            <Button size="small" onClick={() => handleAcknowledge(record.id)}>确认</Button>
          )}
          {record.status !== 'resolved' && (
            <Button size="small" type="primary" onClick={() => handleResolve(record.id)}>解决</Button>
          )}
        </Space>
      ),
    },
  ]

  const ruleColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '指标', dataIndex: 'metric', key: 'metric' },
    {
      title: '条件',
      key: 'condition',
      render: (_, r) => `${r.metric} ${r.operator} ${r.threshold}`,
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (l) => {
        const colors = { critical: 'red', warning: 'orange', info: 'blue' }
        return <Tag color={colors[l]}>{l}</Tag>
      },
    },
    {
      title: '通知渠道',
      dataIndex: 'notification_channels',
      key: 'notification_channels',
      render: (ch) => ch?.map(c => <Tag key={c}>{c}</Tag>),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (e) => <Tag color={e ? 'green' : 'default'}>{e ? '启用' : '禁用'}</Tag>,
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>告警管理</h2>
        <Button type="primary" icon={<AlertOutlined />} onClick={() => { form.resetFields(); setRuleModalVisible(true) }}>新建规则</Button>
      </div>

      <Tabs
        items={[
          {
            key: 'alerts',
            label: <span><AlertOutlined /> 告警记录</span>,
            children: (
              <Table columns={alertColumns} dataSource={alerts} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
            ),
          },
          {
            key: 'rules',
            label: <span><ClockCircleOutlined /> 告警规则</span>,
            children: (
              <Table columns={ruleColumns} dataSource={rules} rowKey="id" pagination={false} />
            ),
          },
        ]}
      />

      <Modal title="新建告警规则" open={ruleModalVisible} onOk={handleRuleSubmit} onCancel={() => setRuleModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="规则名称" rules={[{ required: true, message: '请输入规则名称' }]}>
            <Input placeholder="例如：高温告警" />
          </Form.Item>
          <Form.Item name="metric" label="监测指标" rules={[{ required: true, message: '请选择指标' }]}>
            <Select placeholder="请选择指标" options={[
              { label: '温度 (temperature)', value: 'temperature' },
              { label: '湿度 (humidity)', value: 'humidity' },
              { label: '光照 (light)', value: 'light' },
              { label: 'CO₂ (co2)', value: 'co2' },
              { label: '土壤温度 (soil_temperature)', value: 'soil_temperature' },
              { label: '土壤湿度 (soil_humidity)', value: 'soil_humidity' },
            ]} />
          </Form.Item>
          <Form.Item name="operator" label="条件" rules={[{ required: true, message: '请选择条件' }]}>
            <Select options={[
              { label: '大于 (gt)', value: 'gt' },
              { label: '小于 (lt)', value: 'lt' },
              { label: '大于等于 (gte)', value: 'gte' },
              { label: '小于等于 (lte)', value: 'lte' },
            ]} />
          </Form.Item>
          <Form.Item name="threshold" label="阈值" rules={[{ required: true, message: '请输入阈值' }]}>
            <InputNumber style={{ width: '100%' }} placeholder="请输入阈值" />
          </Form.Item>
          <Form.Item name="level" label="告警级别" initialValue="warning">
            <Select options={LEVEL_OPTIONS} />
          </Form.Item>
          <Form.Item name="cooldown_minutes" label="收敛间隔（分钟）" initialValue={5}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AlertList
