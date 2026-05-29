"""对话管理路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from database import get_db
from models import Conversation, Message
from schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/conversations", tags=["对话"])


@router.get("", response_model=List[ConversationResponse])
def get_conversations(db: Session = Depends(get_db)):
    """获取对话列表"""
    # 查询对话及其消息数量
    conversations = db.query(
        Conversation,
        func.count(Message.id).label("message_count")
    ).outerjoin(
        Message, Conversation.id == Message.conversation_id
    ).group_by(
        Conversation.id
    ).order_by(
        Conversation.updated_at.desc()
    ).all()

    result = []
    for conv, msg_count in conversations:
        result.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))

    return result


@router.post("", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate = None,
    db: Session = Depends(get_db)
):
    """创建新对话"""
    if data is None:
        data = ConversationCreate()

    conversation = Conversation(title=data.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0
    )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """删除对话"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.delete(conversation)
    db.commit()

    return {"message": "删除成功"}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """获取对话消息列表"""
    # 检查对话是否存在
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return messages


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: int,
    data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """更新对话标题"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    conversation.title = data.title
    db.commit()

    return {"message": "更新成功"}
