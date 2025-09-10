from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from models import (
    Achievement, User, Transaction, FinancialGoal, 
    AchievementType, TransactionType, Alert, AlertType
)
from schemas_advanced import (
    Achievement as AchievementSchema,
    AchievementCreate, AchievementUpdate
)
from auth import get_current_active_user

router = APIRouter(prefix="/gamification", tags=["gamification"])

@router.get("/achievements", response_model=List[AchievementSchema])
def get_user_achievements(
    skip: int = 0,
    limit: int = 100,
    unlocked_only: bool = Query(False, description="Mostrar apenas conquistas desbloqueadas"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista todas as conquistas do usuário"""
    
    query = db.query(Achievement).filter(
        Achievement.company_id == current_user.company_id
    )
    
    if unlocked_only:
        query = query.filter(Achievement.is_unlocked == True)
    
    achievements = query.order_by(
        desc(Achievement.is_unlocked),
        desc(Achievement.unlocked_at),
        Achievement.name
    ).offset(skip).limit(limit).all()
    
    return achievements

@router.get("/achievements/{achievement_id}", response_model=AchievementSchema)
def get_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtém uma conquista específica"""
    
    achievement = db.query(Achievement).filter(
        and_(
            Achievement.id == achievement_id,
            Achievement.company_id == current_user.company_id
        )
    ).first()
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conquista não encontrada"
        )
    
    return achievement

@router.get("/profile")
def get_gamification_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perfil de gamificação do usuário"""
    
    # Conquistas do usuário
    achievements = db.query(Achievement).filter(
        Achievement.company_id == current_user.company_id
    ).all()
    
    unlocked_achievements = [a for a in achievements if a.is_unlocked]
    total_points = sum(a.points for a in unlocked_achievements)
    
    # Estatísticas por tipo de conquista
    achievement_stats = {}
    for achievement_type in AchievementType:
        type_achievements = [a for a in unlocked_achievements if a.achievement_type == achievement_type]
        achievement_stats[achievement_type.value] = {
            "count": len(type_achievements),
            "points": sum(a.points for a in type_achievements)
        }
    
    # Nível baseado em pontos
    level = calculate_user_level(total_points)
    points_for_next_level = calculate_points_for_next_level(level)
    
    # Conquistas recentes (últimos 30 dias)
    recent_date = datetime.now() - timedelta(days=30)
    recent_achievements = [
        a for a in unlocked_achievements 
        if a.unlocked_at and a.unlocked_at >= recent_date
    ]
    
    # Ranking (simulado - em produção seria baseado em todos os usuários)
    user_rank = calculate_user_rank(total_points, db, current_user.company_id)
    
    return {
        "user_id": current_user.id,
        "level": level,
        "total_points": total_points,
        "points_for_next_level": points_for_next_level,
        "achievements_summary": {
            "total_achievements": len(achievements),
            "unlocked_achievements": len(unlocked_achievements),
            "completion_percentage": (len(unlocked_achievements) / len(achievements) * 100) if achievements else 0
        },
        "achievement_stats": achievement_stats,
        "recent_achievements": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "points": a.points,
                "unlocked_at": a.unlocked_at
            } for a in sorted(recent_achievements, key=lambda x: x.unlocked_at, reverse=True)[:5]
        ],
        "rank": user_rank
    }

@router.post("/check-achievements")
def check_and_unlock_achievements(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verifica e desbloqueia novas conquistas baseadas nas atividades do usuário"""
    
    new_achievements = []
    
    # Verificar conquistas de transações
    transaction_achievements = check_transaction_achievements(db, current_user)
    new_achievements.extend(transaction_achievements)
    
    # Verificar conquistas de metas
    goal_achievements = check_goal_achievements(db, current_user)
    new_achievements.extend(goal_achievements)
    
    # Verificar conquistas de economia
    saving_achievements = check_saving_achievements(db, current_user)
    new_achievements.extend(saving_achievements)
    
    # Verificar conquistas de consistência
    consistency_achievements = check_consistency_achievements(db, current_user)
    new_achievements.extend(consistency_achievements)
    
    # Salvar novas conquistas
    for achievement_data in new_achievements:
        achievement = Achievement(**achievement_data)
        db.add(achievement)
    
    if new_achievements:
        db.commit()
        
        # Criar alertas para novas conquistas
        for achievement_data in new_achievements:
            create_achievement_alert(achievement_data, db, current_user)
    
    return {
        "message": f"{len(new_achievements)} nova(s) conquista(s) desbloqueada(s)",
        "new_achievements": new_achievements
    }

@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(10, description="Número de usuários no ranking"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ranking de usuários por pontos (dentro da empresa)"""
    
    # Buscar todos os usuários da empresa com suas conquistas
    users_with_points = db.query(
        User.id,
        User.name,
        func.coalesce(func.sum(Achievement.points), 0).label('total_points'),
        func.count(Achievement.id).label('achievements_count')
    ).outerjoin(
        Achievement, and_(
            Achievement.user_id == User.id,
            Achievement.is_unlocked == True
        )
    ).filter(
        User.company_id == current_user.company_id
    ).group_by(
        User.id, User.name
    ).order_by(
        desc('total_points')
    ).limit(limit).all()
    
    leaderboard = []
    for i, (user_id, name, points, achievements_count) in enumerate(users_with_points, 1):
        level = calculate_user_level(points)
        
        leaderboard.append({
            "rank": i,
            "user_id": user_id,
            "name": name,
            "total_points": int(points),
            "level": level,
            "achievements_count": int(achievements_count),
            "is_current_user": user_id == current_user.id
        })
    
    # Encontrar posição do usuário atual se não estiver no top
    current_user_rank = None
    for entry in leaderboard:
        if entry["is_current_user"]:
            current_user_rank = entry["rank"]
            break
    
    if not current_user_rank:
        # Calcular posição real do usuário
        user_points = db.query(
            func.coalesce(func.sum(Achievement.points), 0)
        ).filter(
            and_(
                Achievement.user_id == current_user.id,
                Achievement.is_unlocked == True
            )
        ).scalar() or 0
        
        users_above = db.query(
            func.count(func.distinct(User.id))
        ).select_from(
            User
        ).outerjoin(
            Achievement, and_(
                Achievement.user_id == User.id,
                Achievement.is_unlocked == True
            )
        ).filter(
            User.company_id == current_user.company_id
        ).group_by(
            User.id
        ).having(
            func.coalesce(func.sum(Achievement.points), 0) > user_points
        ).scalar() or 0
        
        current_user_rank = users_above + 1
    
    return {
        "leaderboard": leaderboard,
        "current_user_rank": current_user_rank,
        "total_users": len(users_with_points)
    }

@router.get("/challenges")
def get_active_challenges(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista desafios ativos para o usuário"""
    
    challenges = []
    
    # Desafio: Registrar transações por 7 dias consecutivos
    consecutive_days = get_consecutive_transaction_days(db, current_user)
    challenges.append({
        "id": "consecutive_transactions",
        "name": "Registros Consistentes",
        "description": "Registre transações por 7 dias consecutivos",
        "icon": "📅",
        "progress_current": min(consecutive_days, 7),
        "progress_target": 7,
        "progress_percentage": min((consecutive_days / 7) * 100, 100),
        "reward_points": 50,
        "is_completed": consecutive_days >= 7
    })
    
    # Desafio: Economizar R$ 500 este mês
    monthly_savings = get_monthly_savings(db, current_user)
    target_savings = 500
    challenges.append({
        "id": "monthly_savings",
        "name": "Poupador do Mês",
        "description": f"Economize R$ {target_savings} este mês",
        "icon": "💰",
        "progress_current": min(float(monthly_savings), target_savings),
        "progress_target": target_savings,
        "progress_percentage": min((float(monthly_savings) / target_savings) * 100, 100),
        "reward_points": 100,
        "is_completed": monthly_savings >= target_savings
    })
    
    # Desafio: Categorizar 50 transações
    categorized_transactions = get_categorized_transactions_count(db, current_user)
    challenges.append({
        "id": "categorize_transactions",
        "name": "Organizador Expert",
        "description": "Categorize 50 transações",
        "icon": "🏷️",
        "progress_current": min(categorized_transactions, 50),
        "progress_target": 50,
        "progress_percentage": min((categorized_transactions / 50) * 100, 100),
        "reward_points": 30,
        "is_completed": categorized_transactions >= 50
    })
    
    # Desafio: Completar uma meta financeira
    completed_goals = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.company_id == current_user.company_id,
            FinancialGoal.status == "COMPLETED"
        )
    ).count()
    
    challenges.append({
        "id": "complete_goal",
        "name": "Realizador de Sonhos",
        "description": "Complete sua primeira meta financeira",
        "icon": "🎯",
        "progress_current": min(completed_goals, 1),
        "progress_target": 1,
        "progress_percentage": min(completed_goals * 100, 100),
        "reward_points": 200,
        "is_completed": completed_goals >= 1
    })
    
    return {
        "challenges": challenges,
        "active_challenges": len([c for c in challenges if not c["is_completed"]]),
        "completed_challenges": len([c for c in challenges if c["is_completed"]])
    }

@router.get("/motivational-messages")
def get_motivational_messages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mensagens motivacionais personalizadas"""
    
    messages = []
    
    # Analisar padrões do usuário
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.date >= start_date
        )
    ).all()
    
    income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
    savings = income - expense
    
    # Mensagens baseadas no desempenho
    if savings > 0:
        messages.append({
            "type": "positive",
            "title": "Parabéns! 🎉",
            "message": f"Você economizou R$ {savings:.2f} este mês. Continue assim!",
            "icon": "💚",
            "action": "Criar nova meta de economia"
        })
    else:
        messages.append({
            "type": "motivational",
            "title": "Vamos melhorar! 💪",
            "message": "Pequenos ajustes nos gastos podem fazer grande diferença.",
            "icon": "📈",
            "action": "Ver relatório de gastos"
        })
    
    # Mensagem sobre metas
    active_goals = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.company_id == current_user.company_id,
            FinancialGoal.status == "ACTIVE"
        )
    ).count()
    
    if active_goals == 0:
        messages.append({
            "type": "suggestion",
            "title": "Defina seus objetivos! 🎯",
            "message": "Criar metas financeiras aumenta suas chances de sucesso em 42%.",
            "icon": "🚀",
            "action": "Criar primeira meta"
        })
    
    # Mensagem sobre conquistas
    recent_achievements = db.query(Achievement).filter(
        and_(
            Achievement.company_id == current_user.company_id,
            Achievement.is_unlocked == True,
            Achievement.unlocked_at >= end_date - timedelta(days=7)
        )
    ).count()
    
    if recent_achievements > 0:
        messages.append({
            "type": "celebration",
            "title": "Você está arrasando! ⭐",
            "message": f"Desbloqueou {recent_achievements} conquista(s) esta semana!",
            "icon": "🏆",
            "action": "Ver todas as conquistas"
        })
    
    return {
        "messages": messages,
        "generated_at": datetime.now()
    }

# Funções auxiliares

def calculate_user_level(points: int) -> int:
    """Calcula o nível do usuário baseado nos pontos"""
    if points < 100:
        return 1
    elif points < 300:
        return 2
    elif points < 600:
        return 3
    elif points < 1000:
        return 4
    elif points < 1500:
        return 5
    else:
        return min(10, 5 + (points - 1500) // 500)

def calculate_points_for_next_level(current_level: int) -> int:
    """Calcula pontos necessários para o próximo nível"""
    level_thresholds = [0, 100, 300, 600, 1000, 1500]
    
    if current_level < len(level_thresholds):
        return level_thresholds[current_level]
    else:
        return 1500 + (current_level - 5) * 500

def calculate_user_rank(points: int, db: Session, company_id: int) -> int:
    """Calcula o ranking do usuário na empresa"""
    # Simplificado - em produção seria mais complexo
    return 1  # Placeholder

def check_transaction_achievements(db: Session, user: User) -> List[Dict]:
    """Verifica conquistas relacionadas a transações"""
    achievements = []
    
    # Primeira transação
    first_transaction = db.query(Transaction).filter(
        Transaction.company_id == user.company_id
    ).first()
    
    if first_transaction:
        existing = db.query(Achievement).filter(
            and_(
                Achievement.company_id == user.company_id,
                Achievement.name == "Primeira Transação"
            )
        ).first()
        
        if not existing:
            achievements.append({
                "name": "Primeira Transação",
                "description": "Registrou sua primeira transação no sistema",
                "achievement_type": AchievementType.FIRST_TRANSACTION,
                "icon": "🎯",
                "points": 10,
                "is_unlocked": True,
                "unlocked_at": datetime.now(),
                "progress_current": 1,
                "progress_target": 1,
                "company_id": user.company_id,
                "user_id": user.id
            })
    
    return achievements

def check_goal_achievements(db: Session, user: User) -> List[Dict]:
    """Verifica conquistas relacionadas a metas"""
    return []  # Implementar conforme necessário

def check_saving_achievements(db: Session, user: User) -> List[Dict]:
    """Verifica conquistas relacionadas a economia"""
    return []  # Implementar conforme necessário

def check_consistency_achievements(db: Session, user: User) -> List[Dict]:
    """Verifica conquistas relacionadas a consistência"""
    return []  # Implementar conforme necessário

def get_consecutive_transaction_days(db: Session, user: User) -> int:
    """Calcula dias consecutivos com transações"""
    # Implementação simplificada
    return 3  # Placeholder

def get_monthly_savings(db: Session, user: User) -> Decimal:
    """Calcula economia do mês atual"""
    start_date = datetime.now().replace(day=1)
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == user.company_id,
            Transaction.date >= start_date
        )
    ).all()
    
    income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
    expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
    
    return max(income - expense, 0)

def get_categorized_transactions_count(db: Session, user: User) -> int:
    """Conta transações categorizadas"""
    return db.query(Transaction).filter(
        and_(
            Transaction.company_id == user.company_id,
            Transaction.category.isnot(None),
            Transaction.category != ""
        )
    ).count()

def create_achievement_alert(achievement_data: Dict, db: Session, user: User):
    """Cria alerta para nova conquista"""
    alert = Alert(
        title=f"🏆 Nova conquista: {achievement_data['name']}",
        message=f"{achievement_data['description']} (+{achievement_data['points']} pontos)",
        alert_type=AlertType.ACHIEVEMENT,
        priority=1,
        metadata={
            "achievement_name": achievement_data['name'],
            "points": achievement_data['points'],
            "icon": achievement_data['icon']
        },
        company_id=user.company_id,
        user_id=user.id
    )
    
    db.add(alert)