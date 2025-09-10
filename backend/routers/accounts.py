from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from database import get_db
from models import Account, User
from schemas import Account as AccountSchema, AccountCreate, AccountUpdate
from auth import get_current_active_user

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/", response_model=List[AccountSchema])
def get_accounts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista todas as contas da empresa do usuário"""
    accounts = db.query(Account).filter(
        Account.company_id == current_user.company_id,
        Account.is_active == True
    ).offset(skip).limit(limit).all()
    return accounts

@router.get("/{account_id}", response_model=AccountSchema)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtém uma conta específica"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.company_id == current_user.company_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account

@router.post("/", response_model=AccountSchema)
def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova conta financeira"""
    
    # Verifica se já existe uma conta com o mesmo nome na empresa
    existing_account = db.query(Account).filter(
        Account.name == account_data.name,
        Account.company_id == current_user.company_id,
        Account.is_active == True
    ).first()
    
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this name already exists"
        )
    
    account = Account(
        **account_data.dict(),
        company_id=current_user.company_id
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account

@router.put("/{account_id}", response_model=AccountSchema)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma conta financeira"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.company_id == current_user.company_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Verifica se o novo nome já existe (se foi alterado)
    if account_data.name and account_data.name != account.name:
        existing_account = db.query(Account).filter(
            Account.name == account_data.name,
            Account.company_id == current_user.company_id,
            Account.is_active == True,
            Account.id != account_id
        ).first()
        
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account with this name already exists"
            )
    
    # Atualiza apenas os campos fornecidos
    update_data = account_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return account

@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Desativa uma conta financeira (soft delete)"""
    
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.company_id == current_user.company_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Soft delete - apenas marca como inativa
    account.is_active = False
    db.commit()
    
    return {"message": "Account deactivated successfully"}

@router.get("/summary/balances")
def get_accounts_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna resumo dos saldos de todas as contas"""
    
    accounts = db.query(Account).filter(
        Account.company_id == current_user.company_id,
        Account.is_active == True
    ).all()
    
    total_balance = sum(account.balance for account in accounts)
    
    accounts_by_type = {}
    for account in accounts:
        account_type = account.account_type.value
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = {
                "count": 0,
                "total_balance": Decimal('0.00')
            }
        accounts_by_type[account_type]["count"] += 1
        accounts_by_type[account_type]["total_balance"] += account.balance
    
    return {
        "total_accounts": len(accounts),
        "total_balance": total_balance,
        "accounts_by_type": accounts_by_type,
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "type": account.account_type.value,
                "balance": account.balance
            }
            for account in accounts
        ]
    }