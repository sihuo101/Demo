"""工具定义 - 智能体可调用的工具"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from models import Transaction, Category, TransactionType
from services.calculator import calculator


# ==================== 日期解析工具 ====================

def _parse_date_expr(expr: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """将自然语言日期表达式解析为 (year, month, day)

    支持的表达式：
    - "today" / "今天" → 今天
    - "yesterday" / "昨天" → 昨天
    - "this_month" / "当月" / "本月" / "这个月" → 当前月份
    - "last_month" / "上月" / "上个月" → 上个月
    - "this_year" / "今年" → 当前年份
    - "last_year" / "去年" → 去年
    - "YYYY-MM" → 指定月份
    - "YYYY-MM-DD" → 指定日期
    - "YYYY" → 指定年份

    Returns:
        (year, month, day) 元组，未解析的部分为 None
    """
    if not expr:
        return None, None, None

    expr = expr.strip().lower()
    now = datetime.now()

    # 自然语言映射
    if expr in ("today", "今天", "今日"):
        return now.year, now.month, now.day
    elif expr in ("yesterday", "昨天", "昨日"):
        yesterday = now - timedelta(days=1)
        return yesterday.year, yesterday.month, yesterday.day
    elif expr in ("this_month", "当月", "本月", "这个月", "这个月"):
        return now.year, now.month, None
    elif expr in ("last_month", "上月", "上个月", "上一个月"):
        first_of_this_month = now.replace(day=1)
        last_month = first_of_this_month - timedelta(days=1)
        return last_month.year, last_month.month, None
    elif expr in ("this_year", "今年", "本年"):
        return now.year, None, None
    elif expr in ("last_year", "去年", "上一年"):
        return now.year - 1, None, None

    # 尝试解析 YYYY-MM-DD
    try:
        dt = datetime.strptime(expr, "%Y-%m-%d")
        return dt.year, dt.month, dt.day
    except ValueError:
        pass

    # 尝试解析 YYYY-MM
    try:
        parts = expr.split("-")
        if len(parts) == 2:
            year, month = int(parts[0]), int(parts[1])
            if 1 <= month <= 12:
                return year, month, None
    except (ValueError, IndexError):
        pass

    # 尝试解析 YYYY
    try:
        year = int(expr)
        if 1900 <= year <= 2100:
            return year, None, None
    except ValueError:
        pass

    return None, None, None


def _resolve_month(expr: Optional[str]) -> Optional[str]:
    """将日期表达式解析为 YYYY-MM 格式字符串

    Args:
        expr: 日期表达式（如 "this_month", "last_month", "2026-05" 等）

    Returns:
        YYYY-MM 格式字符串，或 None
    """
    if not expr:
        now = datetime.now()
        return f"{now.year}-{now.month:02d}"

    year, month, _ = _parse_date_expr(expr)
    if year and month:
        return f"{year}-{month:02d}"
    elif year:
        return f"{year}"

    # 解析失败，返回当月
    now = datetime.now()
    return f"{now.year}-{now.month:02d}"


# ==================== 工具定义 ====================

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "获取当前日期和时间信息。当用户提到'今天'、'当月'、'本月'、'这个月'、'今年'等相对时间概念时，先调用此工具获取准确日期。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_transaction",
            "description": "创建新的账单记录（记账/入账）。当用户提到消费、支出、收入、花费、到账等财务操作时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "金额，必须大于0"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "交易类型：income(收入) 或 expense(支出)"
                    },
                    "category_name": {
                        "type": "string",
                        "description": "分类名称，如：餐饮、交通、购物、工资等"
                    },
                    "note": {
                        "type": "string",
                        "description": "备注信息（可选）"
                    },
                    "date": {
                        "type": "string",
                        "description": "交易日期，格式 YYYY-MM-DD，默认为今天"
                    }
                },
                "required": ["amount", "type", "category_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "查询账单记录。当用户想查看账单、交易记录、消费明细时使用。支持自然语言日期：today/yesterday/this_month/last_month/this_year/last_year，或 YYYY-MM/YYYY-MM-DD 格式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "description": "日期表达式，支持：today(今天), this_month(当月), last_month(上月), this_year(今年), last_year(去年), 或 YYYY-MM/YYYY-MM-DD 格式"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "交易类型筛选"
                    },
                    "category_name": {
                        "type": "string",
                        "description": "分类名称筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认10"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_categories",
            "description": "获取分类列表。当用户想知道有哪些分类、或者不确定分类名称时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "分类类型筛选"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_transaction",
            "description": "删除账单记录。当用户要求删除、撤销某笔账单时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "要删除的账单ID"
                    }
                },
                "required": ["transaction_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_statistics",
            "description": "获取统计数据。当用户询问总收入、总支出、结余、月度统计、分类统计、花销总结时使用。支持自然语言日期：today/this_month/last_month/this_year/last_year，或 YYYY-MM 格式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "年份，默认当前年份"
                    },
                    "month": {
                        "type": "string",
                        "description": "日期表达式，支持：this_month(当月), last_month(上月), this_year(今年), 或 YYYY-MM 格式。当用户说'当月花销'时传 this_month"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算或账单相关计算。当用户要求计算、求和、平均值、占比、对比等操作时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "calc_type": {
                        "type": "string",
                        "enum": [
                            "arithmetic",
                            "bill_summary",
                            "daily_average",
                            "ratio",
                            "month_comparison",
                            "growth_rate",
                            "predict_savings",
                            "category_breakdown"
                        ],
                        "description": """计算类型：
- arithmetic: 基础算术计算
- bill_summary: 账单汇总（求和、平均、最大、最小）
- daily_average: 日均支出计算
- ratio: 占比计算
- month_comparison: 月度对比
- growth_rate: 增长率计算
- predict_savings: 储蓄预测
- category_breakdown: 分类明细"""
                    },
                    "params": {
                        "type": "object",
                        "description": "计算参数",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "数学表达式（用于 arithmetic 类型）"
                            },
                            "month": {
                                "type": "string",
                                "description": "月份，格式 YYYY-MM"
                            },
                            "month1": {
                                "type": "string",
                                "description": "月份1（用于 month_comparison）"
                            },
                            "month2": {
                                "type": "string",
                                "description": "月份2（用于 month_comparison）"
                            },
                            "category": {
                                "type": "string",
                                "description": "分类名称"
                            },
                            "transaction_type": {
                                "type": "string",
                                "enum": ["income", "expense"],
                                "description": "交易类型"
                            },
                            "current": {
                                "type": "number",
                                "description": "当前值（用于 growth_rate）"
                            },
                            "previous": {
                                "type": "number",
                                "description": "之前值（用于 growth_rate）"
                            },
                            "monthly_save": {
                                "type": "number",
                                "description": "每月储蓄金额（用于 predict_savings）"
                            },
                            "months": {
                                "type": "integer",
                                "description": "月数（用于 predict_savings）"
                            },
                            "annual_rate": {
                                "type": "number",
                                "description": "年利率百分比（用于 predict_savings）"
                            }
                        }
                    }
                },
                "required": ["calc_type"]
            }
        }
    }
]


# ==================== 工具执行 ====================

def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """执行工具调用

    Args:
        tool_name: 工具名称
        arguments: 工具参数
        db: 数据库会话

    Returns:
        工具执行结果
    """
    try:
        if tool_name == "get_current_date":
            return _get_current_date()
        elif tool_name == "create_transaction":
            return _create_transaction(arguments, db)
        elif tool_name == "get_transactions":
            return _get_transactions(arguments, db)
        elif tool_name == "get_categories":
            return _get_categories(arguments, db)
        elif tool_name == "delete_transaction":
            return _delete_transaction(arguments, db)
        elif tool_name == "get_statistics":
            return _get_statistics(arguments, db)
        elif tool_name == "calculate":
            return _calculate(arguments, db)
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": f"工具执行错误: {str(e)}"}


def _get_current_date() -> Dict[str, Any]:
    """获取当前日期时间信息"""
    now = datetime.now()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return {
        "success": True,
        "date": now.strftime("%Y-%m-%d"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "weekday": weekday_names[now.weekday()],
        "time": now.strftime("%H:%M:%S"),
        "this_month": f"{now.year}-{now.month:02d}",
        "last_month_date": (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
        "message": f"今天是 {now.year}年{now.month}月{now.day}日 {weekday_names[now.weekday()]}"
    }


def _create_transaction(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """创建账单"""
    amount = args.get("amount")
    trans_type = args.get("type")
    category_name = args.get("category_name")
    note = args.get("note", "")
    date_str = args.get("date")

    # 验证金额
    if not amount or amount <= 0:
        return {"success": False, "error": "金额必须大于0"}

    # 解析日期
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "error": "日期格式错误，应为 YYYY-MM-DD"}
    else:
        date = datetime.now()

    # 查找分类
    category = db.query(Category).filter(
        Category.name == category_name,
        Category.type == trans_type
    ).first()

    if not category:
        # 尝试模糊匹配
        category = db.query(Category).filter(
            Category.name.like(f"%{category_name}%"),
            Category.type == trans_type
        ).first()

    if not category:
        return {
            "success": False,
            "error": f"未找到分类: {category_name}",
            "suggestion": "请使用 get_categories 工具查看可用分类"
        }

    # 创建账单
    transaction = Transaction(
        amount=round(amount, 2),
        type=trans_type,
        category_id=category.id,
        category_name=category.name,
        note=note,
        date=date
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    type_label = "收入" if trans_type == "income" else "支出"

    return {
        "success": True,
        "transaction_id": transaction.id,
        "amount": round(amount, 2),
        "type": type_label,
        "category": category.name,
        "category_icon": category.icon,
        "note": note,
        "date": date.strftime("%Y-%m-%d"),
        "message": f"已记录{type_label}：{category.icon} {category.name} {round(amount, 2)} 元"
    }


def _get_transactions(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """查询账单"""
    query = db.query(Transaction)

    # 按月份筛选（支持自然语言日期表达式）
    month_expr = args.get("month")
    if month_expr:
        resolved = _resolve_month(month_expr)
        if resolved:
            try:
                parts = resolved.split("-")
                if len(parts) == 2:
                    year, mon = int(parts[0]), int(parts[1])
                    query = query.filter(
                        extract("year", Transaction.date) == year,
                        extract("month", Transaction.date) == mon
                    )
                elif len(parts) == 1:
                    year = int(parts[0])
                    query = query.filter(
                        extract("year", Transaction.date) == year
                    )
            except (ValueError, IndexError):
                return {"success": False, "error": f"日期解析失败: {month_expr}"}

    # 按类型筛选
    trans_type = args.get("type")
    if trans_type:
        query = query.filter(Transaction.type == trans_type)

    # 按分类筛选
    category_name = args.get("category_name")
    if category_name:
        query = query.filter(Transaction.category_name.like(f"%{category_name}%"))

    # 限制数量
    limit = args.get("limit", 10)
    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()

    # 格式化结果
    items = []
    for t in transactions:
        type_label = "收入" if t.type == TransactionType.INCOME else "支出"
        items.append({
            "id": t.id,
            "amount": round(t.amount, 2),
            "type": type_label,
            "category": t.category_name,
            "note": t.note,
            "date": t.date.strftime("%Y-%m-%d")
        })

    return {
        "success": True,
        "count": len(items),
        "transactions": items
    }


def _get_categories(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """获取分类"""
    query = db.query(Category)

    trans_type = args.get("type")
    if trans_type:
        query = query.filter(Category.type == trans_type)

    categories = query.all()

    items = []
    for c in categories:
        type_label = "收入" if c.type == TransactionType.INCOME else "支出"
        items.append({
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "type": type_label
        })

    return {
        "success": True,
        "categories": items
    }


def _delete_transaction(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """删除账单"""
    transaction_id = args.get("transaction_id")

    if not transaction_id:
        return {"success": False, "error": "请提供账单ID"}

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        return {"success": False, "error": f"未找到账单ID: {transaction_id}"}

    # 保存信息用于返回
    type_label = "收入" if transaction.type == TransactionType.INCOME else "支出"
    info = {
        "id": transaction.id,
        "amount": round(transaction.amount, 2),
        "type": type_label,
        "category": transaction.category_name,
        "date": transaction.date.strftime("%Y-%m-%d")
    }

    db.delete(transaction)
    db.commit()

    return {
        "success": True,
        "deleted": info,
        "message": f"已删除{type_label}：{info['category']} {info['amount']} 元"
    }


def _get_statistics(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """获取统计"""
    now = datetime.now()
    year = args.get("year", now.year)
    month_expr = args.get("month")

    if month_expr:
        # 单月统计（支持自然语言日期表达式）
        resolved = _resolve_month(month_expr)
        try:
            parts = resolved.split("-")
            y, m = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return {"success": False, "error": f"日期解析失败: {month_expr}"}

        transactions = db.query(Transaction).filter(
            extract("year", Transaction.date) == y,
            extract("month", Transaction.date) == m
        ).all()
    else:
        # 年度统计
        transactions = db.query(Transaction).filter(
            extract("year", Transaction.date) == year
        ).all()

    total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)

    # 分类统计
    expense_by_category = {}
    for t in transactions:
        if t.type == TransactionType.EXPENSE:
            if t.category_name not in expense_by_category:
                expense_by_category[t.category_name] = 0
            expense_by_category[t.category_name] += t.amount

    category_stats = [
        {"category": k, "total": round(v, 2)}
        for k, v in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "success": True,
        "year": year,
        "month": month,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "balance": round(total_income - total_expense, 2),
        "category_stats": category_stats
    }


def _calculate(args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """执行计算"""
    calc_type = args.get("calc_type")
    params = args.get("params", {})

    if calc_type == "arithmetic":
        expression = params.get("expression", "")
        return calculator.arithmetic(expression)

    elif calc_type == "bill_summary":
        return calculator.bill_summary(
            db,
            month=params.get("month"),
            category=params.get("category"),
            transaction_type=params.get("transaction_type")
        )

    elif calc_type == "daily_average":
        return calculator.daily_average(
            db,
            month=params.get("month")
        )

    elif calc_type == "ratio":
        return calculator.ratio(
            db,
            month=params.get("month"),
            category=params.get("category"),
            transaction_type=params.get("transaction_type", "expense")
        )

    elif calc_type == "month_comparison":
        return calculator.month_comparison(
            db,
            month1=params.get("month1"),
            month2=params.get("month2"),
            transaction_type=params.get("transaction_type", "expense")
        )

    elif calc_type == "growth_rate":
        return calculator.growth_rate(
            current=params.get("current", 0),
            previous=params.get("previous", 0)
        )

    elif calc_type == "predict_savings":
        return calculator.predict_savings(
            monthly_save=params.get("monthly_save", 0),
            months=params.get("months", 12),
            annual_rate=params.get("annual_rate", 0)
        )

    elif calc_type == "category_breakdown":
        return calculator.category_breakdown(
            db,
            month=params.get("month"),
            transaction_type=params.get("transaction_type", "expense")
        )

    else:
        return {"success": False, "error": f"未知计算类型: {calc_type}"}
