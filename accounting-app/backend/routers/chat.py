"""聊天路由 - 智能体对话接口"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator

from database import get_db
from schemas import ChatRequest, ChatResponse, MessageResponse
from services.agent import agent_service

router = APIRouter(prefix="/api/chat", tags=["聊天"])


async def stream_generator(
    conversation_id: int,
    content: str,
    db: Session
) -> AsyncGenerator[str, None]:
    """生成 SSE 流式响应

    Args:
        conversation_id: 对话ID
        content: 用户消息
        db: 数据库会话

    Yields:
        SSE 格式的事件
    """
    async for event in agent_service.chat_stream(db, conversation_id, content):
        event_type = event.get("type", "message")
        data = json.dumps(event, ensure_ascii=False)
        yield f"event: {event_type}\ndata: {data}\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """普通聊天接口（非流式）

    Args:
        request: 聊天请求
        db: 数据库会话

    Returns:
        聊天响应
    """
    result = await agent_service.chat(
        db=db,
        conversation_id=request.conversation_id,
        user_message=request.content
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "聊天失败")
        )

    return result


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """流式聊天接口

    Args:
        request: 聊天请求
        db: 数据库会话

    Returns:
        SSE 流式响应
    """
    return StreamingResponse(
        stream_generator(
            conversation_id=request.conversation_id,
            content=request.content,
            db=db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status")
async def chat_status():
    """检查智能体状态

    Returns:
        智能体配置状态
    """
    return {
        "configured": agent_service.is_configured(),
        "message": "智能体已就绪" if agent_service.is_configured() else "LLM 未配置"
    }
