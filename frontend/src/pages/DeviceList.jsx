/**
 * 设备管理页面
 */

import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, InputNumber, Tag, message, Popconfirm, Badge } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SendOutlined } from '@ant-design/icons'
import { deviceApi, greenhouseApi } from '../api'

const DEVICE_TYPE_OPTIONS = [
  { label: '传感器', value: 'sensor' },
  { label: '执行器', value: 'actuator' },
  { label: '网关', value: 'gateway' },
  { label: '摄像头', value: 'camera' },
]
const DEVICE_STATUS_OPTIONS = [
  { label: '在线', value: 'online' },
  { label: '离线', value: 'offline' },
  { label: '维护中', value: 'maintenance' },
  { label: '故障', value: 'fault' },
]

function DeviceList() {
  const [data, setData] = useState([])
  const [greenhouses, setGreenhouses] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [commandModalVisible, setCommandModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [commandTarget, setCommandTarget] = useState(null)
  const [form] = Form.useForm()
  const [commandForm] = Form.useForm()

  useEffect(() => {
    loadData()
    loadGreenhouses()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await deviceApi.list()
      setData(res.data)
    } catch { message.error('加载失败') }
    finally { setLoading(false) }
  }

  const loadGreenhouses = async () => {
    try {
      const res = await greenhouseApi.list()
      setGreenhouses(res.data)
    } catch {}
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await deviceApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await deviceApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (err) { if (err.errorFields) return; message.error('操作失败') }
  }

  const handleDelete = async (id) => {
    try { await deviceApi.delete(id); message.success('删除成功'); loadData() }
    catch { message.error('删除失败') }
  }

  const handleSendCommand = async () => {
    try {
      const values = await commandForm.validateFields()
      await deviceApi.sendCommand(commandTarget.id, values)
      message.success('指令已下发')
      setCommandModalVisible(false)
    } catch { message.error('指令下发失败') }
  }

  const statusBadge = (s) => {
    const map = {
      online: { color: 'green', text: '在线' },
      offline: { color: 'default', text: '离线' },
      maintenance: { color: 'orange', text: '维护中' },
      fault: { color: 'red', text: '故障' },
    }
    const { color, text } = map[s] || { color: 'default', text: s }
    return <Badge status={color} text={text} />
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '温室',
      dataIndex: 'greenhouse_id',
      key: 'greenhouse_id',
      render: (id) => greenhouses.find(g => g.id === id)?.name || id,
    },
    {
      title: '类型',
      dataIndex: 'device_type',
      key: 'device_type',
      render: (t) => DEVICE_TYPE_OPTIONS.find(o => o.value === t)?.label || t,
    },
    { title: '型号', dataIndex: 'model', key: 'model', ellipsis: true },
    { title: '序列号', dataIndex: 'sn', key: 'sn', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: statusBadge,
    },
    {
      title: '最后活跃',
      dataIndex: 'last_seen_at',
      key: 'last_seen_at',
      render: v => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作', key: 'action', width: 200,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<SendOutlined />} onClick={() => { setCommandTarget(record); commandForm.resetFields(); setCommandModalVisible(true) }}>指令</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => { setEditingId(record.id); form.setFieldsValue(record); setModalVisible(true) }}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>设备管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalVisible(true) }}>新增设备</Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />

      {/* 新增/编辑 */}
      <Modal title={editingId ? '编辑设备' : '新增设备'} open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)} width={500}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="设备名称" rules={[{ required: true, message: '请输入设备名称' }]}><Input placeholder="请输入设备名称" /></Form.Item>
          <Form.Item name="greenhouse_id" label="所属温室" rules={[{ required: true, message: '请选择温室' }]}>
            <Select placeholder="请选择温室" options={greenhouses.map(g => ({ label: g.name, value: g.id }))} />
          </Form.Item>
          <Form.Item name="device_type" label="设备类型" rules={[{ required: true, message: '请选择设备类型' }]}>
            <Select options={DEVICE_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item name="model" label="型号"><Input placeholder="请输入型号" /></Form.Item>
          <Form.Item name="sn" label="序列号"><Input placeholder="请输入序列号" /></Form.Item>
          <Form.Item name="manufacturer" label="厂商"><Input placeholder="请输入厂商" /></Form.Item>
          <Form.Item name="sampling_interval_sec" label="采集间隔（秒）" initialValue={60}><InputNumber min={10} style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      {/* 发送指令 */}
      <Modal title={`发送指令 - ${commandTarget?.name}`} open={commandModalVisible} onOk={handleSendCommand} onCancel={() => setCommandModalVisible(false)}>
        <Form form={commandForm} layout="vertical">
          <Form.Item name="command" label="指令" rules={[{ required: true, message: '请输入指令' }]}>
            <Input placeholder="例如：open, close, restart" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default DeviceList
