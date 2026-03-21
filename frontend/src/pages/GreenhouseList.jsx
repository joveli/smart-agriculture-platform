/**
 * 温室管理页面
 */

import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, InputNumber, Tag, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { greenhouseApi, farmApi } from '../api'

const STATUS_OPTIONS = [
  { label: '活跃', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '维护中', value: 'maintenance' },
]

function GreenhouseList() {
  const navigate = useNavigate()
  const [data, setData] = useState([])
  const [farms, setFarms] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
    loadFarms()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await greenhouseApi.list()
      setData(res.data)
    } catch { message.error('加载失败') }
    finally { setLoading(false) }
  }

  const loadFarms = async () => {
    try {
      const res = await farmApi.list()
      setFarms(res.data)
    } catch {}
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await greenhouseApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await greenhouseApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (err) {
      if (err.errorFields) return
      message.error('操作失败')
    }
  }

  const handleDelete = async (id) => {
    try { await greenhouseApi.delete(id); message.success('删除成功'); loadData() }
    catch { message.error('删除失败') }
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '农场',
      dataIndex: 'farm_id',
      key: 'farm_id',
      render: (id) => farms.find(f => f.id === id)?.name || id,
    },
    { title: '面积（m²）', dataIndex: 'area_sqm', key: 'area_sqm' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s) => {
        const colors = { active: 'green', inactive: 'default', maintenance: 'orange' }
        return <Tag color={colors[s]}>{STATUS_OPTIONS.find(o => o.value === s)?.label || s}</Tag>
      },
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: v => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'action', width: 180,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/greenhouses/${record.id}`)}>详情</Button>
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
        <h2 style={{ margin: 0 }}>温室管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalVisible(true) }}>新增温室</Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      <Modal title={editingId ? '编辑温室' : '新增温室'} open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)} width={500}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="温室名称" rules={[{ required: true, message: '请输入温室名称' }]}><Input placeholder="请输入温室名称" /></Form.Item>
          <Form.Item name="farm_id" label="所属农场" rules={[{ required: true, message: '请选择农场' }]}>
            <Select placeholder="请选择农场" options={farms.map(f => ({ label: f.name, value: f.id }))} />
          </Form.Item>
          <Form.Item name="area_sqm" label="面积（平方米）"><InputNumber min={0} style={{ width: '100%' }} placeholder="请输入面积" /></Form.Item>
          <Form.Item name="status" label="状态" initialValue="active"><Select options={STATUS_OPTIONS} /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} placeholder="请输入描述" /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default GreenhouseList
