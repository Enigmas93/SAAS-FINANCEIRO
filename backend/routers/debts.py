from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from models import Debt, User, DebtStatus, DebtType, Alert, AlertType
from schemas_advanced import (
    Debt as DebtSchema,
    DebtCreate, DebtUpdate,
    DebtStatusSchema, DebtTypeSchema
)
from auth import get_current_active_user

router = APIRouter(prefix="/debts", tags=["debts"])

@router.get("/", response_model=List[DebtSchema])
def get_debts(
    skip: int = 0,
    limit: int = 100,
    debt_type: Optional[DebtTypeSchema] = None,
    status: Optional[DebtStatusSchema] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista todas as dívidas do usuário"""
    
    query = db.query(Debt).filter(
        Debt.company_id == current_user.company_id
    )
    
    if debt_type:
        query = query.filter(Debt.debt_type == debt_type)
    
    if status:
        query = query.filter(Debt.status == status)
    
    debts = query.order_by(desc(Debt.created_at)).offset(skip).limit(limit).all()
    return debts

@router.get("/{debt_id}", response_model=DebtSchema)
def get_debt(
    debt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtém uma dívida específica"""
    
    debt = db.query(Debt).filter(
        and_(
            Debt.id == debt_id,
            Debt.company_id == current_user.company_id
        )
    ).first()
    
    if not debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dívida não encontrada"
        )
    
    return debt

@router.post("/", response_model=DebtSchema)
def create_debt(
    debt: DebtCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova dívida"""
    
    # Calcular próxima data de vencimento se não fornecida
    next_due_date = None
    if debt.due_day:
        today = datetime.now()
        next_due_date = datetime(today.year, today.month, debt.due_day)
        if next_due_date <= today:
            # Se já passou este mês, próximo mês
            if today.month == 12:
                next_due_date = datetime(today.year + 1, 1, debt.due_day)
            else:
                next_due_date = datetime(today.year, today.month + 1, debt.due_day)
    
    db_debt = Debt(
        **debt.dict(),
        remaining_amount=debt.total_amount,
        next_due_date=next_due_date,
        company_id=current_user.company_id,
        user_id=current_user.id
    )
    
    db.add(db_debt)
    db.commit()
    db.refresh(db_debt)
    
    # Criar alerta se vencimento próximo (7 dias)
    if next_due_date and (next_due_date - datetime.now()).days <= 7:
        create_debt_alert(db_debt, db, current_user)
    
    return db_debt

@router.put("/{debt_id}", response_model=DebtSchema)
def update_debt(
    debt_id: int,
    debt_update: DebtUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma dívida"""
    
    db_debt = db.query(Debt).filter(
        and_(
            Debt.id == debt_id,
            Debt.company_id == current_user.company_id
        )
    ).first()
    
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dívida não encontrada"
        )
    
    update_data = debt_update.dict(exclude_unset=True)
    
    # Se pagou uma parcela, atualizar contadores
    if "installments_paid" in update_data:
        new_paid = update_data["installments_paid"]
        if new_paid > db_debt.installments_paid and db_debt.installment_amount:
            # Calcular novo valor restante
            paid_amount = (new_paid - db_debt.installments_paid) * db_debt.installment_amount
            db_debt.remaining_amount = max(0, db_debt.remaining_amount - paid_amount)
            
            # Se quitou completamente
            if db_debt.remaining_amount == 0 or new_paid >= db_debt.installments_total:
                db_debt.status = DebtStatus.PAID
                update_data["status"] = DebtStatus.PAID
    
    for field, value in update_data.items():
        setattr(db_debt, field, value)
    
    db.commit()
    db.refresh(db_debt)
    
    return db_debt

@router.delete("/{debt_id}")
def delete_debt(
    debt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove uma dívida"""
    
    db_debt = db.query(Debt).filter(
        and_(
            Debt.id == debt_id,
            Debt.company_id == current_user.company_id
        )
    ).first()
    
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dívida não encontrada"
        )
    
    db.delete(db_debt)
    db.commit()
    
    return {"message": "Dívida removida com sucesso"}

@router.post("/{debt_id}/pay-installment")
def pay_installment(
    debt_id: int,
    amount: Optional[Decimal] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Registra pagamento de uma parcela"""
    
    db_debt = db.query(Debt).filter(
        and_(
            Debt.id == debt_id,
            Debt.company_id == current_user.company_id
        )
    ).first()
    
    if not db_debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dívida não encontrada"
        )
    
    if db_debt.status == DebtStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dívida já está quitada"
        )
    
    # Usar valor da parcela padrão se não especificado
    payment_amount = amount or db_debt.installment_amount
    
    if not payment_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor do pagamento deve ser especificado"
        )
    
    # Atualizar dívida
    db_debt.remaining_amount = max(0, db_debt.remaining_amount - payment_amount)
    db_debt.installments_paid += 1
    
    # Calcular próxima data de vencimento
    if db_debt.due_day and db_debt.next_due_date:
        next_month = db_debt.next_due_date + timedelta(days=32)
        db_debt.next_due_date = datetime(next_month.year, next_month.month, db_debt.due_day)
    
    # Verificar se quitou
    if (db_debt.remaining_amount == 0 or 
        (db_debt.installments_total and db_debt.installments_paid >= db_debt.installments_total)):
        db_debt.status = DebtStatus.PAID
        db_debt.next_due_date = None
    
    db.commit()
    db.refresh(db_debt)
    
    return {
        "message": "Pagamento registrado com sucesso",
        "remaining_amount": float(db_debt.remaining_amount),
        "installments_paid": db_debt.installments_paid,
        "is_paid": db_debt.status == DebtStatus.PAID
    }

@router.get("/summary/overview")
def get_debts_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resumo geral das dívidas"""
    
    debts = db.query(Debt).filter(
        Debt.company_id == current_user.company_id
    ).all()
    
    total_debt = sum(debt.remaining_amount for debt in debts if debt.status == DebtStatus.ACTIVE)
    active_debts = len([debt for debt in debts if debt.status == DebtStatus.ACTIVE])
    overdue_debts = len([debt for debt in debts if debt.status == DebtStatus.OVERDUE])
    
    # Próximos vencimentos (30 dias)
    upcoming_due = []
    today = datetime.now()
    for debt in debts:
        if (debt.status == DebtStatus.ACTIVE and debt.next_due_date and 
            debt.next_due_date <= today + timedelta(days=30)):
            upcoming_due.append({
                "id": debt.id,
                "name": debt.name,
                "amount": float(debt.installment_amount or debt.remaining_amount),
                "due_date": debt.next_due_date,
                "days_until_due": (debt.next_due_date - today).days
            })
    
    # Dívidas por tipo
    debts_by_type = {}
    for debt in debts:
        if debt.status == DebtStatus.ACTIVE:
            debt_type = debt.debt_type.value
            if debt_type not in debts_by_type:
                debts_by_type[debt_type] = {"count": 0, "total_amount": 0}
            debts_by_type[debt_type]["count"] += 1
            debts_by_type[debt_type]["total_amount"] += float(debt.remaining_amount)
    
    return {
        "total_debt": float(total_debt),
        "active_debts": active_debts,
        "overdue_debts": overdue_debts,
        "upcoming_due": sorted(upcoming_due, key=lambda x: x["due_date"]),
        "debts_by_type": debts_by_type
    }

@router.post("/check-overdue")
def check_overdue_debts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verifica e marca dívidas em atraso"""
    
    today = datetime.now()
    
    overdue_debts = db.query(Debt).filter(
        and_(
            Debt.company_id == current_user.company_id,
            Debt.status == DebtStatus.ACTIVE,
            Debt.next_due_date < today
        )
    ).all()
    
    updated_count = 0
    for debt in overdue_debts:
        debt.status = DebtStatus.OVERDUE
        create_overdue_alert(debt, db, current_user)
        updated_count += 1
    
    db.commit()
    
    return {
        "message": f"{updated_count} dívidas marcadas como em atraso",
        "overdue_count": updated_count
    }

def create_debt_alert(debt: Debt, db: Session, user: User):
    """Cria alerta para vencimento de dívida"""
    
    days_until_due = (debt.next_due_date - datetime.now()).days if debt.next_due_date else 0
    
    alert = Alert(
        title=f"Vencimento próximo: {debt.name}",
        message=f"A dívida '{debt.name}' vence em {days_until_due} dias. Valor: R$ {debt.installment_amount or debt.remaining_amount}",
        alert_type=AlertType.DEBT_DUE,
        priority=2 if days_until_due <= 3 else 1,
        metadata={
            "debt_id": debt.id,
            "due_date": debt.next_due_date.isoformat() if debt.next_due_date else None,
            "amount": float(debt.installment_amount or debt.remaining_amount)
        },
        company_id=user.company_id,
        user_id=user.id
    )
    
    db.add(alert)

def create_overdue_alert(debt: Debt, db: Session, user: User):
    """Cria alerta para dívida em atraso"""
    
    days_overdue = (datetime.now() - debt.next_due_date).days if debt.next_due_date else 0
    
    alert = Alert(
        title=f"Dívida em atraso: {debt.name}",
        message=f"A dívida '{debt.name}' está {days_overdue} dias em atraso. Valor: R$ {debt.installment_amount or debt.remaining_amount}",
        alert_type=AlertType.DEBT_DUE,
        priority=3,  # Alta prioridade
        metadata={
            "debt_id": debt.id,
            "due_date": debt.next_due_date.isoformat() if debt.next_due_date else None,
            "days_overdue": days_overdue,
            "amount": float(debt.installment_amount or debt.remaining_amount)
        },
        company_id=user.company_id,
        user_id=user.id
    )
    
    db.add(alert)

@router.get("/installment-calendar")
def get_installment_calendar(
    year: int = Query(..., description="Ano para o calendário"),
    month: Optional[int] = Query(None, description="Mês específico (1-12)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calendário de vencimentos de parcelas"""
    
    debts = db.query(Debt).filter(
        and_(
            Debt.company_id == current_user.company_id,
            Debt.status == DebtStatus.ACTIVE,
            Debt.due_day.isnot(None)
        )
    ).all()
    
    calendar_data = {}
    
    # Gerar calendário para o ano/mês especificado
    start_month = month if month else 1
    end_month = month if month else 12
    
    for m in range(start_month, end_month + 1):
        month_key = f"{year}-{m:02d}"
        calendar_data[month_key] = []
        
        for debt in debts:
            if debt.due_day <= 31:  # Validar dia válido
                try:
                    due_date = datetime(year, m, debt.due_day)
                    calendar_data[month_key].append({
                        "debt_id": debt.id,
                        "debt_name": debt.name,
                        "amount": float(debt.installment_amount or debt.remaining_amount),
                        "due_date": due_date.isoformat(),
                        "debt_type": debt.debt_type.value,
                        "creditor": debt.creditor
                    })
                except ValueError:
                    # Dia inválido para o mês (ex: 31 de fevereiro)
                    continue
    
    return calendar_data