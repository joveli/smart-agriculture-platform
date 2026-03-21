/**
 * 租户管理页面
 */

import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { tenantApi } from '../api'

const PLAN_OPTIONS = [
  { label: '免费版 (Free)', value: 'free' },
  { label: '标准版 (Standard)', value: 'standard' },
  { label: '高级版 (Premium)', value: 'premium' },
  { label: '企业版 (Enterprise)', value: 'enterprise' },
]

const STATUS_OPTIONS = [
  { label: '活跃', value: 'active' },
  { label: '暂停', value: 'suspended' },
  { label: '待审核', value: 'pending' },
]

function TenantList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await tenantApi.list()
      setData(res.data)
    } catch (err) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditingId(record.id)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await tenantApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (err) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await tenantApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await tenantApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (err) {
      if (err.errorFields) return
      message.error('操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 220, ellipsis: true },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '联系邮箱', dataIndex: 'contact_email', key: 'contact_email' },
    { title: '联系电话', dataIndex: 'contact_phone', key: 'contact_phone' },
    {
      title: '套餐',
      dataIndex: 'plan_type',
      key: 'plan_type',
      render: (v) => {
        const map = { free: '免费版', standard: '标准版', premium: '高级版', enterprise: '企业版' }
        return map[v] || v
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v) => {
        const color = { active: 'green', suspended: 'red', pending: 'orange' }
        return <span style={{ color: color[v] || 'default' }}>{v}</span>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v) => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
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
        <h2 style={{ margin: 0 }}>租户管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增租户</Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingId ? '编辑租户' : '新增租户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="租户名称" rules={[{ required: true, message: '请输入租户名称' }]}>
            <Input placeholder="请输入租户名称" />
          </Form.Item>
          <Form.Item name="contact_email" label="联系邮箱" rules={[{ required: true, type: 'email', message: '请输入正确的邮箱' }]}>
            <Input placeholder="请输入联系邮箱" />
          </Form.Item>
          <Form.Item name="contact_phone" label="联系电话">
            <Input placeholder="请输入联系电话" />
          </Form.Item>
          <Form.Item name="plan_type" label="套餐" initialValue="free">
            <Select options={PLAN_OPTIONS} />
          </Form.Item>
          {editingId && (
            <Form.Item name="status" label="状态">
              <Select options={STATUS_OPTIONS} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default TenantList
