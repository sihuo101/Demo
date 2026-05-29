from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    INCOME = "income"   # 收入
    EXPENSE = "expense" # 支出


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
