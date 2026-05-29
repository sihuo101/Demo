import React, { useState, useEffect } from 'react';
import { Card, DatePicker, Row, Col, Statistic, Spin, Empty } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, AccountBookOutlined
} from '@ant-design/icons';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import dayjs from 'dayjs';
import { getStatistics } from '../api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC0CB', '#FFD700'];

function StatisticsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [year, setYear] = useState(dayjs().year());

  useEffect(() => {
    loadStats();
  }, [year]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await getStatistics(year);
      setStats(data);
    } catch (error) {
      console.error('加载统计失败', error);
    } finally {
      setLoading(false);
    }
  };

  // 准备柱状图数据
  const barChartData = stats?.monthly_stats.map(item => ({
    month: item.month.split('-')[1] + '月',
    收入: item.total_income,
    支出: item.total_expense,
  })) || [];

  // 准备饼图数据
  const pieChartData = stats?.category_stats.map(item => ({
    name: item.category_name,
    value: item.total,
  })) || [];

  return (
    <div className="container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>统计报表</h1>
        <DatePicker
          picker="year"
          value={dayjs().year(year)}
          onChange={(date) => setYear(date.year())}
        />
      </div>

      <Spin spinning={loading}>
        {stats ? (
          <>
            {/* 统计卡片 */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="总收入"
                    value={stats.total_income}
                    precision={2}
                    prefix={<ArrowUpOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="总支出"
                    value={stats.total_expense}
                    precision={2}
                    prefix={<ArrowDownOutlined />}
                    suffix="元"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="结余"
                    value={stats.balance}
                    precision={2}
                    prefix={<AccountBookOutlined />}
                    suffix="元"
                    valueStyle={{ color: stats.balance >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* 收支趋势图 */}
            <Card title="收支趋势" style={{ marginBottom: 24 }}>
              {barChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="收入" fill="#52c41a" />
                    <Bar dataKey="支出" fill="#ff4d4f" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Empty description="暂无数据" />
              )}
            </Card>

            {/* 支出分类饼图 */}
            <Card title="支出分类">
              {pieChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `¥${value.toFixed(2)}`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Empty description="暂无数据" />
              )}
            </Card>
          </>
        ) : (
          <Empty description="暂无统计数据" />
        )}
      </Spin>
    </div>
  );
}

export default StatisticsPage;
