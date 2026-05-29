import { useState, useCallback, useRef } from 'react';
import {
  getConversations,
  createConversation,
  deleteConversation,
  getMessages,
  sendMessage
} from '../api';

/**
 * 聊天 Hook - 管理对话状态和消息
 */
export function useChat() {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  // 加载对话列表
  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      setError('加载对话列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 创建新对话
  const handleCreateConversation = useCallback(async (title) => {
    try {
      const data = await createConversation({ title: title || '新对话' });
      setConversations(prev => [data, ...prev]);
      setCurrentConversation(data);
      setMessages([]);
      return data;
    } catch (err) {
      setError('创建对话失败');
      console.error(err);
      return null;
    }
  }, []);

  // 删除对话
  const handleDeleteConversation = useCallback(async (conversationId) => {
    try {
      await deleteConversation(conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));

      // 如果删除的是当前对话，清空当前对话
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }

      return true;
    } catch (err) {
      setError('删除对话失败');
      console.error(err);
      return false;
    }
  }, [currentConversation]);

  // 切换对话
  const switchConversation = useCallback(async (conversation) => {
    setCurrentConversation(conversation);

    try {
      setLoading(true);
      const data = await getMessages(conversation.id);
      setMessages(data);
    } catch (err) {
      setError('加载消息失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 发送消息到指定对话（流式）
  const sendMessageToConversation = useCallback(async (conversationId, content) => {
    if (!conversationId || !content.trim()) return;

    // 添加用户消息到列表
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setSending(true);
    setError(null);

    // 创建助手消息占位符
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      // 使用 SSE 进行流式请求
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          content: content
        })
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 解析 SSE 事件
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            // 事件类型
            continue;
          }

          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'content' && data.content) {
                fullContent += data.content;
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.content = fullContent;
                  }
                  return newMessages;
                });
              } else if (data.type === 'tool_start') {
                // 工具调用开始
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.content = fullContent + `\n\n🔧 正在执行: ${data.tool}...`;
                  }
                  return newMessages;
                });
              } else if (data.type === 'tool_result') {
                // 工具调用结果
                if (data.result?.message) {
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.role === 'assistant') {
                      lastMsg.content = fullContent;
                    }
                    return newMessages;
                  });
                }
              } else if (data.type === 'error') {
                setError(data.content);
              } else if (data.type === 'end') {
                // 流结束
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      // 更新对话列表中的消息数量
      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? { ...c, message_count: (c.message_count || 0) + 2, updated_at: new Date().toISOString() }
            : c
        )
      );

    } catch (err) {
      setError('发送消息失败');
      console.error(err);

      // 更新助手消息为错误提示
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.content = '❌ 发送消息失败，请重试';
        }
        return newMessages;
      });
    } finally {
      setSending(false);
    }
  }, []);

  // 发送消息（使用当前对话）
  const handleSendMessage = useCallback(async (content) => {
    if (!currentConversation) return;
    await sendMessageToConversation(currentConversation.id, content);
  }, [currentConversation, sendMessageToConversation]);

  // 创建对话并发送消息（用于快捷指令）
  const createConversationAndSend = useCallback(async (content) => {
    try {
      // 创建新对话
      const data = await createConversation({ title: '新对话' });
      if (!data) return null;

      // 更新状态
      setConversations(prev => [data, ...prev]);
      setCurrentConversation(data);
      setMessages([]);

      // 发送消息
      await sendMessageToConversation(data.id, content);

      return data;
    } catch (err) {
      setError('创建对话失败');
      console.error(err);
      return null;
    }
  }, [sendMessageToConversation]);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    conversations,
    currentConversation,
    messages,
    loading,
    sending,
    error,
    loadConversations,
    createConversation: handleCreateConversation,
    deleteConversation: handleDeleteConversation,
    switchConversation,
    sendMessage: handleSendMessage,
    createConversationAndSend,
    clearError
  };
}