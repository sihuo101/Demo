import React, { useState, useRef } from 'react';
import { Input, Button, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import VoiceInput from './VoiceInput';

const { TextArea } = Input;

/**
 * 聊天输入组件
 */
export default function ChatInput({ onSend, sending, disabled }) {
  const [value, setValue] = useState('');
  const textAreaRef = useRef(null);

  // 发送消息
  const handleSend = () => {
    const content = value.trim();
    if (!content || sending || disabled) return;

    onSend(content);
    setValue('');

    // 重新聚焦输入框
    setTimeout(() => {
      textAreaRef.current?.focus();
    }, 0);
  };

  // 键盘事件
  const handleKeyDown = (e) => {
    // Enter 发送，Shift+Enter 换行
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 语音输入结果
  const handleVoiceResult = (text) => {
    setValue(prev => {
      const newValue = prev ? prev + ' ' + text : text;
      return newValue;
    });

    // 聚焦输入框
    textAreaRef.current?.focus();
  };

  return (
    <div style={{
      padding: '16px',
      borderTop: '1px solid #f0f0f0',
      backgroundColor: '#fff',
    }}>
      <Space.Compact style={{ width: '100%' }}>
        <TextArea
          ref={textAreaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息，按 Enter 发送..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          disabled={disabled || sending}
          style={{
            flex: 1,
            borderRadius: '8px 0 0 8px',
            resize: 'none',
          }}
        />
        <VoiceInput
          onResult={handleVoiceResult}
          disabled={disabled || sending}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={sending}
          disabled={disabled || !value.trim()}
          style={{
            borderRadius: '0 8px 8px 0',
            height: 'auto',
          }}
        >
          发送
        </Button>
      </Space.Compact>
    </div>
  );
}