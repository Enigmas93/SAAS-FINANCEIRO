from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from database import get_db
from models import Transaction, Account, User, TransactionType
from schemas import Transaction as TransactionSchema, TransactionCreate, TransactionUpdate
from auth import get_current_active_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/", response_model=List[TransactionSchema])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista transações com filtros opcionais"""
    
    query = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id
    )
    
    # Aplicar filtros
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category}%"))
    
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    
    if account_id:
        query = query.filter(
            or_(
                Transaction.from_account_id == account_id,
                Transaction.to_account_id == account_id
            )
        )
    
    transactions = query.order_by(desc(Transaction.transaction_date)).offset(skip).limit(limit).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtém uma transação específica"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.company_id == current_user.company_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.post("/", response_model=TransactionSchema)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova transação"""
    
    # Validações específicas por tipo de transação
    if transaction_data.transaction_type == TransactionType.INCOME:
        if not transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Income transactions require to_account_id"
            )
        if transaction_data.from_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Income transactions should not have from_account_id"
            )
    
    elif transaction_data.transaction_type == TransactionType.EXPENSE:
        if not transaction_data.from_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense transactions require from_account_id"
            )
        if transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense transactions should not have to_account_id"
            )
    
    elif transaction_data.transaction_type == TransactionType.TRANSFER:
        if not transaction_data.from_account_id or not transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer transactions require both from_account_id and to_account_id"
            )
        if transaction_data.from_account_id == transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to the same account"
            )
    
    # Verificar se as contas pertencem à empresa do usuário
    if transaction_data.from_account_id:
        from_account = db.query(Account).filter(
            Account.id == transaction_data.from_account_id,
            Account.company_id == current_user.company_id,
            Account.is_active == True
        ).first()
        if not from_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="From account not found or inactive"
            )
    
    if transaction_data.to_account_id:
        to_account = db.query(Account).filter(
            Account.id == transaction_data.to_account_id,
            Account.company_id == current_user.company_id,
            Account.is_active == True
        ).first()
        if not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="To account not found or inactive"
            )
    
    # Criar a transação
    transaction = Transaction(
        **transaction_data.dict(),
        company_id=current_user.company_id,
        user_id=current_user.id
    )
    
    db.add(transaction)
    
    # Atualizar saldos das contas
    if transaction_data.transaction_type == TransactionType.INCOME:
        to_account.balance += transaction_data.amount
    
    elif transaction_data.transaction_type == TransactionType.EXPENSE:
        from_account.balance -= transaction_data.amount
    
    elif transaction_data.transaction_type == TransactionType.TRANSFER:
        from_account.balance -= transaction_data.amount
        to_account.balance += transaction_data.amount
    
    db.commit()
    db.refresh(transaction)
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma transação"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.company_id == current_user.company_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Reverter o impacto da transação original nos saldos
    if transaction.transaction_type == TransactionType.INCOME and transaction.to_account_id:
        to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
        if to_account:
            to_account.balance -= transaction.amount
    
    elif transaction.transaction_type == TransactionType.EXPENSE and transaction.from_account_id:
        from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
        if from_account:
            from_account.balance += transaction.amount
    
    elif transaction.transaction_type == TransactionType.TRANSFER:
        if transaction.from_account_id:
            from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
            if from_account:
                from_account.balance += transaction.amount
        if transaction.to_account_id:
            to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
            if to_account:
                to_account.balance -= transaction.amount
    
    # Atualizar os campos da transação
    update_data = transaction_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Aplicar o novo impacto nos saldos
    if transaction.transaction_type == TransactionType.INCOME and transaction.to_account_id:
        to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
        if to_account:
            to_account.balance += transaction.amount
    
    elif transaction.transaction_type == TransactionType.EXPENSE and transaction.from_account_id:
        from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
        if from_account:
            from_account.balance -= transaction.amount
    
    elif transaction.transaction_type == TransactionType.TRANSFER:
        if transaction.from_account_id:
            from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
            if from_account:
                from_account.balance -= transaction.amount
        if transaction.to_account_id:
            to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
            if to_account:
                to_account.balance += transaction.amount
    
    db.commit()
    db.refresh(transaction)
    
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exclui uma transação e reverte o impacto nos saldos"""
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.company_id == current_user.company_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Reverter o impacto nos saldos
    if transaction.transaction_type == TransactionType.INCOME and transaction.to_account_id:
        to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
        if to_account:
            to_account.balance -= transaction.amount
    
    elif transaction.transaction_type == TransactionType.EXPENSE and transaction.from_account_id:
        from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
        if from_account:
            from_account.balance += transaction.amount
    
    elif transaction.transaction_type == TransactionType.TRANSFER:
        if transaction.from_account_id:
            from_account = db.query(Account).filter(Account.id == transaction.from_account_id).first()
            if from_account:
                from_account.balance += transaction.amount
        if transaction.to_account_id:
            to_account = db.query(Account).filter(Account.id == transaction.to_account_id).first()
            if to_account:
                to_account.balance -= transaction.amount
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}

@router.get("/summary/by-category")
def get_transactions_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna resumo de transações agrupadas por categoria"""
    
    query = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id
    )
    
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    
    transactions = query.all()
    
    summary = {
        "income_by_category": {},
        "expense_by_category": {},
        "total_income": Decimal('0.00'),
        "total_expense": Decimal('0.00')
    }
    
    for transaction in transactions:
        category = transaction.category or "Sem categoria"
        
        if transaction.transaction_type == TransactionType.INCOME:
            if category not in summary["income_by_category"]:
                summary["income_by_category"][category] = Decimal('0.00')
            summary["income_by_category"][category] += transaction.amount
            summary["total_income"] += transaction.amount
        
        elif transaction.transaction_type == TransactionType.EXPENSE:
            if category not in summary["expense_by_category"]:
                summary["expense_by_category"][category] = Decimal('0.00')
            summary["expense_by_category"][category] += transaction.amount
            summary["total_expense"] += transaction.amount
    
    summary["net_result"] = summary["total_income"] - summary["total_expense"]
    
    return summary