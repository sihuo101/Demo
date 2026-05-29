from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    INCOME = "income"   # 收入
    EXPENSE = "expense" # 支出


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Category(Base):
    """分类模型"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="分类名称")
    icon = Column(String(50), default="📦", comment="分类图标")
    type = Column(Enum(TransactionType), nullable=False, comment="分类类型: income/expense")
    created_at = Column(DateTime, server_default=func.now())


class Transaction(Base):
    """账单模型"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Float, nullable=False, comment="金额")
    type = Column(Enum(TransactionType), nullable=False, comment="类型: income/expense")
    category_id = Column(Integer, nullable=False, comment="分类ID")
    category_name = Column(String(50), nullable=False, comment="分类名称")
    note = Column(String(200), default="", comment="备注")
    date = Column(DateTime, nullable=False, comment="交易日期")
    created_at = Column(DateTime, server_default=func.now())


class Conversation(Base):
    """对话模型"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), default="新对话", comment="对话标题")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联消息
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False, comment="消息角色")
    content = Column(Text, nullable=False, comment="消息内容")
    metadata_json = Column(JSON, default=None, comment="附加数据（工具调用结果等）")
    created_at = Column(DateTime, server_default=func.now())

    # 关联对话
    conversation = relationship("Conversation", back_populates="messages")
