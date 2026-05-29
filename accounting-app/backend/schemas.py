from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import TransactionType, MessageRole


# ==================== 分类相关 ====================

class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: str = Field(default="📦", description="分类图标")
    type: TransactionType = Field(..., description="分类类型")


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    pass


class CategoryResponse(CategoryBase):
    """分类响应模型"""
    id: int

    class Config:
        from_attributes = True


# ==================== 账单相关 ====================

class TransactionBase(BaseModel):
    """账单基础模型"""
    amount: float = Field(..., gt=0, description="金额")
    type: TransactionType = Field(..., description="类型: income/expense")
    category_id: int = Field(..., description="分类ID")
    category_name: str = Field(..., description="分类名称")
    note: Optional[str] = Field(default="", max_length=200, description="备注")
    date: datetime = Field(..., description="交易日期")


class TransactionCreate(TransactionBase):
    """创建账单请求"""
    pass


class TransactionResponse(TransactionBase):
    """账单响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """账单列表响应"""
    total: int
    items: List[TransactionResponse]


# ==================== 统计相关 ====================

class MonthlyStats(BaseModel):
    """月度统计"""
    month: str
    total_income: float
    total_expense: float
    balance: float


class CategoryStats(BaseModel):
    """分类统计"""
    category_name: str
    total: float
    count: int


class StatisticsResponse(BaseModel):
    """统计响应"""
    total_income: float
    total_expense: float
    balance: float
    monthly_stats: List[MonthlyStats]
    category_stats: List[CategoryStats]


# ==================== 对话相关 ====================

class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: Optional[str] = Field(default="新对话", max_length=100, description="对话标题")


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """创建消息请求"""
    content: str = Field(..., min_length=1, description="消息内容")


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """聊天请求"""
    conversation_id: int = Field(..., description="对话ID")
    content: str = Field(..., min_length=1, description="消息内容")


class ChatResponse(BaseModel):
    """聊天响应"""
    message: MessageResponse
    tool_calls: Optional[List[Dict[str, Any]]] = None


class STTResponse(BaseModel):
    """语音识别响应"""
    text: str
