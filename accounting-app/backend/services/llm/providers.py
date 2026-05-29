"""LLM 提供商实现 - 支持 OpenAI 兼容接口的国产模型"""

import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from .base import BaseLLM


class OpenAICompatibleLLM(BaseLLM):
    """OpenAI 兼容接口的 LLM 实现

    支持: DeepSeek、通义千问、智谱GLM、月之暗面等
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(api_key, base_url, model)
        # 确保 base_url 以 /v1 结尾或包含 /chat/completions
        if not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'
        self.chat_url = f"{base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """普通对话"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        # 如果有工具定义，添加到请求中
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.chat_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        # 解析响应
        choice = result["choices"][0]
        message = choice["message"]

        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
            "finish_reason": choice.get("finish_reason", "stop")
        }

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.chat_url,
                headers=self.headers,
                json=payload
            ) as response:
                response.raise_for_status()

                # 收集工具调用信息
                tool_calls_buffer = {}
                content_buffer = ""

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]  # 去掉 "data: " 前缀
                    if data == "[DONE]":
                        # 如果有累积的工具调用，返回
                        if tool_calls_buffer:
                            yield {
                                "content": content_buffer,
                                "tool_calls": list(tool_calls_buffer.values()),
                                "finish_reason": "tool_calls"
                            }
                        break

                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        finish_reason = chunk["choices"][0].get("finish_reason")

                        # 处理文本内容
                        if "content" in delta and delta["content"]:
                            content_buffer += delta["content"]
                            yield {
                                "content": delta["content"],
                                "tool_calls": [],
                                "finish_reason": None
                            }

                        # 处理工具调用
                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in tool_calls_buffer:
                                    tool_calls_buffer[idx] = {
                                        "id": tc.get("id", ""),
                                        "type": "function",
                                        "function": {
                                            "name": "",
                                            "arguments": ""
                                        }
                                    }

                                if "id" in tc:
                                    tool_calls_buffer[idx]["id"] = tc["id"]
                                if "function" in tc:
                                    if "name" in tc["function"]:
                                        tool_calls_buffer[idx]["function"]["name"] += tc["function"]["name"]
                                    if "arguments" in tc["function"]:
                                        tool_calls_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]

                        # 处理结束
                        if finish_reason:
                            if finish_reason == "tool_calls" and tool_calls_buffer:
                                yield {
                                    "content": content_buffer,
                                    "tool_calls": list(tool_calls_buffer.values()),
                                    "finish_reason": "tool_calls"
                                }
                            elif finish_reason == "stop":
                                yield {
                                    "content": "",
                                    "tool_calls": [],
                                    "finish_reason": "stop"
                                }

                    except json.JSONDecodeError:
                        continue


def create_llm(provider: str, api_key: str, base_url: str, model: str) -> BaseLLM:
    """创建 LLM 实例的工厂函数

    Args:
        provider: 提供商名称（目前统一使用 OpenAI 兼容接口）
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称

    Returns:
        LLM 实例
    """
    # 所有国产模型都使用 OpenAI 兼容接口
    return OpenAICompatibleLLM(api_key=api_key, base_url=base_url, model=model)
