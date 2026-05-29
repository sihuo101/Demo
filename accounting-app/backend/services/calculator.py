"""计算服务 - 提供各种计算能力"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from models import Transaction, TransactionType


class CalculatorService:
    """计算器服务"""

    # 安全的数学运算字符
    SAFE_CHARS = set("0123456789+-*/.() %")

    @staticmethod
    def round(value: float, digits: int = 2) -> float:
        """四舍五入到指定小数位"""
        return round(value, digits)

    def arithmetic(self, expression: str) -> Dict[str, Any]:
        """基础算术计算

        Args:
            expression: 数学表达式，如 "125 + 378" 或 "(100 + 200) * 0.15"

        Returns:
            包含结果的字典
        """
        try:
            # 清理表达式
            expr = expression.strip()

            # 安全检查：只允许数字和运算符
            if not all(c in self.SAFE_CHARS for c in expr):
                return {
                    "success": False,
                    "error": "表达式包含不安全的字符"
                }

            # 替换中文符号
            expr = expr.replace("×", "*").replace("÷", "/").replace("％", "%")

            # 计算
            result = eval(expr)

            return {
                "success": True,
                "expression": expression,
                "result": self.round(float(result)),
                "formatted": f"{expression} = {self.round(float(result))}"
            }
        except ZeroDivisionError:
            return {
                "success": False,
                "error": "除数不能为零"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"计算错误: {str(e)}"
            }

    def bill_summary(
        self,
        db: Session,
        month: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """账单汇总计算

        Args:
            db: 数据库会话
            month: 月份，格式 YYYY-MM
            category: 分类名称
            transaction_type: 交易类型 income/expense

        Returns:
            汇总结果
        """
        query = db.query(Transaction)

        # 按月份筛选
        if month:
            try:
                year, mon = map(int, month.split("-"))
                query = query.filter(
                    extract("year", Transaction.date) == year,
                    extract("month", Transaction.date) == mon
                )
            except ValueError:
                return {"success": False, "error": "月份格式错误，应为 YYYY-MM"}

        # 按分类筛选
        if category:
            query = query.filter(Transaction.category_name == category)

        # 按类型筛选
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)

        transactions = query.all()

        if not transactions:
            return {
                "success": True,
                "total": 0,
                "count": 0,
                "average": 0,
                "max": 0,
                "min": 0,
                "transactions": []
            }

        amounts = [t.amount for t in transactions]

        return {
            "success": True,
            "total": self.round(sum(amounts)),
            "count": len(amounts),
            "average": self.round(sum(amounts) / len(amounts)),
            "max": self.round(max(amounts)),
            "min": self.round(min(amounts)),
            "month": month,
            "category": category,
            "type": transaction_type
        }

    def daily_average(
        self,
        db: Session,
        month: Optional[str] = None
    ) -> Dict[str, Any]:
        """日均支出计算

        Args:
            db: 数据库会话
            month: 月份，格式 YYYY-MM

        Returns:
            日均结果
        """
        if not month:
            now = datetime.now()
            month = f"{now.year}-{now.month:02d}"

        try:
            year, mon = map(int, month.split("-"))
        except ValueError:
            return {"success": False, "error": "月份格式错误"}

        # 查询指定月份的支出
        transactions = db.query(Transaction).filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mon,
            Transaction.type == TransactionType.EXPENSE
        ).all()

        if not transactions:
            return {
                "success": True,
                "daily_average": 0,
                "total": 0,
                "days_with_records": 0,
                "month": month
            }

        total = sum(t.amount for t in transactions)

        # 计算有记录的天数
        unique_days = len(set(t.date.date() for t in transactions))

        # 计算当月天数
        if mon == 12:
            days_in_month = 31
        else:
            next_month = datetime(year, mon + 1, 1)
            this_month = datetime(year, mon, 1)
            days_in_month = (next_month - this_month).days

        return {
            "success": True,
            "daily_average_by_days": self.round(total / days_in_month),
            "daily_average_by_records": self.round(total / unique_days) if unique_days > 0 else 0,
            "total": self.round(total),
            "days_in_month": days_in_month,
            "days_with_records": unique_days,
            "month": month
        }

    def ratio(
        self,
        db: Session,
        month: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: str = "expense"
    ) -> Dict[str, Any]:
        """占比计算

        Args:
            db: 数据库会话
            month: 月份
            category: 分类名称
            transaction_type: 交易类型

        Returns:
            占比结果
        """
        if not month:
            now = datetime.now()
            month = f"{now.year}-{now.month:02d}"

        try:
            year, mon = map(int, month.split("-"))
        except ValueError:
            return {"success": False, "error": "月份格式错误"}

        # 查询总金额
        total_query = db.query(func.sum(Transaction.amount)).filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mon,
            Transaction.type == transaction_type
        )
        total = total_query.scalar() or 0

        # 查询分类金额
        if category:
            part_query = db.query(func.sum(Transaction.amount)).filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mon,
                Transaction.type == transaction_type,
                Transaction.category_name == category
            )
            part = part_query.scalar() or 0
        else:
            part = total

        ratio_value = (part / total * 100) if total > 0 else 0

        return {
            "success": True,
            "part": self.round(part),
            "total": self.round(total),
            "ratio": self.round(ratio_value),
            "formatted": f"{self.round(ratio_value)}%",
            "category": category,
            "month": month,
            "type": transaction_type
        }

    def month_comparison(
        self,
        db: Session,
        month1: str,
        month2: str,
        transaction_type: str = "expense"
    ) -> Dict[str, Any]:
        """月度对比计算

        Args:
            db: 数据库会话
            month1: 月份1（当月）
            month2: 月份2（上月）
            transaction_type: 交易类型

        Returns:
            对比结果
        """
        def get_month_total(month_str: str) -> float:
            try:
                year, mon = map(int, month_str.split("-"))
                total = db.query(func.sum(Transaction.amount)).filter(
                    extract("year", Transaction.date) == year,
                    extract("month", Transaction.date) == mon,
                    Transaction.type == transaction_type
                ).scalar()
                return total or 0
            except:
                return 0

        total1 = get_month_total(month1)
        total2 = get_month_total(month2)

        diff = total1 - total2
        growth_rate = (diff / total2 * 100) if total2 > 0 else 0

        return {
            "success": True,
            "month1": month1,
            "month2": month2,
            "total1": self.round(total1),
            "total2": self.round(total2),
            "difference": self.round(diff),
            "growth_rate": self.round(growth_rate),
            "type": transaction_type,
            "formatted": f"{'增加' if diff >= 0 else '减少'} {self.round(abs(diff))} 元（{'+' if growth_rate >= 0 else ''}{self.round(growth_rate)}%）"
        }

    def growth_rate(self, current: float, previous: float) -> Dict[str, Any]:
        """增长率计算

        Args:
            current: 当前值
            previous: 之前值

        Returns:
            增长率结果
        """
        if previous == 0:
            rate = 100 if current > 0 else 0
        else:
            rate = (current - previous) / abs(previous) * 100

        return {
            "success": True,
            "current": self.round(current),
            "previous": self.round(previous),
            "difference": self.round(current - previous),
            "growth_rate": self.round(rate),
            "formatted": f"{'+' if rate >= 0 else ''}{self.round(rate)}%"
        }

    def predict_savings(
        self,
        monthly_save: float,
        months: int = 12,
        annual_rate: float = 0
    ) -> Dict[str, Any]:
        """储蓄预测

        Args:
            monthly_save: 每月储蓄金额
            months: 月数
            annual_rate: 年利率（百分比，如 2 表示 2%）

        Returns:
            预测结果
        """
        if annual_rate > 0:
            # 考虑复利
            monthly_rate = annual_rate / 100 / 12
            if monthly_rate > 0:
                total = monthly_save * ((1 + monthly_rate) ** months - 1) / monthly_rate
            else:
                total = monthly_save * months
        else:
            total = monthly_save * months

        return {
            "success": True,
            "monthly_save": self.round(monthly_save),
            "months": months,
            "annual_rate": annual_rate,
            "total": self.round(total),
            "formatted": f"每月存 {self.round(monthly_save)} 元，{months} 个月后可存 {self.round(total)} 元"
        }

    def category_breakdown(
        self,
        db: Session,
        month: Optional[str] = None,
        transaction_type: str = "expense"
    ) -> Dict[str, Any]:
        """分类明细

        Args:
            db: 数据库会话
            month: 月份
            transaction_type: 交易类型

        Returns:
            分类明细结果
        """
        if not month:
            now = datetime.now()
            month = f"{now.year}-{now.month:02d}"

        try:
            year, mon = map(int, month.split("-"))
        except ValueError:
            return {"success": False, "error": "月份格式错误"}

        # 查询分类统计
        results = db.query(
            Transaction.category_name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mon,
            Transaction.type == transaction_type
        ).group_by(Transaction.category_name).all()

        # 计算总金额
        grand_total = sum(r.total for r in results)

        # 构建分类明细
        categories = []
        for r in results:
            ratio = (r.total / grand_total * 100) if grand_total > 0 else 0
            categories.append({
                "category": r.category_name,
                "total": self.round(r.total),
                "count": r.count,
                "ratio": self.round(ratio),
                "average": self.round(r.total / r.count) if r.count > 0 else 0
            })

        # 按金额降序排序
        categories.sort(key=lambda x: x["total"], reverse=True)

        return {
            "success": True,
            "month": month,
            "type": transaction_type,
            "grand_total": self.round(grand_total),
            "categories": categories
        }


# 创建全局实例
calculator = CalculatorService()
