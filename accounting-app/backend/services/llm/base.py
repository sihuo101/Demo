"""LLM 基类定义"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional


class BaseLLM(ABC):
    """LLM 基类，所有模型实现此接口"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """普通对话

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            tools: 工具定义列表（可选）
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            包含 message 和 tool_calls 的字典
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话

        Args:
            messages: 消息列表
            tools: 工具定义列表（可选）
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            包含 content 和 tool_calls 的字典片段
        """
        pass
