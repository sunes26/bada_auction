"""
회계 시스템 API - SQLAlchemy ORM 기반
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, cast, Date
from sqlalchemy.orm import Session

from database.database_manager import get_database_manager
from database.models import (
    Order, OrderItem, Expense, Settlement, MarketOrderRaw
)

router = APIRouter(prefix="/api/accounting", tags=["accounting"])

# ==========================================
# Pydantic Models
# ==========================================

class ExpenseCreate(BaseModel):
    expense_date: str
    category: str
    subcategory: Optional[str] = None
    amount: float
    description: Optional[str] = None
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None
    is_vat_deductible: bool = False

class ExpenseUpdate(BaseModel):
    expense_date: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None
    is_vat_deductible: Optional[bool] = None

class SettlementCreate(BaseModel):
    market: str
    settlement_date: str
    period_start: str
    period_end: str
    total_sales: float
    commission: float
    shipping_fee: float
    promotion_cost: float
    net_amount: float
    settlement_status: str = 'pending'
    memo: Optional[str] = None

class SettlementUpdate(BaseModel):
    settlement_status: Optional[str] = None
    memo: Optional[str] = None


def get_session():
    """SQLAlchemy 세션 가져오기"""
    db_manager = get_database_manager()
    return db_manager.get_session()


def model_to_dict(obj) -> Dict:
    """SQLAlchemy 모델을 딕셔너리로 변환"""
    if obj is None:
        return {}
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        elif isinstance(value, date):
            result[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        else:
            result[column.name] = value
    return result


# ==========================================
# 1. 대시보드 - 회계 요약 통계
# ==========================================

@router.get("/dashboard/stats")
async def get_accounting_dashboard_stats(period: str = "this_month"):
    """
    회계 대시보드 통계
    period: this_month, last_month, this_quarter, this_year, custom
    """
    try:
        # 기간 계산
        today = datetime.now()
        if period == "this_month":
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif period == "last_month":
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_month.replace(hour=23, minute=59, second=59)
        elif period == "this_year":
            start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        else:
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today

        with get_session() as session:
            # 1. 총 매출 (주문 데이터에서) - OrderItem이 있는 경우
            try:
                revenue_result = session.query(
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('total_revenue'),
                    func.count(func.distinct(Order.id)).label('order_count')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                total_revenue = float(revenue_result.total_revenue or 0) if revenue_result else 0
                order_count = revenue_result.order_count or 0 if revenue_result else 0
            except Exception:
                # OrderItem 테이블이 없거나 데이터가 없는 경우
                total_revenue = 0
                order_count = 0

            # 2. 총 매입 (소싱가)
            try:
                cost_result = session.query(
                    func.sum(OrderItem.sourcing_price * OrderItem.quantity).label('total_cost')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                total_cost = float(cost_result.total_cost or 0) if cost_result else 0
            except Exception:
                total_cost = 0

            # 3. 총 지출 (expenses 테이블)
            try:
                expense_result = session.query(
                    func.sum(Expense.amount).label('total_expenses')
                ).filter(
                    Expense.expense_date >= start_date.date(),
                    Expense.expense_date <= end_date.date()
                ).first()

                total_expenses = float(expense_result.total_expenses or 0) if expense_result else 0
            except Exception:
                total_expenses = 0

            # 4. 순이익 계산
            gross_profit = total_revenue - total_cost
            net_profit = gross_profit - total_expenses
            profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

            # 5. 월별 매출 추이 (최근 6개월)
            monthly_revenue = []
            for i in range(5, -1, -1):
                month_date = today - timedelta(days=30 * i)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                # 다음 달 1일
                if month_date.month == 12:
                    month_end = month_date.replace(year=month_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    month_end = month_date.replace(month=month_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

                try:
                    result = session.query(
                        func.sum(OrderItem.selling_price * OrderItem.quantity).label('revenue')
                    ).join(Order).filter(
                        Order.created_at >= month_start,
                        Order.created_at < month_end
                    ).first()

                    revenue = float(result.revenue or 0) if result else 0
                except Exception:
                    revenue = 0

                monthly_revenue.append({
                    "month": month_date.strftime('%Y-%m'),
                    "revenue": revenue
                })

            # 6. 마켓별 매출
            market_revenue = []
            try:
                market_results = session.query(
                    Order.market,
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('revenue'),
                    func.count(func.distinct(Order.id)).label('orders')
                ).join(OrderItem).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).group_by(Order.market).all()

                for row in market_results:
                    market_revenue.append({
                        "market": row.market,
                        "revenue": float(row.revenue or 0),
                        "orders": row.orders or 0
                    })
            except Exception:
                pass

            # 7. 지출 카테고리별
            expense_by_category = []
            try:
                expense_results = session.query(
                    Expense.category,
                    func.sum(Expense.amount).label('total')
                ).filter(
                    Expense.expense_date >= start_date.date(),
                    Expense.expense_date <= end_date.date()
                ).group_by(Expense.category).all()

                for row in expense_results:
                    expense_by_category.append({
                        "category": row.category,
                        "total": float(row.total or 0)
                    })
            except Exception:
                pass

            return {
                "success": True,
                "period": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "summary": {
                    "total_revenue": total_revenue,
                    "total_cost": total_cost,
                    "total_expenses": total_expenses,
                    "gross_profit": gross_profit,
                    "net_profit": net_profit,
                    "profit_margin": round(profit_margin, 2),
                    "order_count": order_count
                },
                "monthly_revenue": monthly_revenue,
                "market_revenue": market_revenue,
                "expense_by_category": expense_by_category
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 2. 손익계산서
# ==========================================

@router.get("/profit-loss")
async def get_profit_loss_statement(start_date: str, end_date: str):
    """
    손익계산서 조회
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

        with get_session() as session:
            # 1. 매출
            try:
                revenue_result = session.query(
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('total_sales'),
                    func.count(func.distinct(Order.id)).label('order_count')
                ).join(Order).filter(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                ).first()

                total_sales = float(revenue_result.total_sales or 0) if revenue_result else 0
                order_count = revenue_result.order_count or 0 if revenue_result else 0
            except Exception:
                total_sales = 0
                order_count = 0

            # 2. 매출원가
            try:
                cost_result = session.query(
                    func.sum(OrderItem.sourcing_price * OrderItem.quantity).label('total_cost')
                ).join(Order).filter(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                ).first()

                total_cost = float(cost_result.total_cost or 0) if cost_result else 0
            except Exception:
                total_cost = 0

            # 3. 판매관리비 (지출)
            expenses = []
            try:
                expense_results = session.query(
                    Expense.category,
                    func.sum(Expense.amount).label('total')
                ).filter(
                    Expense.expense_date >= start_dt.date(),
                    Expense.expense_date <= end_dt.date()
                ).group_by(Expense.category).all()

                for row in expense_results:
                    expenses.append({
                        "category": row.category,
                        "total": float(row.total or 0)
                    })
            except Exception:
                pass

            total_expenses = sum([e['total'] for e in expenses])

            # 4. 계산
            gross_profit = total_sales - total_cost
            gross_margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
            operating_profit = gross_profit - total_expenses
            operating_margin = (operating_profit / total_sales * 100) if total_sales > 0 else 0
            net_profit = operating_profit
            net_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

            return {
                "success": True,
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "statement": {
                    "revenue": {
                        "total_sales": total_sales,
                        "order_count": order_count
                    },
                    "cost_of_sales": {
                        "total_cost": total_cost
                    },
                    "gross_profit": {
                        "amount": gross_profit,
                        "margin": round(gross_margin, 2)
                    },
                    "operating_expenses": {
                        "breakdown": expenses,
                        "total": total_expenses
                    },
                    "operating_profit": {
                        "amount": operating_profit,
                        "margin": round(operating_margin, 2)
                    },
                    "net_profit": {
                        "amount": net_profit,
                        "margin": round(net_margin, 2)
                    }
                }
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. 지출 관리 CRUD
# ==========================================

@router.get("/expenses")
async def get_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
):
    """지출 목록 조회"""
    try:
        with get_session() as session:
            query = session.query(Expense)

            if start_date:
                query = query.filter(Expense.expense_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Expense.expense_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
            if category:
                query = query.filter(Expense.category == category)

            query = query.order_by(Expense.expense_date.desc())
            expenses = query.all()

            return {
                "success": True,
                "expenses": [model_to_dict(e) for e in expenses],
                "total": len(expenses)
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expenses")
async def create_expense(expense: ExpenseCreate):
    """지출 추가"""
    try:
        with get_session() as session:
            new_expense = Expense(
                expense_date=datetime.strptime(expense.expense_date, '%Y-%m-%d').date(),
                category=expense.category,
                subcategory=expense.subcategory,
                amount=expense.amount,
                description=expense.description,
                payment_method=expense.payment_method,
                receipt_url=expense.receipt_url,
                is_vat_deductible=expense.is_vat_deductible
            )
            session.add(new_expense)
            session.flush()
            expense_id = new_expense.id

            return {
                "success": True,
                "message": "지출이 등록되었습니다",
                "expense_id": expense_id
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: ExpenseUpdate):
    """지출 수정"""
    try:
        with get_session() as session:
            existing = session.query(Expense).filter_by(id=expense_id).first()
            if not existing:
                raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다")

            if expense.expense_date:
                existing.expense_date = datetime.strptime(expense.expense_date, '%Y-%m-%d').date()
            if expense.category:
                existing.category = expense.category
            if expense.subcategory is not None:
                existing.subcategory = expense.subcategory
            if expense.amount:
                existing.amount = expense.amount
            if expense.description is not None:
                existing.description = expense.description
            if expense.payment_method:
                existing.payment_method = expense.payment_method
            if expense.receipt_url is not None:
                existing.receipt_url = expense.receipt_url
            if expense.is_vat_deductible is not None:
                existing.is_vat_deductible = expense.is_vat_deductible

            return {
                "success": True,
                "message": "지출이 수정되었습니다"
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    """지출 삭제"""
    try:
        with get_session() as session:
            existing = session.query(Expense).filter_by(id=expense_id).first()
            if not existing:
                raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다")

            session.delete(existing)

            return {
                "success": True,
                "message": "지출이 삭제되었습니다"
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. 정산 관리 CRUD
# ==========================================

@router.get("/settlements")
async def get_settlements(market: Optional[str] = None):
    """정산 목록 조회"""
    try:
        with get_session() as session:
            query = session.query(Settlement)

            if market:
                query = query.filter(Settlement.market == market)

            query = query.order_by(Settlement.settlement_date.desc())
            settlements = query.all()

            return {
                "success": True,
                "settlements": [model_to_dict(s) for s in settlements],
                "total": len(settlements)
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settlements")
async def create_settlement(settlement: SettlementCreate):
    """정산 추가"""
    try:
        with get_session() as session:
            new_settlement = Settlement(
                market=settlement.market,
                settlement_date=datetime.strptime(settlement.settlement_date, '%Y-%m-%d').date(),
                period_start=datetime.strptime(settlement.period_start, '%Y-%m-%d').date(),
                period_end=datetime.strptime(settlement.period_end, '%Y-%m-%d').date(),
                total_sales=settlement.total_sales,
                commission=settlement.commission,
                shipping_fee=settlement.shipping_fee,
                promotion_cost=settlement.promotion_cost,
                net_amount=settlement.net_amount,
                settlement_status=settlement.settlement_status,
                memo=settlement.memo
            )
            session.add(new_settlement)
            session.flush()
            settlement_id = new_settlement.id

            return {
                "success": True,
                "message": "정산 내역이 등록되었습니다",
                "settlement_id": settlement_id
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settlements/{settlement_id}")
async def update_settlement(settlement_id: int, settlement: SettlementUpdate):
    """정산 수정"""
    try:
        with get_session() as session:
            existing = session.query(Settlement).filter_by(id=settlement_id).first()
            if not existing:
                raise HTTPException(status_code=404, detail="정산 내역을 찾을 수 없습니다")

            if settlement.settlement_status:
                existing.settlement_status = settlement.settlement_status
            if settlement.memo is not None:
                existing.memo = settlement.memo

            return {
                "success": True,
                "message": "정산 내역이 수정되었습니다"
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settlements/{settlement_id}")
async def delete_settlement(settlement_id: int):
    """정산 삭제"""
    try:
        with get_session() as session:
            existing = session.query(Settlement).filter_by(id=settlement_id).first()
            if not existing:
                raise HTTPException(status_code=404, detail="정산 내역을 찾을 수 없습니다")

            session.delete(existing)

            return {
                "success": True,
                "message": "정산 내역이 삭제되었습니다"
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 5. 세금 계산
# ==========================================

@router.get("/tax/vat")
async def get_vat_calculation(year: int, quarter: int):
    """
    부가세 계산 (분기별)
    quarter: 1~4
    """
    try:
        # 분기 기간 계산
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }

        start_month, end_month = quarter_months[quarter]
        start_date = datetime(year, start_month, 1)

        # 분기 마지막 날
        if end_month == 12:
            end_date = datetime(year, 12, 31, 23, 59, 59)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(seconds=1)

        with get_session() as session:
            # 과세 매출
            try:
                sales_result = session.query(
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('taxable_sales')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                taxable_sales = float(sales_result.taxable_sales or 0) if sales_result else 0
            except Exception:
                taxable_sales = 0

            # 과세 매입
            try:
                purchases_result = session.query(
                    func.sum(OrderItem.sourcing_price * OrderItem.quantity).label('taxable_purchases')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                taxable_purchases = float(purchases_result.taxable_purchases or 0) if purchases_result else 0
            except Exception:
                taxable_purchases = 0

            # 부가세 공제 가능 지출
            try:
                deductible_result = session.query(
                    func.sum(Expense.amount).label('deductible_expenses')
                ).filter(
                    Expense.expense_date >= start_date.date(),
                    Expense.expense_date <= end_date.date(),
                    Expense.is_vat_deductible == True
                ).first()

                deductible_expenses = float(deductible_result.deductible_expenses or 0) if deductible_result else 0
            except Exception:
                deductible_expenses = 0

            # 부가세 계산 (10%)
            vat_on_sales = taxable_sales * 0.1
            vat_on_purchases = (taxable_purchases + deductible_expenses) * 0.1
            vat_payable = vat_on_sales - vat_on_purchases

            return {
                "success": True,
                "year": year,
                "quarter": quarter,
                "period": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "calculation": {
                    "taxable_sales": taxable_sales,
                    "vat_on_sales": round(vat_on_sales, 2),
                    "taxable_purchases": taxable_purchases,
                    "deductible_expenses": deductible_expenses,
                    "vat_on_purchases": round(vat_on_purchases, 2),
                    "vat_payable": round(vat_payable, 2)
                }
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tax/income")
async def get_income_tax_estimate(year: int):
    """
    종합소득세 예상 계산 (연간)
    """
    try:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        with get_session() as session:
            # 총 매출
            try:
                sales_result = session.query(
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('total_sales')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                total_sales = float(sales_result.total_sales or 0) if sales_result else 0
            except Exception:
                total_sales = 0

            # 총 매입
            try:
                purchases_result = session.query(
                    func.sum(OrderItem.sourcing_price * OrderItem.quantity).label('total_purchases')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).first()

                total_purchases = float(purchases_result.total_purchases or 0) if purchases_result else 0
            except Exception:
                total_purchases = 0

            # 필요경비 (지출)
            try:
                expenses_result = session.query(
                    func.sum(Expense.amount).label('total_expenses')
                ).filter(
                    Expense.expense_date >= start_date.date(),
                    Expense.expense_date <= end_date.date()
                ).first()

                total_expenses = float(expenses_result.total_expenses or 0) if expenses_result else 0
            except Exception:
                total_expenses = 0

            # 과세표준
            taxable_income = total_sales - total_purchases - total_expenses

            # 간이세액표 (2024년 기준)
            if taxable_income <= 0:
                income_tax = 0
                tax_rate = 0
            elif taxable_income <= 14000000:
                income_tax = taxable_income * 0.06
                tax_rate = 6
            elif taxable_income <= 50000000:
                income_tax = 840000 + (taxable_income - 14000000) * 0.15
                tax_rate = 15
            elif taxable_income <= 88000000:
                income_tax = 6240000 + (taxable_income - 50000000) * 0.24
                tax_rate = 24
            elif taxable_income <= 150000000:
                income_tax = 15360000 + (taxable_income - 88000000) * 0.35
                tax_rate = 35
            elif taxable_income <= 300000000:
                income_tax = 37060000 + (taxable_income - 150000000) * 0.38
                tax_rate = 38
            elif taxable_income <= 500000000:
                income_tax = 94060000 + (taxable_income - 300000000) * 0.40
                tax_rate = 40
            else:
                income_tax = 174060000 + (taxable_income - 500000000) * 0.45
                tax_rate = 45

            # 지방소득세 (소득세의 10%)
            local_tax = income_tax * 0.1
            total_tax = income_tax + local_tax

            return {
                "success": True,
                "year": year,
                "calculation": {
                    "total_sales": total_sales,
                    "total_purchases": total_purchases,
                    "total_expenses": total_expenses,
                    "taxable_income": taxable_income,
                    "income_tax": round(income_tax, 2),
                    "local_tax": round(local_tax, 2),
                    "total_tax": round(total_tax, 2),
                    "effective_tax_rate": tax_rate
                }
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 6. 월별 리포트
# ==========================================

@router.get("/report/monthly")
async def get_monthly_report(year: int, month: int):
    """
    월별 회계 리포트
    """
    try:
        # 기간 계산
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

        with get_session() as session:
            # 1. 매출 분석
            try:
                revenue_result = session.query(
                    func.count(func.distinct(Order.id)).label('order_count'),
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('total_revenue'),
                    func.avg(OrderItem.selling_price * OrderItem.quantity).label('avg_order_value')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at < end_date
                ).first()

                order_count = revenue_result.order_count or 0 if revenue_result else 0
                total_revenue = float(revenue_result.total_revenue or 0) if revenue_result else 0
                avg_order_value = float(revenue_result.avg_order_value or 0) if revenue_result else 0
            except Exception:
                order_count = 0
                total_revenue = 0
                avg_order_value = 0

            # 2. 베스트셀러 TOP 5
            bestsellers = []
            try:
                bestseller_results = session.query(
                    OrderItem.product_name,
                    func.sum(OrderItem.quantity).label('total_quantity'),
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('total_revenue')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at < end_date
                ).group_by(OrderItem.product_name).order_by(
                    func.sum(OrderItem.selling_price * OrderItem.quantity).desc()
                ).limit(5).all()

                for row in bestseller_results:
                    bestsellers.append({
                        "product_name": row.product_name,
                        "total_quantity": int(row.total_quantity or 0),
                        "total_revenue": float(row.total_revenue or 0)
                    })
            except Exception:
                pass

            # 3. 마켓별 분석
            market_analysis = []
            try:
                market_results = session.query(
                    Order.market,
                    func.count(func.distinct(Order.id)).label('orders'),
                    func.sum(OrderItem.selling_price * OrderItem.quantity).label('revenue')
                ).join(OrderItem).filter(
                    Order.created_at >= start_date,
                    Order.created_at < end_date
                ).group_by(Order.market).all()

                for row in market_results:
                    market_analysis.append({
                        "market": row.market,
                        "orders": row.orders or 0,
                        "revenue": float(row.revenue or 0)
                    })
            except Exception:
                pass

            # 4. 손익 요약
            try:
                cost_result = session.query(
                    func.sum(OrderItem.sourcing_price * OrderItem.quantity).label('total_cost')
                ).join(Order).filter(
                    Order.created_at >= start_date,
                    Order.created_at < end_date
                ).first()

                total_cost = float(cost_result.total_cost or 0) if cost_result else 0
            except Exception:
                total_cost = 0

            try:
                expense_result = session.query(
                    func.sum(Expense.amount).label('total_expenses')
                ).filter(
                    Expense.expense_date >= start_date.date(),
                    Expense.expense_date < end_date.date()
                ).first()

                total_expenses = float(expense_result.total_expenses or 0) if expense_result else 0
            except Exception:
                total_expenses = 0

            net_profit = total_revenue - total_cost - total_expenses
            roi = (net_profit / total_cost * 100) if total_cost > 0 else 0

            return {
                "success": True,
                "period": {
                    "year": year,
                    "month": month
                },
                "summary": {
                    "order_count": order_count,
                    "total_revenue": total_revenue,
                    "total_cost": total_cost,
                    "total_expenses": total_expenses,
                    "net_profit": net_profit,
                    "roi": round(roi, 2),
                    "avg_order_value": avg_order_value
                },
                "bestsellers": bestsellers,
                "market_analysis": market_analysis
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 7. 카테고리 목록
# ==========================================

@router.get("/expense-categories")
async def get_expense_categories():
    """지출 카테고리 목록"""
    return {
        "success": True,
        "categories": [
            "광고비",
            "배송비",
            "포장재",
            "수수료",
            "기타"
        ]
    }
