import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, DatePicker, Tag, Space, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { contractApi } from '../api';
import dayjs from 'dayjs';

const ContractList = () => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [form] = Form.useForm();
  const [statusFilter, setStatusFilter] = useState(null);

  const fetchContracts = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await contractApi.list(params);
      setContracts(res.data);
    } catch (err) {
      message.error('获取合同列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchContracts(); }, [statusFilter]);

  const handleAdd = () => {
    setEditingContract(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingContract(record);
    form.setFieldsValue({ ...record, start_date: dayjs(record.start_date), end_date: dayjs(record.end_date) });
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await contractApi.delete(id);
      message.success('删除成功');
      fetchContracts();
    } catch (err) { message.error('删除失败'); }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = { ...values, start_date: values.date_range[0].format('YYYY-MM-DD'), end_date: values.date_range[1].format('YYYY-MM-DD'), date_range: undefined };
      if (editingContract) { await contractApi.update(editingContract.id, data); message.success('更新成功'); }
      else { await contractApi.create(data); message.success('创建成功'); }
      setModalVisible(false);
      fetchContracts();
    } catch (err) { message.error(editingContract ? '更新失败' : '创建失败'); }
  };

  const columns = [
    { title: '合同名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'contract_type', key: 'contract_type', render: (t) => ({ rental: '租赁', service: '服务', purchase: '采购' })[t] },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (a) => '¥' + a.toLocaleString() },
    { title: '日期', key: 'dates', render: (_, r) => r.start_date + ' ~ ' + r.end_date },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s) => ({ draft: '草稿', active: '生效', expired: '过期', terminated: '终止' })[s] },
    { title: '操作', key: 'action', render: (_, r) => <Space><Button type="link" onClick={() => handleEdit(r)}>编辑</Button><Button type="link" danger onClick={() => handleDelete(r.id)}>删除</Button></Space> },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Select placeholder="状态筛选" allowClear style={{ width: 120 }} onChange={(v) => setStatusFilter(v)}>
          <Select.Option value="draft">草稿</Select.Option>
          <Select.Option value="active">生效中</Select.Option>
          <Select.Option value="expired">已过期</Select.Option>
          <Select.Option value="terminated">已终止</Select.Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新建合同</Button>
      </div>
      <Table columns={columns} dataSource={contracts} rowKey="id" loading={loading} />
      <Modal title={editingContract ? '编辑合同' : '新建合同'} open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)} width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contract_type" label="类型" rules={[{ required: true }]}><Select><Select.Option value="rental">租赁合同</Select.Option><Select.Option value="service">服务合同</Select.Option><Select.Option value="purchase">采购合同</Select.Option></Select></Form.Item>
          <Form.Item name="amount" label="金额" rules={[{ required: true }]}><Input type="number" prefix="¥" /></Form.Item>
          <Form.Item name="date_range" label="期限" rules={[{ required: true }]}><DatePicker.RangePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="status" label="状态"><Select><Select.Option value="draft">草稿</Select.Option><Select.Option value="active">生效中</Select.Option></Select></Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
export default ContractList;
