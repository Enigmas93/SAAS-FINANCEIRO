from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from models import (
    FinancialGoal, User, Account, GoalStatus, 
    Alert, AlertType, Achievement, AchievementType
)
from schemas_advanced import (
    FinancialGoal as FinancialGoalSchema,
    FinancialGoalCreate, FinancialGoalUpdate,
    GoalStatusSchema
)
from auth import get_current_active_user

router = APIRouter(prefix="/goals", tags=["financial-goals"])

@router.get("/", response_model=List[FinancialGoalSchema])
def get_financial_goals(
    skip: int = 0,
    limit: int = 100,
    status: Optional[GoalStatusSchema] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista todas as metas financeiras do usuário"""
    
    query = db.query(FinancialGoal).filter(
        FinancialGoal.company_id == current_user.company_id
    )
    
    if status:
        query = query.filter(FinancialGoal.status == status)
    
    if category:
        query = query.filter(FinancialGoal.category.ilike(f"%{category}%"))
    
    goals = query.order_by(desc(FinancialGoal.created_at)).offset(skip).limit(limit).all()
    return goals

@router.get("/{goal_id}", response_model=FinancialGoalSchema)
def get_financial_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtém uma meta financeira específica"""
    
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    return goal

@router.post("/", response_model=FinancialGoalSchema)
def create_financial_goal(
    goal: FinancialGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova meta financeira"""
    
    # Verificar se a conta existe (se especificada)
    if goal.account_id:
        account = db.query(Account).filter(
            and_(
                Account.id == goal.account_id,
                Account.company_id == current_user.company_id
            )
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada"
            )
    
    db_goal = FinancialGoal(
        **goal.dict(),
        company_id=current_user.company_id,
        user_id=current_user.id
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    # Criar achievement para criação de meta
    create_goal_achievement(db_goal, db, current_user, "created")
    
    return db_goal

@router.put("/{goal_id}", response_model=FinancialGoalSchema)
def update_financial_goal(
    goal_id: int,
    goal_update: FinancialGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma meta financeira"""
    
    db_goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    update_data = goal_update.dict(exclude_unset=True)
    old_amount = db_goal.current_amount
    
    for field, value in update_data.items():
        setattr(db_goal, field, value)
    
    # Verificar se atingiu a meta
    if (db_goal.current_amount >= db_goal.target_amount and 
        db_goal.status != GoalStatus.COMPLETED):
        db_goal.status = GoalStatus.COMPLETED
        create_goal_achievement(db_goal, db, current_user, "completed")
        create_goal_completion_alert(db_goal, db, current_user)
    
    # Verificar progresso para alertas
    elif old_amount != db_goal.current_amount:
        check_goal_progress_alerts(db_goal, db, current_user)
    
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

@router.delete("/{goal_id}")
def delete_financial_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove uma meta financeira"""
    
    db_goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    db.delete(db_goal)
    db.commit()
    
    return {"message": "Meta financeira removida com sucesso"}

@router.post("/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: int,
    amount: Decimal,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Adiciona uma contribuição à meta"""
    
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor da contribuição deve ser positivo"
        )
    
    db_goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    if db_goal.status != GoalStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível contribuir para uma meta inativa"
        )
    
    # Atualizar valor atual
    old_amount = db_goal.current_amount
    db_goal.current_amount += amount
    
    # Verificar se atingiu a meta
    if db_goal.current_amount >= db_goal.target_amount:
        db_goal.status = GoalStatus.COMPLETED
        create_goal_achievement(db_goal, db, current_user, "completed")
        create_goal_completion_alert(db_goal, db, current_user)
    else:
        check_goal_progress_alerts(db_goal, db, current_user)
    
    db.commit()
    db.refresh(db_goal)
    
    progress_percentage = (db_goal.current_amount / db_goal.target_amount) * 100
    
    return {
        "message": "Contribuição adicionada com sucesso",
        "new_amount": float(db_goal.current_amount),
        "target_amount": float(db_goal.target_amount),
        "progress_percentage": min(float(progress_percentage), 100.0),
        "is_completed": db_goal.status == GoalStatus.COMPLETED,
        "remaining_amount": max(0, float(db_goal.target_amount - db_goal.current_amount))
    }

@router.get("/summary/overview")
def get_goals_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resumo geral das metas financeiras"""
    
    goals = db.query(FinancialGoal).filter(
        FinancialGoal.company_id == current_user.company_id
    ).all()
    
    active_goals = [g for g in goals if g.status == GoalStatus.ACTIVE]
    completed_goals = [g for g in goals if g.status == GoalStatus.COMPLETED]
    
    total_target = sum(goal.target_amount for goal in active_goals)
    total_saved = sum(goal.current_amount for goal in active_goals)
    
    # Metas por categoria
    goals_by_category = {}
    for goal in active_goals:
        category = goal.category or "Outros"
        if category not in goals_by_category:
            goals_by_category[category] = {
                "count": 0,
                "target_amount": 0,
                "current_amount": 0
            }
        goals_by_category[category]["count"] += 1
        goals_by_category[category]["target_amount"] += float(goal.target_amount)
        goals_by_category[category]["current_amount"] += float(goal.current_amount)
    
    # Metas próximas do prazo
    upcoming_deadlines = []
    today = datetime.now()
    for goal in active_goals:
        if goal.target_date:
            days_remaining = (goal.target_date - today).days
            if 0 <= days_remaining <= 30:
                progress = (goal.current_amount / goal.target_amount) * 100
                upcoming_deadlines.append({
                    "id": goal.id,
                    "name": goal.name,
                    "target_date": goal.target_date,
                    "days_remaining": days_remaining,
                    "progress_percentage": float(progress),
                    "remaining_amount": float(goal.target_amount - goal.current_amount)
                })
    
    return {
        "total_goals": len(goals),
        "active_goals": len(active_goals),
        "completed_goals": len(completed_goals),
        "total_target_amount": float(total_target),
        "total_saved_amount": float(total_saved),
        "overall_progress": float((total_saved / total_target * 100) if total_target > 0 else 0),
        "goals_by_category": goals_by_category,
        "upcoming_deadlines": sorted(upcoming_deadlines, key=lambda x: x["days_remaining"])
    }

@router.get("/{goal_id}/progress-history")
def get_goal_progress_history(
    goal_id: int,
    days: int = Query(30, description="Número de dias para histórico"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Histórico de progresso de uma meta (simulado)"""
    
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    # Simular histórico baseado no progresso atual
    # Em uma implementação real, isso viria de uma tabela de histórico
    history = []
    current_progress = goal.current_amount
    daily_increment = current_progress / days if days > 0 else 0
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        amount = daily_increment * (i + 1)
        progress_percentage = (amount / goal.target_amount) * 100
        
        history.append({
            "date": date.date(),
            "amount": float(amount),
            "progress_percentage": min(float(progress_percentage), 100.0)
        })
    
    return {
        "goal_id": goal_id,
        "goal_name": goal.name,
        "target_amount": float(goal.target_amount),
        "current_amount": float(goal.current_amount),
        "history": history
    }

def create_goal_achievement(goal: FinancialGoal, db: Session, user: User, action: str):
    """Cria achievement relacionado a metas"""
    
    if action == "created":
        achievement = Achievement(
            name="Primeira Meta",
            description=f"Criou sua primeira meta financeira: {goal.name}",
            achievement_type=AchievementType.GOAL_COMPLETED,
            icon="🎯",
            points=10,
            is_unlocked=True,
            unlocked_at=datetime.now(),
            progress_current=1,
            progress_target=1,
            metadata={"goal_id": goal.id, "action": "created"},
            company_id=user.company_id,
            user_id=user.id
        )
    elif action == "completed":
        achievement = Achievement(
            name="Meta Alcançada",
            description=f"Completou a meta '{goal.name}' de R$ {goal.target_amount}",
            achievement_type=AchievementType.GOAL_COMPLETED,
            icon="🏆",
            points=50,
            is_unlocked=True,
            unlocked_at=datetime.now(),
            progress_current=1,
            progress_target=1,
            metadata={"goal_id": goal.id, "amount": float(goal.target_amount)},
            company_id=user.company_id,
            user_id=user.id
        )
    
    db.add(achievement)

def create_goal_completion_alert(goal: FinancialGoal, db: Session, user: User):
    """Cria alerta para meta completada"""
    
    alert = Alert(
        title=f"🎉 Meta alcançada: {goal.name}",
        message=f"Parabéns! Você atingiu sua meta de R$ {goal.target_amount}. Continue assim!",
        alert_type=AlertType.GOAL_PROGRESS,
        priority=1,
        metadata={
            "goal_id": goal.id,
            "target_amount": float(goal.target_amount),
            "completion_date": datetime.now().isoformat()
        },
        company_id=user.company_id,
        user_id=user.id
    )
    
    db.add(alert)

def check_goal_progress_alerts(goal: FinancialGoal, db: Session, user: User):
    """Verifica se deve criar alertas de progresso"""
    
    progress_percentage = (goal.current_amount / goal.target_amount) * 100
    
    # Alertas em marcos específicos (25%, 50%, 75%)
    milestones = [25, 50, 75]
    
    for milestone in milestones:
        if progress_percentage >= milestone:
            # Verificar se já existe alerta para este marco
            existing_alert = db.query(Alert).filter(
                and_(
                    Alert.company_id == user.company_id,
                    Alert.user_id == user.id,
                    Alert.alert_type == AlertType.GOAL_PROGRESS,
                    Alert.metadata.contains({"goal_id": goal.id, "milestone": milestone})
                )
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    title=f"Progresso da meta: {goal.name}",
                    message=f"Você já alcançou {milestone}% da sua meta! Continue assim!",
                    alert_type=AlertType.GOAL_PROGRESS,
                    priority=1,
                    metadata={
                        "goal_id": goal.id,
                        "milestone": milestone,
                        "current_amount": float(goal.current_amount),
                        "target_amount": float(goal.target_amount)
                    },
                    company_id=user.company_id,
                    user_id=user.id
                )
                db.add(alert)

@router.post("/auto-transfer/{goal_id}")
def setup_auto_transfer(
    goal_id: int,
    enable: bool,
    monthly_amount: Optional[Decimal] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Configura transferência automática para meta"""
    
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.company_id == current_user.company_id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta financeira não encontrada"
        )
    
    goal.auto_transfer = enable
    if monthly_amount:
        goal.monthly_target = monthly_amount
    
    db.commit()
    db.refresh(goal)
    
    return {
        "message": f"Transferência automática {'ativada' if enable else 'desativada'}",
        "auto_transfer": goal.auto_transfer,
        "monthly_target": float(goal.monthly_target) if goal.monthly_target else None
    }