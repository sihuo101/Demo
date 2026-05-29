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
    // 如果没有当前对话，先创建一个
    if (!currentConversation) {
      const newConv = await createConversation();
      if (!newConv) return;

      // 等待状态更新后再发送消息
      setTimeout(async () => {
        await sendMessage(content);
      }, 100);
      return;
    }

    await sendMessage(content);
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
            <div
              onClick={() => handleSend('帮我记一笔午饭35元')}
              style={{
                padding: '12px 16px',
                backgroundColor: '#f5f5f5',
                borderRadius: 8,
                cursor: 'pointer',
                transition: 'background-color 0.3s',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#e6f7ff'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#f5f5f5'}
            >
              💬 帮我记一笔午饭35元
            </div>
            <div
              onClick={() => handleSend('这个月花了多少钱')}
              style={{
                padding: '12px 16px',
                backgroundColor: '#f5f5f5',
                borderRadius: 8,
                cursor: 'pointer',
                transition: 'background-color 0.3s',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#e6f7ff'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#f5f5f5'}
            >
              💬 这个月花了多少钱
            </div>
            <div
              onClick={() => handleSend('帮我算一下 125 + 378 等于多少')}
              style={{
                padding: '12px 16px',
                backgroundColor: '#f5f5f5',
                borderRadius: 8,
                cursor: 'pointer',
                transition: 'background-color 0.3s',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#e6f7ff'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#f5f5f5'}
            >
              💬 帮我算一下 125 + 378 等于多少
            </div>
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