import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  AccountBookOutlined,
  PieChartOutlined,
  UnorderedListOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import TransactionPage from './pages/TransactionPage';
import StatisticsPage from './pages/StatisticsPage';
import HistoryPage from './pages/HistoryPage';
import AgentPage from './pages/AgentPage';

const { Header, Content, Sider } = Layout;

const menuItems = [
  {
    key: '/',
    icon: <AccountBookOutlined />,
    label: <Link to="/">记账</Link>,
  },
  {
    key: '/history',
    icon: <UnorderedListOutlined />,
    label: <Link to="/history">账单</Link>,
  },
  {
    key: '/statistics',
    icon: <PieChartOutlined />,
    label: <Link to="/statistics">统计</Link>,
  },
  {
    key: '/agent',
    icon: <RobotOutlined />,
    label: <Link to="/agent">智能助手</Link>,
  },
];

function AppLayout() {
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        style={{ background: '#fff' }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 20,
          fontWeight: 600,
          color: '#1a1a1a',
        }}>
          💰 记账APP
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          <Routes>
            <Route path="/" element={<TransactionPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/statistics" element={<StatisticsPage />} />
            <Route path="/agent" element={<AgentPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
