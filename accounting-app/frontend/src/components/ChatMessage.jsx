import React from 'react';
import { Avatar, Card } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

/**
 * 聊天消息组件
 */
export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  // 格式化时间
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    return dayjs(timeStr).format('HH:mm');
  };

  // 渲染消息内容（支持简单的 markdown）
  const renderContent = (content) => {
    if (!content) return null;

    // 简单的换行处理
    const lines = content.split('\n');
    return lines.map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < lines.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
        gap: 8,
      }}
    >
      {/* 助手头像 */}
      {isAssistant && (
        <Avatar
          icon={<RobotOutlined />}
          style={{
            backgroundColor: '#7265e6',
            flexShrink: 0,
          }}
        />
      )}

      {/* 消息内容 */}
      <div
        style={{
          maxWidth: '70%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 12,
            backgroundColor: isUser ? '#7265e6' : '#f0f0f0',
            color: isUser ? '#fff' : '#333',
            fontSize: 14,
            lineHeight: 1.6,
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
          }}
        >
          {renderContent(message.content)}
        </div>
        <div
          style={{
            fontSize: 12,
            color: '#999',
            marginTop: 4,
            padding: '0 4px',
          }}
        >
          {formatTime(message.created_at)}
        </div>
      </div>

      {/* 用户头像 */}
      {isUser && (
        <Avatar
          icon={<UserOutlined />}
          style={{
            backgroundColor: '#87d068',
            flexShrink: 0,
          }}
        />
      )}
    </div>
  );
}