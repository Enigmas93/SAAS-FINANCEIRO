from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from auth import get_current_active_user
from models import (
    User, Account, Transaction, TransactionType, BankConnection, 
    BankConnectionStatus, Debt, DebtStatus, FinancialGoal, GoalStatus,
    Alert, AlertType
)
from schemas_advanced import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/consolidated")
async def get_consolidated_dashboard(
    period_days: int = Query(30, description="Período em dias para análise"),
    include_personal: bool = Query(True, description="Incluir transações pessoais"),
    include_business: bool = Query(True, description="Incluir transações empresariais"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Painel consolidado com visão geral de todas as contas"""
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Filtros de transação baseados nas preferências
        transaction_filters = [Transaction.company_id == current_user.company_id]
        
        if not include_personal and not include_business:
            raise HTTPException(status_code=400, detail="Deve incluir pelo menos um tipo de transação")
        
        if include_personal and not include_business:
            transaction_filters.append(Transaction.is_personal == True)
        elif include_business and not include_personal:
            transaction_filters.append(Transaction.is_personal == False)
        # Se ambos são True, não adiciona filtro
        
        # Resumo de contas
        accounts = db.query(Account).filter(
            Account.company_id == current_user.company_id
        ).all()
        
        accounts_summary = []
        total_balance = Decimal('0')
        
        for account in accounts:
            account_balance = account.balance or Decimal('0')
            total_balance += account_balance
            
            # Transações recentes da conta
            recent_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    *transaction_filters
                )
            ).count()
            
            accounts_summary.append({
                "id": account.id,
                "name": account.name,
                "bank": account.bank,
                "account_type": account.account_type,
                "balance": float(account_balance),
                "recent_transactions": recent_transactions,
                "is_active": account.is_active
            })
        
        # Conexões bancárias
        bank_connections = db.query(BankConnection).filter(
            BankConnection.company_id == current_user.company_id
        ).all()
        
        connections_summary = []
        for connection in bank_connections:
            connections_summary.append({
                "id": connection.id,
                "bank_name": connection.bank_name,
                "status": connection.status.value,
                "last_sync": connection.last_sync.isoformat() if connection.last_sync else None,
                "is_active": connection.is_active
            })
        
        # Resumo financeiro do período
        income_query = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.transaction_type == TransactionType.INCOME,
                Transaction.date >= start_date,
                *transaction_filters
            )
        ).scalar() or Decimal('0')
        
        expense_query = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.date >= start_date,
                *transaction_filters
            )
        ).scalar() or Decimal('0')
        
        net_flow = income_query - abs(expense_query)
        
        # Transações por categoria
        category_expenses = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            and_(
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.date >= start_date,
                Transaction.category.isnot(None),
                *transaction_filters
            )
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).limit(10).all()
        
        categories_data = []
        for category, total in category_expenses:
            categories_data.append({
                "category": category,
                "amount": float(abs(total)),
                "percentage": round(float(abs(total)) / float(abs(expense_query)) * 100, 1) if expense_query else 0
            })
        
        # Dívidas ativas
        active_debts = db.query(Debt).filter(
            and_(
                Debt.company_id == current_user.company_id,
                Debt.status.in_([DebtStatus.ACTIVE, DebtStatus.OVERDUE])
            )
        ).all()
        
        debts_summary = {
            "total_debts": len(active_debts),
            "total_amount": sum(float(debt.remaining_amount or debt.total_amount) for debt in active_debts),
            "overdue_count": len([d for d in active_debts if d.status == DebtStatus.OVERDUE]),
            "next_payment_date": min([d.next_payment_date for d in active_debts if d.next_payment_date], default=None)
        }
        
        # Metas financeiras
        active_goals = db.query(FinancialGoal).filter(
            and_(
                FinancialGoal.company_id == current_user.company_id,
                FinancialGoal.status == GoalStatus.ACTIVE
            )
        ).all()
        
        goals_summary = []
        for goal in active_goals:
            progress_percentage = (float(goal.current_amount) / float(goal.target_amount)) * 100 if goal.target_amount else 0
            
            goals_summary.append({
                "id": goal.id,
                "name": goal.name,
                "target_amount": float(goal.target_amount),
                "current_amount": float(goal.current_amount),
                "progress_percentage": round(progress_percentage, 1),
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "days_remaining": (goal.target_date - datetime.now().date()).days if goal.target_date else None
            })
        
        # Alertas ativos
        active_alerts = db.query(Alert).filter(
            and_(
                Alert.company_id == current_user.company_id,
                Alert.is_read == False
            )
        ).order_by(Alert.created_at.desc()).limit(5).all()
        
        alerts_summary = []
        for alert in active_alerts:
            alerts_summary.append({
                "id": alert.id,
                "type": alert.alert_type.value,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "priority": alert.priority
            })
        
        # Fluxo de caixa dos últimos 7 dias
        cash_flow_data = []
        for i in range(7):
            day = end_date - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_income = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.transaction_type == TransactionType.INCOME,
                    Transaction.date >= day_start,
                    Transaction.date <= day_end,
                    *transaction_filters
                )
            ).scalar() or Decimal('0')
            
            day_expense = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.date >= day_start,
                    Transaction.date <= day_end,
                    *transaction_filters
                )
            ).scalar() or Decimal('0')
            
            cash_flow_data.append({
                "date": day.strftime("%Y-%m-%d"),
                "income": float(day_income),
                "expense": float(abs(day_expense)),
                "net": float(day_income - abs(day_expense))
            })
        
        cash_flow_data.reverse()  # Ordem cronológica
        
        # Comparação com período anterior
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date
        
        previous_income = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.transaction_type == TransactionType.INCOME,
                Transaction.date >= previous_start,
                Transaction.date < previous_end,
                *transaction_filters
            )
        ).scalar() or Decimal('0')
        
        previous_expense = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.date >= previous_start,
                Transaction.date < previous_end,
                *transaction_filters
            )
        ).scalar() or Decimal('0')
        
        income_change = ((float(income_query) - float(previous_income)) / float(previous_income) * 100) if previous_income else 0
        expense_change = ((float(abs(expense_query)) - float(abs(previous_expense))) / float(abs(previous_expense)) * 100) if previous_expense else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "accounts": {
                "total_balance": float(total_balance),
                "accounts_count": len(accounts),
                "accounts": accounts_summary
            },
            "bank_connections": {
                "total_connections": len(bank_connections),
                "active_connections": len([c for c in bank_connections if c.is_active]),
                "connections": connections_summary
            },
            "financial_summary": {
                "total_income": float(income_query),
                "total_expense": float(abs(expense_query)),
                "net_flow": float(net_flow),
                "income_change_percentage": round(income_change, 1),
                "expense_change_percentage": round(expense_change, 1)
            },
            "categories": categories_data,
            "debts": debts_summary,
            "goals": {
                "active_goals": len(active_goals),
                "goals": goals_summary
            },
            "alerts": {
                "unread_count": len(active_alerts),
                "alerts": alerts_summary
            },
            "cash_flow": cash_flow_data,
            "filters_applied": {
                "include_personal": include_personal,
                "include_business": include_business
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(e)}")

@router.get("/accounts-overview")
async def get_accounts_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Visão detalhada de todas as contas"""
    
    try:
        accounts = db.query(Account).filter(
            Account.company_id == current_user.company_id
        ).all()
        
        accounts_data = []
        
        for account in accounts:
            # Últimas transações da conta
            recent_transactions = db.query(Transaction).filter(
                Transaction.account_id == account.id
            ).order_by(Transaction.date.desc()).limit(5).all()
            
            transactions_data = []
            for transaction in recent_transactions:
                transactions_data.append({
                    "id": transaction.id,
                    "description": transaction.description,
                    "amount": float(transaction.amount),
                    "type": transaction.transaction_type.value,
                    "date": transaction.date.isoformat(),
                    "category": transaction.category
                })
            
            # Estatísticas da conta (últimos 30 dias)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            monthly_income = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.transaction_type == TransactionType.INCOME,
                    Transaction.date >= thirty_days_ago
                )
            ).scalar() or Decimal('0')
            
            monthly_expense = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.date >= thirty_days_ago
                )
            ).scalar() or Decimal('0')
            
            transaction_count = db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= thirty_days_ago
                )
            ).count()
            
            accounts_data.append({
                "id": account.id,
                "name": account.name,
                "bank": account.bank,
                "account_type": account.account_type,
                "balance": float(account.balance or Decimal('0')),
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat(),
                "monthly_stats": {
                    "income": float(monthly_income),
                    "expense": float(abs(monthly_expense)),
                    "net": float(monthly_income - abs(monthly_expense)),
                    "transaction_count": transaction_count
                },
                "recent_transactions": transactions_data
            })
        
        return {
            "accounts": accounts_data,
            "total_accounts": len(accounts),
            "active_accounts": len([a for a in accounts if a.is_active]),
            "total_balance": sum(float(a.balance or Decimal('0')) for a in accounts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contas: {str(e)}")

@router.get("/quick-stats")
async def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Estatísticas rápidas para widgets"""
    
    try:
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        
        # Saldo total
        total_balance = db.query(func.sum(Account.balance)).filter(
            Account.company_id == current_user.company_id
        ).scalar() or Decimal('0')
        
        # Gastos do mês
        monthly_expenses = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.company_id == current_user.company_id,
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.date >= this_month_start
            )
        ).scalar() or Decimal('0')
        
        # Receitas do mês
        monthly_income = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.company_id == current_user.company_id,
                Transaction.transaction_type == TransactionType.INCOME,
                Transaction.date >= this_month_start
            )
        ).scalar() or Decimal('0')
        
        # Dívidas pendentes
        pending_debts = db.query(func.sum(Debt.remaining_amount)).filter(
            and_(
                Debt.company_id == current_user.company_id,
                Debt.status.in_([DebtStatus.ACTIVE, DebtStatus.OVERDUE])
            )
        ).scalar() or Decimal('0')
        
        # Metas ativas
        active_goals_count = db.query(FinancialGoal).filter(
            and_(
                FinancialGoal.company_id == current_user.company_id,
                FinancialGoal.status == GoalStatus.ACTIVE
            )
        ).count()
        
        # Alertas não lidos
        unread_alerts = db.query(Alert).filter(
            and_(
                Alert.company_id == current_user.company_id,
                Alert.is_read == False
            )
        ).count()
        
        return {
            "total_balance": float(total_balance),
            "monthly_income": float(monthly_income),
            "monthly_expenses": float(abs(monthly_expenses)),
            "monthly_net": float(monthly_income - abs(monthly_expenses)),
            "pending_debts": float(pending_debts),
            "active_goals": active_goals_count,
            "unread_alerts": unread_alerts,
            "reference_date": today.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")