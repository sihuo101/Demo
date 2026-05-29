from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from database import engine, get_db, Base
from models import Transaction, Category, TransactionType
from schemas import (
    TransactionCreate, TransactionResponse, TransactionListResponse,
    CategoryCreate, CategoryResponse,
    StatisticsResponse, MonthlyStats, CategoryStats
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表已创建")
    yield
    # 关闭时清理
    print("👋 应用已关闭")


app = FastAPI(
    title="记账APP API",
    description="个人记账应用后端接口",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 分类接口 ====================

@app.get("/api/categories", response_model=List[CategoryResponse], tags=["分类"])
def get_categories(
    type: Optional[TransactionType] = None,
    db: Session = Depends(get_db)
):
    """获取分类列表"""
    query = db.query(Category)
    if type:
        query = query.filter(Category.type == type)
    return query.all()


@app.post("/api/categories", response_model=CategoryResponse, tags=["分类"])
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """创建新分类"""
    # 检查是否已存在
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类已存在")

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# ==================== 账单接口 ====================

@app.get("/api/transactions", response_model=TransactionListResponse, tags=["账单"])
def get_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[TransactionType] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取账单列表（分页）"""
    query = db.query(Transaction)

    # 按类型筛选
    if type:
        query = query.filter(Transaction.type == type)

    # 按月份筛选 (格式: 2024-01)
    if month:
        try:
            year, mon = map(int, month.split("-"))
            query = query.filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mon
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="月份格式错误，应为 YYYY-MM")

    # 获取总数
    total = query.count()

    # 分页查询，按日期倒序
    items = query.order_by(Transaction.date.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    return TransactionListResponse(total=total, items=items)


@app.post("/api/transactions", response_model=TransactionResponse, tags=["账单"])
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """创建新账单"""
    db_transaction = Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@app.delete("/api/transactions/{transaction_id}", tags=["账单"])
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """删除账单"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="账单不存在")

    db.delete(transaction)
    db.commit()
    return {"message": "删除成功"}


# ==================== 统计接口 ====================

@app.get("/api/statistics", response_model=StatisticsResponse, tags=["统计"])
def get_statistics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取统计数据"""
    # 如果不指定年份，使用当前年份
    if year is None:
        year = datetime.now().year

    # 查询指定年份的数据
    query = db.query(Transaction).filter(extract("year", Transaction.date) == year)
    transactions = query.all()

    # 计算总收入和总支出
    total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)

    # 按月统计
    monthly_stats = []
    for month in range(1, 13):
        month_transactions = [
            t for t in transactions
            if t.date.month == month
        ]
        month_income = sum(t.amount for t in month_transactions if t.type == TransactionType.INCOME)
        month_expense = sum(t.amount for t in month_transactions if t.type == TransactionType.EXPENSE)

        monthly_stats.append(MonthlyStats(
            month=f"{year}-{month:02d}",
            total_income=month_income,
            total_expense=month_expense,
            balance=month_income - month_expense
        ))

    # 按分类统计（支出）
    expense_transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
    category_dict = {}
    for t in expense_transactions:
        if t.category_name not in category_dict:
            category_dict[t.category_name] = {"total": 0, "count": 0}
        category_dict[t.category_name]["total"] += t.amount
        category_dict[t.category_name]["count"] += 1

    category_stats = [
        CategoryStats(category_name=name, total=data["total"], count=data["count"])
        for name, data in category_dict.items()
    ]
    category_stats.sort(key=lambda x: x.total, reverse=True)

    return StatisticsResponse(
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        monthly_stats=monthly_stats,
        category_stats=category_stats
    )


# ==================== 初始化默认分类 ====================

@app.on_event("startup")
async def init_default_categories():
    """初始化默认分类"""
    db = next(get_db())
    try:
        # 检查是否已有分类
        if db.query(Category).count() == 0:
            default_categories = [
                # 支出分类
                Category(name="餐饮", icon="🍜", type=TransactionType.EXPENSE),
                Category(name="交通", icon="🚗", type=TransactionType.EXPENSE),
                Category(name="购物", icon="🛒", type=TransactionType.EXPENSE),
                Category(name="住房", icon="🏠", type=TransactionType.EXPENSE),
                Category(name="娱乐", icon="🎮", type=TransactionType.EXPENSE),
                Category(name="医疗", icon="💊", type=TransactionType.EXPENSE),
                Category(name="教育", icon="📚", type=TransactionType.EXPENSE),
                Category(name="通讯", icon="📱", type=TransactionType.EXPENSE),
                Category(name="其他支出", icon="📦", type=TransactionType.EXPENSE),
                # 收入分类
                Category(name="工资", icon="💰", type=TransactionType.INCOME),
                Category(name="奖金", icon="🎁", type=TransactionType.INCOME),
                Category(name="投资", icon="📈", type=TransactionType.INCOME),
                Category(name="兼职", icon="💼", type=TransactionType.INCOME),
                Category(name="其他收入", icon="💵", type=TransactionType.INCOME),
            ]
            db.add_all(default_categories)
            db.commit()
            print("✅ 默认分类已初始化")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
