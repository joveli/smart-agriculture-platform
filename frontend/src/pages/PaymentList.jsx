import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, Space, message, Card, Row, Col, Statistic } from 'antd';
import { PlusOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { paymentApi } from '../api';

const PaymentList = () => {
  const [payments, setPayments] = useState([]);
  const [stats, setStats] = useState({ total_income: 0, pending_amount: 0, completed_amount: 0, refunded_amount: 0 });
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [statusFilter, setStatusFilter] = useState(null);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const [listRes, statsRes] = await Promise.all([paymentApi.list(params), paymentApi.stats()]);
      setPayments(listRes.data);
      setStats(statsRes.data);
    } catch (err) { message.error('获取支付列表失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchPayments(); }, [statusFilter]);

  const handleSubmit = async () => {
    try {
      await form.validateFields();
      const values = form.getFieldsValue();
      await paymentApi.create(values);
      message.success('创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchPayments();
    } catch (err) { message.error('创建失败'); }
  };

  const statusConfig = {
    pending: { color: 'orange', text: '待支付' },
    processing: { color: 'blue', text: '处理中' },
    completed: { color: 'green', text: '已完成' },
    failed: { color: 'red', text: '失败' },
    refunded: { color: 'gray', text: '已退款' },
  };

  const columns = [
    { title: '订单号', dataIndex: 'order_id', key: 'order_id' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (a) => '¥' + a.toLocaleString() },
    { title: '方式', dataIndex: 'payment_method', key: 'payment_method', render: (m) => ({ alipay: '支付宝', wechat: '微信', bank_transfer: '银行转账' })[m] },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s) => <Tag color={statusConfig[s]?.color}>{statusConfig[s]?.text}</Tag> },
    { title: '交易号', dataIndex: 'transaction_id', key: 'transaction_id', render: (t) => t || '-' },
    { title: '时间', dataIndex: 'created_at', key: 'created_at' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="总收入" value={stats.total_income} prefix="¥" /></Card></Col>
        <Col span={6}><Card><Statistic title="待收款" value={stats.pending_amount} prefix="¥" /></Card></Col>
        <Col span={6}><Card><Statistic title="已完成" value={stats.completed_amount} prefix="¥" /></Card></Col>
        <Col span={6}><Card><Statistic title="已退款" value={stats.refunded_amount} prefix="¥" /></Card></Col>
      </Row>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Select placeholder="状态筛选" allowClear style={{ width: 120 }} onChange={(v) => setStatusFilter(v)}>
          {Object.entries(statusConfig).map(([k, v]) => <Select.Option key={k} value={k}>{v.text}</Select.Option>)}
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>创建支付</Button>
      </div>
      <Table columns={columns} dataSource={payments} rowKey="id" loading={loading} />
      <Modal title="创建支付" open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="amount" label="金额" rules={[{ required: true }]}><Input type="number" prefix="¥" /></Form.Item>
          <Form.Item name="payment_method" label="支付方式" rules={[{ required: true }]} initialValue="alipay">
            <Select><Select.Option value="alipay">支付宝</Select.Option><Select.Option value="wechat">微信</Select.Option><Select.Option value="bank_transfer">银行转账</Select.Option></Select>
          </Form.Item>
          <Form.Item name="contract_id" label="关联合同"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
export default PaymentList;
