"""智能体服务 - 核心对话逻辑"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import Conversation, Message, MessageRole
from services.llm.providers import create_llm
from services.tools import TOOLS_DEFINITION, execute_tool
from config import settings


# 系统提示词
SYSTEM_PROMPT = """你是一个智能记账助手，可以帮助用户完成以下任务：

1. **记账/入账**：帮用户记录收入和支出
   - 识别用户的消费或收入描述
   - 自动匹配合适的分类
   - 记录金额、分类、备注、日期

2. **查询账单**：帮用户查看历史账单
   - 按时间、分类、类型筛选
   - 展示详细的账单列表

3. **统计分析**：帮用户分析财务状况
   - 收支统计
   - 分类占比
   - 趋势分析

4. **数学计算**：帮用户进行各种计算
   - 基础算术（加减乘除）
   - 账单相关计算（求和、平均、占比）
   - 对比计算（月度对比、增长率）
   - 预测计算（储蓄预测）

5. **账单管理**：帮用户删除账单

## 使用规则

1. 当用户提到消费、支出、花费、买了、花了等，识别为**支出**
2. 当用户提到收入、到账、工资、赚了等，识别为**收入**
3. 如果用户没有明确日期，使用今天的日期
4. 金额需要从用户描述中提取，支持"元"、"块"、"¥"等单位
5. 尽量自动匹配分类，如果不确定可以询问用户
6. 对于计算请求，使用 calculate 工具执行
7. 回复要简洁明了，使用 emoji 增加可读性

## 分类参考

支出分类：餐饮🍜、交通🚗、购物🛒、住房🏠、娱乐🎮、医疗💊、教育📚、通讯📱、其他支出📦
收入分类：工资💰、奖金🎁、投资📈、兼职💼、其他收入💵

## 回复格式

- 记账成功：简要确认记录的内容
- 查询结果：以列表形式展示
- 统计结果：突出关键数字
- 计算结果：展示计算过程和结果
"""


class AgentService:
    """智能体服务"""

    def __init__(self):
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM"""
        if settings.LLM_API_KEY and settings.LLM_BASE_URL and settings.LLM_MODEL:
            self.llm = create_llm(
                provider=settings.LLM_PROVIDER,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL
            )

    def is_configured(self) -> bool:
        """检查 LLM 是否已配置"""
        return self.llm is not None

    def _build_messages(
        self,
        conversation: Conversation,
        new_message: str
    ) -> List[Dict[str, str]]:
        """构建消息列表

        Args:
            conversation: 对话对象
            new_message: 新消息

        Returns:
            消息列表
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 添加历史消息（最近20条）
        history = conversation.messages[-20:] if conversation.messages else []
        for msg in history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        # 添加新消息
        messages.append({"role": "user", "content": new_message})

        return messages

    async def chat(
        self,
        db: Session,
        conversation_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """普通对话

        Args:
            db: 数据库会话
            conversation_id: 对话ID
            user_message: 用户消息

        Returns:
            包含助手回复和工具调用结果的字典
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "LLM 未配置，请在 .env 文件中配置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL"
            }

        # 获取对话
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return {"success": False, "error": "对话不存在"}

        # 保存用户消息
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # 构建消息列表
        messages = self._build_messages(conversation, user_message)

        # 调用 LLM
        try:
            result = await self.llm.chat(messages, tools=TOOLS_DEFINITION)
        except Exception as e:
            return {"success": False, "error": f"LLM 调用失败: {str(e)}"}

        # 处理工具调用
        tool_results = []
        if result.get("tool_calls"):
            for tool_call in result["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                # 执行工具
                tool_result = execute_tool(tool_name, arguments, db)
                tool_results.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })

            # 将工具结果添加到消息列表，再次调用 LLM 生成最终回复
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": result["tool_calls"]
            })

            for i, tool_call in enumerate(result["tool_calls"]):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_results[i]["result"], ensure_ascii=False)
                })

            # 再次调用 LLM 生成回复
            try:
                final_result = await self.llm.chat(messages, tools=TOOLS_DEFINITION)
                assistant_content = final_result.get("content", "处理完成")
            except Exception as e:
                assistant_content = f"工具执行完成，但生成回复时出错: {str(e)}"
        else:
            assistant_content = result.get("content", "抱歉，我没有理解您的意思")

        # 保存助手消息
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            metadata_json={"tool_calls": tool_results} if tool_results else None
        )
        db.add(assistant_msg)

        # 更新对话标题（如果是新对话且标题是默认的）
        if conversation.title == "新对话":
            # 使用用户消息的前20个字符作为标题
            conversation.title = user_message[:20] + ("..." if len(user_message) > 20 else "")

        conversation.updated_at = datetime.now()
        db.commit()
        db.refresh(assistant_msg)

        return {
            "success": True,
            "message": {
                "id": assistant_msg.id,
                "role": "assistant",
                "content": assistant_content,
                "created_at": assistant_msg.created_at.isoformat()
            },
            "tool_calls": tool_results if tool_results else None
        }

    async def chat_stream(
        self,
        db: Session,
        conversation_id: int,
        user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话

        Args:
            db: 数据库会话
            conversation_id: 对话ID
            user_message: 用户消息

        Yields:
            流式响应片段
        """
        if not self.is_configured():
            yield {
                "type": "error",
                "content": "LLM 未配置，请在 .env 文件中配置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL"
            }
            return

        # 获取对话
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            yield {"type": "error", "content": "对话不存在"}
            return

        # 保存用户消息
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # 构建消息列表
        messages = self._build_messages(conversation, user_message)

        # 发送开始标记
        yield {"type": "start", "content": ""}

        # 流式调用 LLM
        full_content = ""
        tool_calls = []

        try:
            async for chunk in self.llm.chat_stream(messages, tools=TOOLS_DEFINITION):
                # 处理文本内容
                if chunk.get("content"):
                    full_content += chunk["content"]
                    yield {
                        "type": "content",
                        "content": chunk["content"]
                    }

                # 处理工具调用
                if chunk.get("tool_calls"):
                    tool_calls = chunk["tool_calls"]

                # 处理结束
                if chunk.get("finish_reason") == "tool_calls" and tool_calls:
                    # 执行工具
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"])
                        except json.JSONDecodeError:
                            arguments = {}

                        yield {
                            "type": "tool_start",
                            "tool": tool_name,
                            "arguments": arguments
                        }

                        # 执行工具
                        tool_result = execute_tool(tool_name, arguments, db)
                        tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": tool_result
                        })

                        yield {
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": tool_result
                        }

                    # 将工具结果添加到消息列表
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls
                    })

                    for i, tool_call in enumerate(tool_calls):
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_results[i]["result"], ensure_ascii=False)
                        })

                    # 再次调用 LLM 生成最终回复
                    yield {"type": "content", "content": "\n\n"}

                    final_content = ""
                    async for final_chunk in self.llm.chat_stream(messages, tools=TOOLS_DEFINITION):
                        if final_chunk.get("content"):
                            final_content += final_chunk["content"]
                            yield {
                                "type": "content",
                                "content": final_chunk["content"]
                            }

                        if final_chunk.get("finish_reason") == "stop":
                            break

                    full_content = final_content

        except Exception as e:
            yield {
                "type": "error",
                "content": f"LLM 调用失败: {str(e)}"
            }
            return

        # 保存助手消息
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=full_content,
            metadata_json={"tool_calls": tool_results} if tool_calls else None
        )
        db.add(assistant_msg)

        # 更新对话标题
        if conversation.title == "新对话":
            conversation.title = user_message[:20] + ("..." if len(user_message) > 20 else "")

        conversation.updated_at = datetime.now()
        db.commit()

        # 发送结束标记
        yield {
            "type": "end",
            "message_id": assistant_msg.id
        }


# 创建全局实例
agent_service = AgentService()
