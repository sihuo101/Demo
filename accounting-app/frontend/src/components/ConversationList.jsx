import React from 'react';
import { List, Button, Popconfirm, Empty, Tag } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

/**
 * 对话列表组件
 */
export default function ConversationList({
  conversations,
  currentConversation,
  loading,
  onSelect,
  onCreate,
  onDelete
}) {
  // 格式化时间
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = dayjs(timeStr);
    const now = dayjs();

    // 今天的时间只显示时分
    if (date.isSame(now, 'day')) {
      return date.format('HH:mm');
    }

    // 今年的显示月日
    if (date.isSame(now, 'year')) {
      return date.format('MM-DD');
    }

    // 其他显示年月日
    return date.format('YYYY-MM-DD');
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      borderRight: '1px solid #f0f0f0',
      backgroundColor: '#fafafa'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: 16, fontWeight: 500 }}>对话列表</span>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="small"
          onClick={() => onCreate()}
        >
          新建
        </Button>
      </div>

      {/* 列表 */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {conversations.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无对话"
            style={{ marginTop: 40 }}
          />
        ) : (
          <List
            loading={loading}
            dataSource={conversations}
            renderItem={(item) => (
              <List.Item
                style={{
                  padding: '12px 16px',
                  cursor: 'pointer',
                  backgroundColor: currentConversation?.id === item.id ? '#e6f7ff' : 'transparent',
                  borderLeft: currentConversation?.id === item.id ? '3px solid #1890ff' : '3px solid transparent',
                  transition: 'all 0.3s',
                }}
                onClick={() => onSelect(item)}
                actions={[
                  <Popconfirm
                    key="delete"
                    title="确定删除这个对话吗？"
                    description="删除后无法恢复"
                    onConfirm={(e) => {
                      e.stopPropagation();
                      onDelete(item.id);
                    }}
                    onCancel={(e) => e.stopPropagation()}
                  >
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      size="small"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <MessageOutlined style={{ fontSize: 18, color: '#7265e6' }} />
                  }
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: 120
                      }}>
                        {item.title || '新对话'}
                      </span>
                      {item.message_count > 0 && (
                        <Tag style={{ fontSize: 12, lineHeight: '18px', padding: '0 4px' }}>
                          {item.message_count}
                        </Tag>
                      )}
                    </div>
                  }
                  description={
                    <span style={{ fontSize: 12, color: '#999' }}>
                      {formatTime(item.updated_at)}
                    </span>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
}