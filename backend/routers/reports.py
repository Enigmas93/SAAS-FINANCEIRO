from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, extract, case
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from database import get_db
from models import (
    Transaction, Account, User, TransactionCategory,
    FinancialGoal, Debt, Alert, AlertType, TransactionType
)
from schemas_advanced import (
    MonthlyReport, CategoryReport, AccountReport,
    CashFlowReport, AlertCreate
)
from auth import get_current_active_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/dashboard")
def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dashboard principal com resumo financeiro"""
    
    # Período atual (último mês)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Transações do período
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    ).all()
    
    # Cálculos básicos
    total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
    net_balance = total_income - total_expense
    
    # Saldo atual das contas
    accounts = db.query(Account).filter(
        Account.company_id == current_user.company_id
    ).all()
    total_balance = sum(acc.balance for acc in accounts)
    
    # Metas ativas
    active_goals = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.company_id == current_user.company_id,
            FinancialGoal.status == "ACTIVE"
        )
    ).all()
    
    goals_progress = []
    for goal in active_goals:
        progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
        goals_progress.append({
            "id": goal.id,
            "name": goal.name,
            "progress": min(float(progress), 100.0),
            "current_amount": float(goal.current_amount),
            "target_amount": float(goal.target_amount)
        })
    
    # Dívidas pendentes
    pending_debts = db.query(Debt).filter(
        and_(
            Debt.company_id == current_user.company_id,
            Debt.status.in_(["ACTIVE", "OVERDUE"])
        )
    ).all()
    
    total_debt = sum(debt.remaining_amount for debt in pending_debts)
    
    # Alertas não lidos
    unread_alerts = db.query(Alert).filter(
        and_(
            Alert.company_id == current_user.company_id,
            Alert.is_read == False
        )
    ).count()
    
    return {
        "period": {
            "start_date": start_date.date(),
            "end_date": end_date.date()
        },
        "financial_summary": {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_balance": float(net_balance),
            "total_balance": float(total_balance),
            "total_debt": float(total_debt)
        },
        "goals_summary": {
            "active_goals_count": len(active_goals),
            "goals_progress": goals_progress
        },
        "alerts_count": unread_alerts,
        "accounts_count": len(accounts),
        "transactions_count": len(transactions)
    }

@router.get("/monthly/{year}/{month}")
def get_monthly_report(
    year: int,
    month: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Relatório mensal detalhado"""
    
    # Validar mês e ano
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mês deve estar entre 1 e 12"
        )
    
    # Período do mês
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Transações do mês
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    ).all()
    
    # Análise por categoria
    categories_data = defaultdict(lambda: {"income": 0, "expense": 0, "count": 0})
    
    for transaction in transactions:
        category = transaction.category or "Outros"
        amount = float(transaction.amount)
        
        if transaction.transaction_type == TransactionType.INCOME:
            categories_data[category]["income"] += amount
        else:
            categories_data[category]["expense"] += amount
        
        categories_data[category]["count"] += 1
    
    # Análise por dia
    daily_data = defaultdict(lambda: {"income": 0, "expense": 0})
    
    for transaction in transactions:
        day = transaction.date.day
        amount = float(transaction.amount)
        
        if transaction.transaction_type == TransactionType.INCOME:
            daily_data[day]["income"] += amount
        else:
            daily_data[day]["expense"] += amount
    
    # Comparação com mês anterior
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    prev_start = datetime(prev_year, prev_month, 1)
    if prev_month == 12:
        prev_end = datetime(prev_year + 1, 1, 1) - timedelta(days=1)
    else:
        prev_end = datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)
    
    prev_transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= prev_start,
            Transaction.date <= prev_end
        )
    ).all()
    
    prev_income = sum(t.amount for t in prev_transactions if t.transaction_type == TransactionType.INCOME)
    prev_expense = sum(t.amount for t in prev_transactions if t.transaction_type == TransactionType.EXPENSE)
    
    current_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    current_expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
    
    income_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    expense_change = ((current_expense - prev_expense) / prev_expense * 100) if prev_expense > 0 else 0
    
    return {
        "period": {
            "year": year,
            "month": month,
            "start_date": start_date.date(),
            "end_date": end_date.date()
        },
        "summary": {
            "total_income": float(current_income),
            "total_expense": float(current_expense),
            "net_balance": float(current_income - current_expense),
            "transactions_count": len(transactions)
        },
        "comparison": {
            "income_change_percentage": float(income_change),
            "expense_change_percentage": float(expense_change),
            "previous_month": {
                "income": float(prev_income),
                "expense": float(prev_expense)
            }
        },
        "categories": dict(categories_data),
        "daily_flow": dict(daily_data)
    }

@router.get("/categories")
def get_categories_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, description="Número máximo de categorias"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Relatório de gastos por categoria"""
    
    # Período padrão: últimos 3 meses
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # Buscar transações do período
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.transaction_type == TransactionType.EXPENSE
        )
    ).all()
    
    # Agrupar por categoria
    categories = defaultdict(lambda: {"total": 0, "count": 0, "transactions": []})
    
    for transaction in transactions:
        category = transaction.category or "Outros"
        amount = float(transaction.amount)
        
        categories[category]["total"] += amount
        categories[category]["count"] += 1
        categories[category]["transactions"].append({
            "id": transaction.id,
            "description": transaction.description,
            "amount": amount,
            "date": transaction.date
        })
    
    # Ordenar por valor total
    sorted_categories = sorted(
        categories.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )[:limit]
    
    total_expenses = sum(cat[1]["total"] for cat in sorted_categories)
    
    # Calcular percentuais
    result = []
    for category, data in sorted_categories:
        percentage = (data["total"] / total_expenses * 100) if total_expenses > 0 else 0
        result.append({
            "category": category,
            "total_amount": data["total"],
            "percentage": float(percentage),
            "transactions_count": data["count"],
            "average_amount": data["total"] / data["count"] if data["count"] > 0 else 0
        })
    
    return {
        "period": {
            "start_date": start_date.date(),
            "end_date": end_date.date()
        },
        "total_expenses": total_expenses,
        "categories": result
    }

@router.get("/cash-flow")
def get_cash_flow_report(
    days: int = Query(30, description="Número de dias para análise"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Relatório de fluxo de caixa"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Transações do período
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    ).order_by(Transaction.date).all()
    
    # Saldo inicial (saldo atual menos movimentações do período)
    current_balance = sum(
        acc.balance for acc in db.query(Account).filter(
            Account.company_id == current_user.company_id
        ).all()
    )
    
    period_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    period_expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
    initial_balance = current_balance - (period_income - period_expense)
    
    # Fluxo diário
    daily_flow = []
    running_balance = initial_balance
    
    # Agrupar transações por dia
    daily_transactions = defaultdict(list)
    for transaction in transactions:
        day = transaction.date.date()
        daily_transactions[day].append(transaction)
    
    # Gerar dados diários
    current_date = start_date.date()
    while current_date <= end_date.date():
        day_income = sum(
            t.amount for t in daily_transactions[current_date]
            if t.transaction_type == TransactionType.INCOME
        )
        day_expense = sum(
            t.amount for t in daily_transactions[current_date]
            if t.transaction_type == TransactionType.EXPENSE
        )
        
        net_flow = day_income - day_expense
        running_balance += net_flow
        
        daily_flow.append({
            "date": current_date,
            "income": float(day_income),
            "expense": float(day_expense),
            "net_flow": float(net_flow),
            "balance": float(running_balance),
            "transactions_count": len(daily_transactions[current_date])
        })
        
        current_date += timedelta(days=1)
    
    # Projeção futura (próximos 7 dias)
    future_projection = []
    avg_daily_income = period_income / days if days > 0 else 0
    avg_daily_expense = period_expense / days if days > 0 else 0
    
    projection_balance = running_balance
    for i in range(1, 8):
        future_date = end_date.date() + timedelta(days=i)
        projected_net = avg_daily_income - avg_daily_expense
        projection_balance += projected_net
        
        future_projection.append({
            "date": future_date,
            "projected_income": float(avg_daily_income),
            "projected_expense": float(avg_daily_expense),
            "projected_net_flow": float(projected_net),
            "projected_balance": float(projection_balance)
        })
    
    return {
        "period": {
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "days": days
        },
        "summary": {
            "initial_balance": float(initial_balance),
            "final_balance": float(running_balance),
            "total_income": float(period_income),
            "total_expense": float(period_expense),
            "net_flow": float(period_income - period_expense),
            "average_daily_income": float(avg_daily_income),
            "average_daily_expense": float(avg_daily_expense)
        },
        "daily_flow": daily_flow,
        "future_projection": future_projection
    }

@router.get("/insights")
def get_financial_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Insights e alertas inteligentes sobre finanças"""
    
    insights = []
    
    # Período de análise: últimos 60 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    ).all()
    
    # Insight 1: Categoria com maior gasto
    expense_by_category = defaultdict(float)
    for t in transactions:
        if t.transaction_type == TransactionType.EXPENSE:
            category = t.category or "Outros"
            expense_by_category[category] += float(t.amount)
    
    if expense_by_category:
        top_category = max(expense_by_category.items(), key=lambda x: x[1])
        total_expenses = sum(expense_by_category.values())
        percentage = (top_category[1] / total_expenses) * 100
        
        insights.append({
            "type": "spending_pattern",
            "title": f"Maior gasto: {top_category[0]}",
            "message": f"Você gastou R$ {top_category[1]:.2f} em {top_category[0]} ({percentage:.1f}% do total)",
            "severity": "info" if percentage < 40 else "warning",
            "data": {
                "category": top_category[0],
                "amount": top_category[1],
                "percentage": percentage
            }
        })
    
    # Insight 2: Comparação com mês anterior
    current_month_start = datetime(end_date.year, end_date.month, 1)
    current_month_expenses = sum(
        t.amount for t in transactions
        if t.transaction_type == TransactionType.EXPENSE and t.date >= current_month_start
    )
    
    prev_month = current_month_start - timedelta(days=1)
    prev_month_start = datetime(prev_month.year, prev_month.month, 1)
    
    prev_transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= prev_month_start,
            Transaction.date < current_month_start,
            Transaction.transaction_type == TransactionType.EXPENSE
        )
    ).all()
    
    prev_month_expenses = sum(t.amount for t in prev_transactions)
    
    if prev_month_expenses > 0:
        expense_change = ((current_month_expenses - prev_month_expenses) / prev_month_expenses) * 100
        
        if abs(expense_change) > 10:
            insights.append({
                "type": "monthly_comparison",
                "title": f"Gastos {'aumentaram' if expense_change > 0 else 'diminuíram'} {abs(expense_change):.1f}%",
                "message": f"Comparado ao mês anterior, você {'gastou' if expense_change > 0 else 'economizou'} R$ {abs(current_month_expenses - prev_month_expenses):.2f}",
                "severity": "warning" if expense_change > 20 else "info",
                "data": {
                    "current_month": float(current_month_expenses),
                    "previous_month": float(prev_month_expenses),
                    "change_percentage": expense_change
                }
            })
    
    # Insight 3: Metas em risco
    goals = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.company_id == current_user.company_id,
            FinancialGoal.status == "ACTIVE",
            FinancialGoal.target_date.isnot(None)
        )
    ).all()
    
    for goal in goals:
        days_remaining = (goal.target_date - datetime.now()).days
        progress = (goal.current_amount / goal.target_amount) * 100
        
        if days_remaining > 0 and days_remaining <= 30 and progress < 80:
            daily_needed = (goal.target_amount - goal.current_amount) / days_remaining
            
            insights.append({
                "type": "goal_risk",
                "title": f"Meta em risco: {goal.name}",
                "message": f"Faltam {days_remaining} dias e você precisa economizar R$ {daily_needed:.2f} por dia",
                "severity": "warning",
                "data": {
                    "goal_id": goal.id,
                    "days_remaining": days_remaining,
                    "daily_needed": float(daily_needed),
                    "current_progress": progress
                }
            })
    
    # Insight 4: Dívidas próximas do vencimento
    upcoming_debts = db.query(Debt).filter(
        and_(
            Debt.company_id == current_user.company_id,
            Debt.status == "ACTIVE",
            Debt.next_due_date.isnot(None),
            Debt.next_due_date <= end_date + timedelta(days=7)
        )
    ).all()
    
    if upcoming_debts:
        total_upcoming = sum(debt.installment_amount for debt in upcoming_debts)
        
        insights.append({
            "type": "upcoming_debts",
            "title": f"{len(upcoming_debts)} dívida(s) vencendo em 7 dias",
            "message": f"Total de R$ {total_upcoming:.2f} em pagamentos próximos",
            "severity": "warning",
            "data": {
                "debts_count": len(upcoming_debts),
                "total_amount": float(total_upcoming)
            }
        })
    
    return {
        "generated_at": datetime.now(),
        "insights_count": len(insights),
        "insights": insights
    }

@router.post("/generate-alerts")
def generate_smart_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Gera alertas inteligentes baseados nos padrões financeiros"""
    
    alerts_created = []
    
    # Verificar gastos acima da média
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    recent_transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date,
            Transaction.transaction_type == TransactionType.EXPENSE
        )
    ).all()
    
    if recent_transactions:
        daily_expenses = defaultdict(float)
        for t in recent_transactions:
            day = t.date.date()
            daily_expenses[day] += float(t.amount)
        
        avg_daily_expense = sum(daily_expenses.values()) / len(daily_expenses)
        
        # Verificar últimos 3 dias
        for i in range(3):
            check_date = (end_date - timedelta(days=i)).date()
            if check_date in daily_expenses:
                day_expense = daily_expenses[check_date]
                if day_expense > avg_daily_expense * 1.5:  # 50% acima da média
                    
                    # Verificar se já existe alerta similar
                    existing_alert = db.query(Alert).filter(
                        and_(
                            Alert.company_id == current_user.company_id,
                            Alert.alert_type == AlertType.BUDGET_EXCEEDED,
                            Alert.created_at >= check_date
                        )
                    ).first()
                    
                    if not existing_alert:
                        alert = Alert(
                            title="Gasto acima da média",
                            message=f"Você gastou R$ {day_expense:.2f} em {check_date.strftime('%d/%m')}, {((day_expense/avg_daily_expense-1)*100):.0f}% acima da sua média diária",
                            alert_type=AlertType.BUDGET_EXCEEDED,
                            priority=2,
                            metadata={
                                "date": check_date.isoformat(),
                                "amount": day_expense,
                                "average": avg_daily_expense,
                                "percentage_above": ((day_expense/avg_daily_expense-1)*100)
                            },
                            company_id=current_user.company_id,
                            user_id=current_user.id
                        )
                        
                        db.add(alert)
                        alerts_created.append("high_spending")
    
    db.commit()
    
    return {
        "message": f"{len(alerts_created)} alertas criados",
        "alerts_created": alerts_created
    }

@router.get("/export/{format}")
def export_report(
    format: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    report_type: str = Query("transactions", description="Tipo: transactions, categories, cash_flow"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta relatórios em diferentes formatos"""
    
    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato deve ser 'json' ou 'csv'"
        )
    
    # Buscar dados baseado no tipo de relatório
    if report_type == "transactions":
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.company_id == current_user.company_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        data = []
        for t in transactions:
            data.append({
                "id": t.id,
                "date": t.date.isoformat(),
                "description": t.description,
                "amount": float(t.amount),
                "type": t.transaction_type.value,
                "category": t.category,
                "account_id": t.account_id
            })
    
    elif report_type == "categories":
        # Usar função existente
        categories_report = get_categories_report(
            start_date=start_date,
            end_date=end_date,
            current_user=current_user,
            db=db
        )
        data = categories_report["categories"]
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de relatório não suportado"
        )
    
    return {
        "format": format,
        "report_type": report_type,
        "period": {
            "start_date": start_date.date(),
            "end_date": end_date.date()
        },
        "data": data,
        "total_records": len(data)
    }