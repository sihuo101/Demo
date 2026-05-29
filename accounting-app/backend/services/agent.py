"""智能体服务 - 核心对话逻辑"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import Conversation, Message, MessageRole
from services.llm.providers import create_llm
from services.tools import TOOLS_DEFINITION, execute_tool
from config import settings


# 系统提示词模板（{current_date} 会在运行时替换为当前日期）
SYSTEM_PROMPT_TEMPLATE = """你是一个智能记账助手，当前日期：{current_date}。可以帮助用户完成以下任务：

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

## 日期查询规则（重要！）

当用户提到相对时间概念时，**必须**使用工具查询，不要自己推算：
- "当月"、"本月"、"这个月" → 使用 get_statistics(month="this_month") 或 get_transactions(month="this_month")
- "上个月"、"上月" → 使用 get_statistics(month="last_month") 或 get_transactions(month="last_month")
- "今年" → 使用 get_statistics(year=当前年份) 或 get_transactions(month="this_year")
- "去年" → 使用 get_statistics(year=去年年份) 或 get_transactions(month="last_year")
- "今天" → 使用 get_transactions(month="today")
- 不确定日期时，先调用 get_current_date 工具获取准确日期

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
        """构建消息列表（包含工具调用历史，确保 LLM 能看到完整的上下文）

        Args:
            conversation: 对话对象
            new_message: 新消息

        Returns:
            消息列表
        """
        # 动态注入当前日期到系统提示词
        now = datetime.now()
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        current_date = f"{now.year}年{now.month}月{now.day}日 {weekday_names[now.weekday()]} {now.strftime('%H:%M')}"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(current_date=current_date)
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史消息（最近20条）
        history = conversation.messages[-20:] if conversation.messages else []
        for msg in history:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
            # 如果有工具调用记录，还原到消息列表中
            # 这样 LLM 就能看到之前执行了什么工具、返回了什么结果
            if msg.metadata_json and "tool_call_messages" in msg.metadata_json:
                messages.extend(msg.metadata_json["tool_call_messages"])

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
        tool_call_messages_for_history = []
        if result.get("tool_calls"):
            # 将 assistant 的工具调用消息加入历史（同时记录用于持久化）
            assistant_tool_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": result["tool_calls"]
            }
            messages.append(assistant_tool_msg)
            tool_call_messages_for_history.append(assistant_tool_msg)

            for i, tool_call in enumerate(result["tool_calls"]):
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

                # 将工具结果加入消息列表（同时记录用于持久化）
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
                messages.append(tool_result_msg)
                tool_call_messages_for_history.append(tool_result_msg)

            # 再次调用 LLM 生成回复
            try:
                final_result = await self.llm.chat(messages, tools=TOOLS_DEFINITION)
                assistant_content = final_result.get("content", "处理完成")
            except Exception as e:
                assistant_content = f"工具执行完成，但生成回复时出错: {str(e)}"
        else:
            assistant_content = result.get("content", "抱歉，我没有理解您的意思")

        # 保存助手消息（包含工具调用历史，供后续对话还原上下文）
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            metadata_json={
                "tool_calls": tool_results,
                "tool_call_messages": tool_call_messages_for_history
            } if tool_results else None
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
        """流式对话（支持多轮工具调用）

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

        full_content = ""
        all_tool_results = []
        has_tool_calls = False
        # 收集完整的工具调用消息，存入数据库供后续对话还原上下文
        tool_call_messages_for_history = []

        try:
            # 支持多轮工具调用（最多 5 轮，防止无限循环）
            for round_num in range(5):
                tool_calls = []
                round_content = ""

                # 流式读取 LLM 响应
                async for chunk in self.llm.chat_stream(messages, tools=TOOLS_DEFINITION):
                    if chunk.get("content"):
                        chunk_text = chunk["content"]
                        round_content += chunk_text
                        yield {
                            "type": "content",
                            "content": chunk_text
                        }

                    if chunk.get("tool_calls"):
                        tool_calls = chunk["tool_calls"]

                    # 收到 finish_reason 就退出内层循环
                    if chunk.get("finish_reason"):
                        break

                # 没有工具调用，说明 LLM 已生成最终回复
                if not tool_calls:
                    full_content = round_content
                    break

                # 有工具调用，执行工具
                has_tool_calls = True

                # 将 assistant 的工具调用消息加入历史（同时记录用于持久化）
                assistant_tool_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                }
                messages.append(assistant_tool_msg)
                tool_call_messages_for_history.append(assistant_tool_msg)

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
                    all_tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": tool_result
                    })

                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": tool_result
                    }

                    # 将工具结果加入消息列表，供下一轮 LLM 调用（同时记录用于持久化）
                    tool_result_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    }
                    messages.append(tool_result_msg)
                    tool_call_messages_for_history.append(tool_result_msg)

                yield {"type": "content", "content": "\n\n"}

        except Exception as e:
            yield {
                "type": "error",
                "content": f"LLM 调用失败: {str(e)}"
            }
            return

        # 保存助手消息（包含工具调用历史，供后续对话还原上下文）
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=full_content,
            metadata_json={
                "tool_calls": all_tool_results,
                "tool_call_messages": tool_call_messages_for_history
            } if has_tool_calls else None
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
