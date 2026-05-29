import React, { useState, useEffect } from 'react';
import {
  Card, List, DatePicker, Select, Empty, Popconfirm,
  message, Tag, Spin, Pagination
} from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getTransactions, deleteTransaction } from '../api';

function HistoryPage() {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [month, setMonth] = useState(dayjs().format('YYYY-MM'));
  const [type, setType] = useState(undefined);

  useEffect(() => {
    loadTransactions();
  }, [page, month, type]);

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const data = await getTransactions({
        page,
        page_size: 20,
        month,
        type,
      });
      setTransactions(data.items);
      setTotal(data.total);
    } catch (error) {
      message.error('加载账单失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteTransaction(id);
      message.success('删除成功');
      loadTransactions();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 月份选择器
  const handleMonthChange = (date) => {
    setMonth(date ? date.format('YYYY-MM') : undefined);
    setPage(1);
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>账单明细</h1>
      </div>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <DatePicker
            picker="month"
            value={month ? dayjs(month) : null}
            onChange={handleMonthChange}
            placeholder="选择月份"
            allowClear
          />
          <Select
            value={type}
            onChange={(value) => {
              setType(value);
              setPage(1);
            }}
            placeholder="收支类型"
            allowClear
            style={{ width: 120 }}
          >
            <Select.Option value="expense">支出</Select.Option>
            <Select.Option value="income">收入</Select.Option>
          </Select>
        </div>
      </Card>

      {/* 账单列表 */}
      <Card>
        <Spin spinning={loading}>
          {transactions.length > 0 ? (
            <>
              <List
                dataSource={transactions}
                renderItem={(item) => (
                  <div className="transaction-item">
                    <div className="transaction-info">
                      <div className="transaction-icon">
                        {item.type === 'income' ? '💰' : '💸'}
                      </div>
                      <div className="transaction-detail">
                        <span className="transaction-category">
                          {item.category_name}
                          <Tag
                            color={item.type === 'income' ? 'green' : 'red'}
                            style={{ marginLeft: 8 }}
                          >
                            {item.type === 'income' ? '收入' : '支出'}
                          </Tag>
                        </span>
                        <span className="transaction-note">
                          {dayjs(item.date).format('YYYY-MM-DD')}
                          {item.note && ` · ${item.note}`}
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <span className={`transaction-amount ${item.type}`}>
                        {item.type === 'income' ? '+' : '-'}¥{item.amount.toFixed(2)}
                      </span>
                      <Popconfirm
                        title="确定删除这条记录吗？"
                        onConfirm={() => handleDelete(item.id)}
                        okText="确定"
                        cancelText="取消"
                      >
                        <DeleteOutlined
                          style={{ color: '#ff4d4f', cursor: 'pointer' }}
                        />
                      </Popconfirm>
                    </div>
                  </div>
                )}
              />
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Pagination
                  current={page}
                  total={total}
                  pageSize={20}
                  onChange={setPage}
                  showTotal={(total) => `共 ${total} 条`}
                />
              </div>
            </>
          ) : (
            <Empty description="暂无账单数据" />
          )}
        </Spin>
      </Card>
    </div>
  );
}

export default HistoryPage;
