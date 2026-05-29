import React, { useState, useRef, useCallback } from 'react';
import { Button, message, Tooltip } from 'antd';
import { AudioOutlined, AudioMutedOutlined } from '@ant-design/icons';

/**
 * 语音输入组件 - 使用 Web Speech API
 */
export default function VoiceInput({ onResult, disabled }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef(null);

  // 检查浏览器支持
  const checkSupport = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      return false;
    }
    return true;
  }, []);

  // 开始录音
  const startRecording = useCallback(() => {
    if (!checkSupport()) {
      message.warning('您的浏览器不支持语音输入，请使用 Chrome 浏览器');
      return;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      // 配置
      recognition.lang = 'zh-CN';  // 中文
      recognition.continuous = false;  // 不连续识别
      recognition.interimResults = true;  // 显示中间结果
      recognition.maxAlternatives = 1;

      // 识别结果
      recognition.onresult = (event) => {
        const results = event.results;
        const transcript = Array.from(results)
          .map(result => result[0].transcript)
          .join('');

        // 如果是最终结果
        if (results[0].isFinal) {
          onResult(transcript);
          stopRecording();
        }
      };

      // 错误处理
      recognition.onerror = (event) => {
        console.error('语音识别错误:', event.error);
        if (event.error === 'no-speech') {
          message.info('未检测到语音，请重试');
        } else if (event.error === 'not-allowed') {
          message.error('请允许麦克风权限');
        } else {
          message.error('语音识别失败，请重试');
        }
        stopRecording();
      };

      // 结束事件
      recognition.onend = () => {
        setIsRecording(false);
      };

      // 开始识别
      recognition.start();
      recognitionRef.current = recognition;
      setIsRecording(true);

      message.info('正在聆听，请说话...');
    } catch (err) {
      console.error('启动语音识别失败:', err);
      message.error('启动语音识别失败');
    }
  }, [checkSupport, onResult]);

  // 停止录音
  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsRecording(false);
  }, []);

  // 切换录音状态
  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  if (!isSupported) {
    return null;
  }

  return (
    <Tooltip title={isRecording ? '点击停止' : '语音输入'}>
      <Button
        icon={isRecording ? <AudioMutedOutlined /> : <AudioOutlined />}
        onClick={toggleRecording}
        type={isRecording ? 'primary' : 'default'}
        danger={isRecording}
        disabled={disabled}
        style={{
          animation: isRecording ? 'pulse 1.5s infinite' : 'none',
        }}
      />
    </Tooltip>
  );
}