/**
 * 农场管理页面
 */

import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, InputNumber, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { farmApi } from '../api'

function FarmList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await farmApi.list()
      setData(res.data)
    } catch { message.error('加载失败') }
    finally { setLoading(false) }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await farmApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await farmApi.create(values)
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
    try { await farmApi.delete(id); message.success('删除成功'); loadData() }
    catch { message.error('删除失败') }
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '位置', dataIndex: 'location', key: 'location', ellipsis: true },
    { title: '面积（亩）', dataIndex: 'area_mu', key: 'area_mu' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: v => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'action', width: 150,
      render: (_, record) => (
        <Space>
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
        <h2 style={{ margin: 0 }}>农场管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalVisible(true) }}>新增农场</Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      <Modal title={editingId ? '编辑农场' : '新增农场'} open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="农场名称" rules={[{ required: true, message: '请输入农场名称' }]}><Input placeholder="请输入农场名称" /></Form.Item>
          <Form.Item name="location" label="位置"><Input placeholder="请输入位置" /></Form.Item>
          <Form.Item name="area_mu" label="面积（亩）"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} placeholder="请输入描述" /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default FarmList
