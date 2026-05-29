import React, { useEffect, useState } from 'react';
import { Layout, Alert, Spin, Empty, Typography } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { useChat } from '../hooks/useChat';
import ConversationList from '../components/ConversationList';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import { getChatStatus } from '../api';

const { Sider, Content } = Layout;
const { Text } = Typography;

/**
 * 快捷指令组件
 */
function QuickCommand({ text, icon, description, onClick }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onClick={() => onClick(text)}
      style={{
        padding: '14px 18px',
        backgroundColor: isHovered ? '#e6f7ff' : '#f5f5f5',
        borderRadius: 10,
        cursor: 'pointer',
        transition: 'all 0.3s',
        border: isHovered ? '1px solid #91d5ff' : '1px solid transparent',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span style={{ fontSize: 24 }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 500, color: '#333' }}>{text}</div>
        <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>{description}</div>
      </div>
      <span style={{ color: '#7265e6', fontSize: 12 }}>试试 →</span>
    </div>
  );
}

/**
 * 智能体对话页面
 */
export default function AgentPage() {
  const {
    conversations,
    currentConversation,
    messages,
    loading,
    sending,
    error,
    loadConversations,
    createConversation,
    deleteConversation,
    switchConversation,
    sendMessage,
    createConversationAndSend,
    clearError
  } = useChat();

  const [agentStatus, setAgentStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const messagesEndRef = React.useRef(null);

  // 加载初始数据
  useEffect(() => {
    loadConversations();
    checkAgentStatus();
  }, [loadConversations]);

  // 检查智能体状态
  const checkAgentStatus = async () => {
    try {
      setStatusLoading(true);
      const status = await getChatStatus();
      setAgentStatus(status);
    } catch (err) {
      console.error('检查智能体状态失败:', err);
      setAgentStatus({ configured: false, message: '无法连接到服务' });
    } finally {
      setStatusLoading(false);
    }
  };

  // 滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 创建新对话
  const handleCreate = async () => {
    await createConversation();
  };

  // 删除对话
  const handleDelete = async (conversationId) => {
    await deleteConversation(conversationId);
  };

  // 选择对话
  const handleSelect = async (conversation) => {
    await switchConversation(conversation);
  };

  // 发送消息
  const handleSend = async (content) => {
    // 如果没有当前对话，创建新对话并直接发送（避免闭包陷阱）
    if (!currentConversation) {
      await createConversationAndSend(content);
      return;
    }

    await sendMessage(content);
  };

  // 快捷指令 - 创建新对话并执行命令
  const handleQuickCommand = async (content) => {
    // 创建新对话并发送消息
    await createConversationAndSend(content);
  };

  // 渲染聊天区域
  const renderChatArea = () => {
    if (statusLoading) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%'
        }}>
          <Spin size="large" />
        </div>
      );
    }

    if (!agentStatus?.configured) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
          padding: 24
        }}>
          <Alert
            message="智能体未配置"
            description={
              <div>
                <p>请在后端 .env 文件中配置 LLM 相关参数：</p>
                <ul>
                  <li><code>LLM_API_KEY</code> - API 密钥</li>
                  <li><code>LLM_BASE_URL</code> - API 地址</li>
                  <li><code>LLM_MODEL</code> - 模型名称</li>
                </ul>
                <p style={{ marginTop: 12 }}>
                  支持的国产模型：DeepSeek、通义千问、智谱GLM、月之暗面等
                </p>
              </div>
            }
            type="warning"
            showIcon
          />
        </div>
      );
    }

    if (!currentConversation) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
          gap: 24
        }}>
          <RobotOutlined style={{ fontSize: 64, color: '#7265e6' }} />
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ marginBottom: 8 }}>智能记账助手</h2>
            <Text type="secondary">
              我可以帮你记账、查询账单、统计数据、进行各种计算
            </Text>
          </div>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            maxWidth: 400,
            width: '100%'
          }}>
            <QuickCommand
              text="帮我记一笔午饭35元"
              icon="🍜"
              description="快速记账"
              onClick={handleQuickCommand}
            />
            <QuickCommand
              text="这个月花了多少钱"
              icon="📊"
              description="查询统计"
              onClick={handleQuickCommand}
            />
            <QuickCommand
              text="帮我算一下 125 + 378 等于多少"
              icon="🧮"
              description="数学计算"
              onClick={handleQuickCommand}
            />
            <QuickCommand
              text="工资到账8000元"
              icon="💰"
              description="记录收入"
              onClick={handleQuickCommand}
            />
          </div>
        </div>
      );
    }

    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}>
        {/* 消息列表 */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          backgroundColor: '#fff'
        }}>
          {messages.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="开始对话吧"
              style={{ marginTop: 80 }}
            />
          ) : (
            messages.map((msg, index) => (
              <ChatMessage key={msg.id || index} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入框 */}
        <ChatInput
          onSend={handleSend}
          sending={sending}
          disabled={false}
        />
      </div>
    );
  };

  return (
    <Layout style={{
      height: 'calc(100vh - 48px)',
      backgroundColor: '#fff',
      borderRadius: 8,
      overflow: 'hidden'
    }}>
      {/* 左侧对话列表 */}
      <Sider
        width={280}
        style={{
          backgroundColor: '#fafafa',
          borderRight: '1px solid #f0f0f0'
        }}
      >
        <ConversationList
          conversations={conversations}
          currentConversation={currentConversation}
          loading={loading}
          onSelect={handleSelect}
          onCreate={handleCreate}
          onDelete={handleDelete}
        />
      </Sider>

      {/* 右侧聊天区域 */}
      <Content style={{ height: '100%' }}>
        {error && (
          <Alert
            message={error}
            type="error"
            closable
            onClose={clearError}
            style={{ margin: 16 }}
          />
        )}
        {renderChatArea()}
      </Content>
    </Layout>
  );
}