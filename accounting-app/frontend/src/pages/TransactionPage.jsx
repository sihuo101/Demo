import React, { useState, useEffect } from 'react';
import {
  Card, Form, Input, InputNumber, Select, DatePicker, Button,
  message, Segmented, Space
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getCategories, createTransaction, getStatistics } from '../api';

const { TextArea } = Input;

function TransactionPage() {
  const [form] = Form.useForm();
  const [type, setType] = useState('expense');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  // 加载分类列表
  useEffect(() => {
    loadCategories();
    loadStats();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await getCategories();
      setCategories(data);
    } catch (error) {
      message.error('加载分类失败');
    }
  };

  const loadStats = async () => {
    try {
      const data = await getStatistics(dayjs().year());
      setStats(data);
    } catch (error) {
      console.error('加载统计失败', error);
    }
  };

  // 筛选当前类型的分类
  const filteredCategories = categories.filter(c => c.type === type);

  // 提交表单
  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      await createTransaction({
        amount: values.amount,
        type: type,
        category_id: values.category_id,
        category_name: categories.find(c => c.id === values.category_id)?.name || '',
        note: values.note || '',
        date: values.date.toISOString(),
      });
      message.success('记账成功！');
      form.resetFields();
      form.setFieldsValue({ date: dayjs() });
      loadStats();
    } catch (error) {
      message.error('记账失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>记账</h1>
      </div>

      {/* 收支概览卡片 */}
      {stats && (
        <div className="stats-card">
          <div style={{ fontSize: 14, opacity: 0.8 }}>本月结余</div>
          <div className="balance">
            ¥{stats.balance.toFixed(2)}
          </div>
          <div className="detail">
            <div className="detail-item">
              <span className="detail-label">收入</span>
              <span className="detail-value" style={{ color: '#95de64' }}>
                ¥{stats.total_income.toFixed(2)}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">支出</span>
              <span className="detail-value" style={{ color: '#ffa39e' }}>
                ¥{stats.total_expense.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 记账表单 */}
      <Card title="新建账单">
        <div style={{ marginBottom: 24 }}>
          <Segmented
            options={[
              { label: '支出', value: 'expense' },
              { label: '收入', value: 'income' },
            ]}
            value={type}
            onChange={(value) => {
              setType(value);
              form.setFieldsValue({ category_id: undefined });
            }}
            style={{ marginBottom: 16 }}
          />
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ date: dayjs() }}
        >
          <Form.Item
            name="amount"
            label="金额"
            rules={[{ required: true, message: '请输入金额' }]}
          >
            <InputNumber
              prefix="¥"
              style={{ width: '100%' }}
              min={0.01}
              step={0.01}
              precision={2}
              placeholder="请输入金额"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="category_id"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="请选择分类">
              {filteredCategories.map(cat => (
                <Select.Option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="note" label="备注">
            <TextArea rows={3} placeholder="添加备注（可选）" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlusOutlined />}
              loading={loading}
              size="large"
              style={{ width: '100%' }}
            >
              记一笔
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default TransactionPage;
