"""
회계 시스템 API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from database.db_wrapper import get_db
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from decimal import Decimal

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
        db = get_db()
        conn = db.get_connection()

        # 기간 계산
        today = datetime.now()
        if period == "this_month":
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif period == "last_month":
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1).strftime('%Y-%m-%d')
            end_date = last_month.strftime('%Y-%m-%d')
        elif period == "this_year":
            start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        else:
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

        # 1. 총 매출 (주문 데이터에서)
        revenue_cursor = conn.execute("""
            SELECT
                SUM(oi.selling_price * oi.quantity) as total_revenue,
                COUNT(DISTINCT o.id) as order_count
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        revenue_data = revenue_cursor.fetchone()
        total_revenue = float(revenue_data['total_revenue'] or 0)
        order_count = revenue_data['order_count'] or 0

        # 2. 총 매입 (소싱가)
        cost_cursor = conn.execute("""
            SELECT SUM(oi.sourcing_price * oi.quantity) as total_cost
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        cost_data = cost_cursor.fetchone()
        total_cost = float(cost_data['total_cost'] or 0)

        # 3. 총 지출 (expenses 테이블)
        expense_cursor = conn.execute("""
            SELECT SUM(amount) as total_expenses
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (start_date, end_date))
        expense_data = expense_cursor.fetchone()
        total_expenses = float(expense_data['total_expenses'] or 0)

        # 4. 순이익 계산
        gross_profit = total_revenue - total_cost
        net_profit = gross_profit - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        # 5. 월별 매출 추이 (최근 6개월)
        monthly_revenue = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30 * i)
            month_start = month_date.replace(day=1).strftime('%Y-%m-%d')

            # 다음 달 1일
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1).strftime('%Y-%m-%d')
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1).strftime('%Y-%m-%d')

            cursor = conn.execute("""
                SELECT SUM(oi.selling_price * oi.quantity) as revenue
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
            """, (month_start, month_end))

            row = cursor.fetchone()
            monthly_revenue.append({
                "month": month_date.strftime('%Y-%m'),
                "revenue": float(row['revenue'] or 0)
            })

        # 6. 마켓별 매출
        market_cursor = conn.execute("""
            SELECT
                o.market,
                SUM(oi.selling_price * oi.quantity) as revenue,
                COUNT(DISTINCT o.id) as orders
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY o.market
        """, (start_date, end_date))
        market_revenue = [dict(row) for row in market_cursor.fetchall()]

        # 7. 지출 카테고리별
        expense_category_cursor = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            GROUP BY category
        """, (start_date, end_date))
        expense_by_category = [dict(row) for row in expense_category_cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "period": {
                "start": start_date,
                "end": end_date
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
        db = get_db()
        conn = db.get_connection()

        # 1. 매출
        revenue_cursor = conn.execute("""
            SELECT
                SUM(oi.selling_price * oi.quantity) as total_sales,
                COUNT(DISTINCT o.id) as order_count
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        revenue_data = revenue_cursor.fetchone()
        total_sales = float(revenue_data['total_sales'] or 0)

        # 2. 매출원가
        cost_cursor = conn.execute("""
            SELECT SUM(oi.sourcing_price * oi.quantity) as total_cost
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        cost_data = cost_cursor.fetchone()
        total_cost = float(cost_data['total_cost'] or 0)

        # 3. 판매관리비 (지출)
        expense_cursor = conn.execute("""
            SELECT
                category,
                SUM(amount) as total
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            GROUP BY category
        """, (start_date, end_date))
        expenses = [dict(row) for row in expense_cursor.fetchall()]
        total_expenses = sum([e['total'] for e in expenses])

        # 4. 계산
        gross_profit = total_sales - total_cost
        gross_margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
        operating_profit = gross_profit - total_expenses
        operating_margin = (operating_profit / total_sales * 100) if total_sales > 0 else 0
        net_profit = operating_profit
        net_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

        conn.close()

        return {
            "success": True,
            "period": {
                "start": start_date,
                "end": end_date
            },
            "statement": {
                "revenue": {
                    "total_sales": total_sales,
                    "order_count": revenue_data['order_count']
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
        db = get_db()
        conn = db.get_connection()

        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if start_date:
            query += " AND expense_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND expense_date <= ?"
            params.append(end_date)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY expense_date DESC"

        cursor = conn.execute(query, params)
        expenses = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "expenses": expenses,
            "total": len(expenses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expenses")
async def create_expense(expense: ExpenseCreate):
    """지출 추가"""
    try:
        db = get_db()
        conn = db.get_connection()

        conn.execute("""
            INSERT INTO expenses (
                expense_date, category, subcategory, amount, description,
                payment_method, receipt_url, is_vat_deductible
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expense.expense_date, expense.category, expense.subcategory,
            expense.amount, expense.description, expense.payment_method,
            expense.receipt_url, expense.is_vat_deductible
        ))

        conn.commit()
        expense_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        return {
            "success": True,
            "message": "지출이 등록되었습니다",
            "expense_id": expense_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: ExpenseUpdate):
    """지출 수정"""
    try:
        db = get_db()
        conn = db.get_connection()

        updates = []
        params = []

        if expense.expense_date:
            updates.append("expense_date = ?")
            params.append(expense.expense_date)
        if expense.category:
            updates.append("category = ?")
            params.append(expense.category)
        if expense.subcategory is not None:
            updates.append("subcategory = ?")
            params.append(expense.subcategory)
        if expense.amount:
            updates.append("amount = ?")
            params.append(expense.amount)
        if expense.description is not None:
            updates.append("description = ?")
            params.append(expense.description)
        if expense.payment_method:
            updates.append("payment_method = ?")
            params.append(expense.payment_method)
        if expense.receipt_url is not None:
            updates.append("receipt_url = ?")
            params.append(expense.receipt_url)
        if expense.is_vat_deductible is not None:
            updates.append("is_vat_deductible = ?")
            params.append(expense.is_vat_deductible)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(expense_id)

        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "지출이 수정되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    """지출 삭제"""
    try:
        db = get_db()
        conn = db.get_connection()

        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "지출이 삭제되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. 정산 관리 CRUD
# ==========================================

@router.get("/settlements")
async def get_settlements(market: Optional[str] = None):
    """정산 목록 조회"""
    try:
        db = get_db()
        conn = db.get_connection()

        if market:
            cursor = conn.execute(
                "SELECT * FROM settlements WHERE market = ? ORDER BY settlement_date DESC",
                (market,)
            )
        else:
            cursor = conn.execute("SELECT * FROM settlements ORDER BY settlement_date DESC")

        settlements = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "settlements": settlements,
            "total": len(settlements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settlements")
async def create_settlement(settlement: SettlementCreate):
    """정산 추가"""
    try:
        db = get_db()
        conn = db.get_connection()

        conn.execute("""
            INSERT INTO settlements (
                market, settlement_date, period_start, period_end,
                total_sales, commission, shipping_fee, promotion_cost,
                net_amount, settlement_status, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            settlement.market, settlement.settlement_date,
            settlement.period_start, settlement.period_end,
            settlement.total_sales, settlement.commission,
            settlement.shipping_fee, settlement.promotion_cost,
            settlement.net_amount, settlement.settlement_status,
            settlement.memo
        ))

        conn.commit()
        settlement_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        return {
            "success": True,
            "message": "정산 내역이 등록되었습니다",
            "settlement_id": settlement_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settlements/{settlement_id}")
async def update_settlement(settlement_id: int, settlement: SettlementUpdate):
    """정산 수정"""
    try:
        db = get_db()
        conn = db.get_connection()

        updates = []
        params = []

        if settlement.settlement_status:
            updates.append("settlement_status = ?")
            params.append(settlement.settlement_status)
        if settlement.memo is not None:
            updates.append("memo = ?")
            params.append(settlement.memo)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(settlement_id)

        query = f"UPDATE settlements SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "정산 내역이 수정되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settlements/{settlement_id}")
async def delete_settlement(settlement_id: int):
    """정산 삭제"""
    try:
        db = get_db()
        conn = db.get_connection()

        conn.execute("DELETE FROM settlements WHERE id = ?", (settlement_id,))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "정산 내역이 삭제되었습니다"
        }
    except Exception as e:
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
        db = get_db()
        conn = db.get_connection()

        # 분기 기간 계산
        quarter_months = {
            1: ('01', '03'),
            2: ('04', '06'),
            3: ('07', '09'),
            4: ('10', '12')
        }

        start_month, end_month = quarter_months[quarter]
        start_date = f"{year}-{start_month}-01"
        end_date = f"{year}-{end_month}-31"

        # 과세 매출
        sales_cursor = conn.execute("""
            SELECT SUM(oi.selling_price * oi.quantity) as taxable_sales
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        taxable_sales = float(sales_cursor.fetchone()['taxable_sales'] or 0)

        # 과세 매입
        purchases_cursor = conn.execute("""
            SELECT SUM(oi.sourcing_price * oi.quantity) as taxable_purchases
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        taxable_purchases = float(purchases_cursor.fetchone()['taxable_purchases'] or 0)

        # 부가세 공제 가능 지출
        deductible_cursor = conn.execute("""
            SELECT SUM(amount) as deductible_expenses
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            AND is_vat_deductible = 1
        """, (start_date, end_date))
        deductible_expenses = float(deductible_cursor.fetchone()['deductible_expenses'] or 0)

        # 부가세 계산 (10%)
        vat_on_sales = taxable_sales * 0.1
        vat_on_purchases = (taxable_purchases + deductible_expenses) * 0.1
        vat_payable = vat_on_sales - vat_on_purchases

        conn.close()

        return {
            "success": True,
            "year": year,
            "quarter": quarter,
            "period": {
                "start": start_date,
                "end": end_date
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tax/income")
async def get_income_tax_estimate(year: int):
    """
    종합소득세 예상 계산 (연간)
    """
    try:
        db = get_db()
        conn = db.get_connection()

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # 총 매출
        sales_cursor = conn.execute("""
            SELECT SUM(oi.selling_price * oi.quantity) as total_sales
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        total_sales = float(sales_cursor.fetchone()['total_sales'] or 0)

        # 총 매입
        purchases_cursor = conn.execute("""
            SELECT SUM(oi.sourcing_price * oi.quantity) as total_purchases
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        total_purchases = float(purchases_cursor.fetchone()['total_purchases'] or 0)

        # 필요경비 (지출)
        expenses_cursor = conn.execute("""
            SELECT SUM(amount) as total_expenses
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (start_date, end_date))
        total_expenses = float(expenses_cursor.fetchone()['total_expenses'] or 0)

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

        conn.close()

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
        db = get_db()
        conn = db.get_connection()

        # 기간 계산
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        # 1. 매출 분석
        revenue_cursor = conn.execute("""
            SELECT
                COUNT(DISTINCT o.id) as order_count,
                SUM(oi.selling_price * oi.quantity) as total_revenue,
                AVG(oi.selling_price * oi.quantity) as avg_order_value
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
        """, (start_date, end_date))
        revenue_data = dict(revenue_cursor.fetchone())

        # 2. 일별 매출 (최고 매출일 찾기)
        daily_cursor = conn.execute("""
            SELECT
                DATE(o.created_at) as date,
                SUM(oi.selling_price * oi.quantity) as daily_revenue
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
            GROUP BY DATE(o.created_at)
            ORDER BY daily_revenue DESC
            LIMIT 1
        """, (start_date, end_date))
        best_day = daily_cursor.fetchone()

        # 3. 베스트셀러 TOP 5
        bestseller_cursor = conn.execute("""
            SELECT
                oi.product_name,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.selling_price * oi.quantity) as total_revenue
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
            GROUP BY oi.product_name
            ORDER BY total_revenue DESC
            LIMIT 5
        """, (start_date, end_date))
        bestsellers = [dict(row) for row in bestseller_cursor.fetchall()]

        # 4. 마켓별 분석
        market_cursor = conn.execute("""
            SELECT
                o.market,
                COUNT(DISTINCT o.id) as orders,
                SUM(oi.selling_price * oi.quantity) as revenue
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
            GROUP BY o.market
        """, (start_date, end_date))
        market_analysis = [dict(row) for row in market_cursor.fetchall()]

        # 5. 손익 요약
        cost_cursor = conn.execute("""
            SELECT SUM(oi.sourcing_price * oi.quantity) as total_cost
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) < ?
        """, (start_date, end_date))
        total_cost = float(cost_cursor.fetchone()['total_cost'] or 0)

        expense_cursor = conn.execute("""
            SELECT SUM(amount) as total_expenses
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
        """, (start_date, end_date))
        total_expenses = float(expense_cursor.fetchone()['total_expenses'] or 0)

        total_revenue = float(revenue_data['total_revenue'] or 0)
        net_profit = total_revenue - total_cost - total_expenses
        roi = (net_profit / total_cost * 100) if total_cost > 0 else 0

        conn.close()

        return {
            "success": True,
            "period": {
                "year": year,
                "month": month
            },
            "summary": {
                "order_count": revenue_data['order_count'],
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "roi": round(roi, 2),
                "avg_order_value": float(revenue_data['avg_order_value'] or 0)
            },
            "best_day": dict(best_day) if best_day else None,
            "bestsellers": bestsellers,
            "market_analysis": market_analysis
        }
    except Exception as e:
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
