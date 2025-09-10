from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime

from database import get_db
from models import User, Company, UserRole, Account, Transaction
from schemas import UserCreate, UserUpdate, User as UserSchema
from auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/permissions", tags=["permissions"])

# Definição de permissões por role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "users": ["create", "read", "update", "delete"],
        "accounts": ["create", "read", "update", "delete"],
        "transactions": ["create", "read", "update", "delete"],
        "reports": ["read", "export"],
        "settings": ["read", "update"],
        "debts": ["create", "read", "update", "delete"],
        "goals": ["create", "read", "update", "delete"],
        "company": ["read", "update"]
    },
    UserRole.MANAGER: {
        "users": ["read"],
        "accounts": ["create", "read", "update"],
        "transactions": ["create", "read", "update", "delete"],
        "reports": ["read", "export"],
        "settings": ["read"],
        "debts": ["create", "read", "update", "delete"],
        "goals": ["create", "read", "update", "delete"],
        "company": ["read"]
    },
    UserRole.EMPLOYEE: {
        "users": [],
        "accounts": ["read"],
        "transactions": ["create", "read"],
        "reports": ["read"],
        "settings": [],
        "debts": ["create", "read", "update"],
        "goals": ["create", "read", "update"],
        "company": []
    },
    UserRole.VIEWER: {
        "users": [],
        "accounts": ["read"],
        "transactions": ["read"],
        "reports": ["read"],
        "settings": [],
        "debts": ["read"],
        "goals": ["read"],
        "company": []
    }
}

def check_permission(user: User, resource: str, action: str) -> bool:
    """Verifica se o usuário tem permissão para executar uma ação em um recurso"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, {})
    resource_permissions = user_permissions.get(resource, [])
    return action in resource_permissions

def require_permission(resource: str, action: str):
    """Decorator para verificar permissões"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada: {action} em {resource}"
            )
        return current_user
    return permission_checker

@router.get("/my-permissions")
def get_my_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """Retorna as permissões do usuário atual"""
    
    user_permissions = ROLE_PERMISSIONS.get(current_user.role, {})
    
    return {
        "user_id": current_user.id,
        "role": current_user.role.value,
        "permissions": user_permissions,
        "company_id": current_user.company_id
    }

@router.get("/users", response_model=List[UserSchema])
def list_company_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db)
):
    """Lista usuários da empresa (apenas admins)"""
    
    query = db.query(User).filter(
        User.company_id == current_user.company_id
    )
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db)
):
    """Obtém informações de um usuário específico"""
    
    user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return user

@router.post("/users", response_model=UserSchema)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("users", "create")),
    db: Session = Depends(get_db)
):
    """Cria um novo usuário na empresa"""
    
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Verificar se o role é válido para o usuário atual
    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem criar outros administradores"
        )
    
    # Criar usuário
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        company_id=current_user.company_id,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_permission("users", "update")),
    db: Session = Depends(get_db)
):
    """Atualiza informações de um usuário"""
    
    # Buscar usuário
    db_user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    ).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se pode alterar o role
    if user_update.role and user_update.role != db_user.role:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem alterar roles"
            )
        
        if user_update.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem promover a administrador"
            )
    
    # Atualizar campos
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "delete")),
    db: Session = Depends(get_db)
):
    """Remove um usuário da empresa"""
    
    # Verificar se não está tentando deletar a si mesmo
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível deletar sua própria conta"
        )
    
    # Buscar usuário
    db_user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    ).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se pode deletar (apenas admin pode deletar admin)
    if db_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem deletar outros administradores"
        )
    
    # Desativar ao invés de deletar (para manter integridade dos dados)
    db_user.is_active = False
    db.commit()
    
    return {"message": "Usuário desativado com sucesso"}

@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "update")),
    db: Session = Depends(get_db)
):
    """Ativa um usuário desativado"""
    
    db_user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    ).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    db_user.is_active = True
    db.commit()
    
    return {"message": "Usuário ativado com sucesso"}

@router.get("/roles")
def get_available_roles(
    current_user: User = Depends(get_current_active_user)
):
    """Lista roles disponíveis baseado no role do usuário atual"""
    
    if current_user.role == UserRole.ADMIN:
        available_roles = list(UserRole)
    elif current_user.role == UserRole.MANAGER:
        available_roles = [UserRole.EMPLOYEE, UserRole.VIEWER]
    else:
        available_roles = []
    
    return {
        "available_roles": [{
            "value": role.value,
            "name": role.value.title(),
            "permissions": ROLE_PERMISSIONS.get(role, {})
        } for role in available_roles]
    }

@router.get("/company/settings")
def get_company_settings(
    current_user: User = Depends(require_permission("company", "read")),
    db: Session = Depends(get_db)
):
    """Obtém configurações da empresa"""
    
    company = db.query(Company).filter(
        Company.id == current_user.company_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Estatísticas da empresa
    users_count = db.query(User).filter(
        User.company_id == current_user.company_id
    ).count()
    
    active_users_count = db.query(User).filter(
        and_(
            User.company_id == current_user.company_id,
            User.is_active == True
        )
    ).count()
    
    accounts_count = db.query(Account).filter(
        Account.company_id == current_user.company_id
    ).count()
    
    transactions_count = db.query(Transaction).filter(
        Transaction.company_id == current_user.company_id
    ).count()
    
    return {
        "company": {
            "id": company.id,
            "name": company.name,
            "cnpj": company.cnpj,
            "created_at": company.created_at
        },
        "statistics": {
            "total_users": users_count,
            "active_users": active_users_count,
            "total_accounts": accounts_count,
            "total_transactions": transactions_count
        }
    }

@router.put("/company/settings")
def update_company_settings(
    company_name: str,
    current_user: User = Depends(require_permission("company", "update")),
    db: Session = Depends(get_db)
):
    """Atualiza configurações da empresa"""
    
    company = db.query(Company).filter(
        Company.id == current_user.company_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    company.name = company_name
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Configurações da empresa atualizadas com sucesso",
        "company": {
            "id": company.id,
            "name": company.name,
            "cnpj": company.cnpj
        }
    }

@router.get("/audit-log")
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db)
):
    """Log de auditoria das ações dos usuários (simulado)"""
    
    # Em uma implementação real, isso viria de uma tabela de auditoria
    # Por agora, retornamos dados simulados
    
    audit_entries = [
        {
            "id": 1,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "action": "login",
            "resource": "auth",
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.100",
            "details": "Login realizado com sucesso"
        },
        {
            "id": 2,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "action": "create",
            "resource": "transaction",
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.100",
            "details": "Transação criada: R$ 100,00"
        }
    ]
    
    # Filtrar por usuário se especificado
    if user_id:
        audit_entries = [entry for entry in audit_entries if entry["user_id"] == user_id]
    
    # Filtrar por ação se especificado
    if action:
        audit_entries = [entry for entry in audit_entries if entry["action"] == action]
    
    # Aplicar paginação
    paginated_entries = audit_entries[skip:skip + limit]
    
    return {
        "audit_log": paginated_entries,
        "total": len(audit_entries),
        "skip": skip,
        "limit": limit
    }

@router.get("/data-access/{user_id}")
def get_user_data_access(
    user_id: int,
    current_user: User = Depends(require_permission("users", "read")),
    db: Session = Depends(get_db)
):
    """Mostra quais dados um usuário pode acessar"""
    
    target_user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.company_id == current_user.company_id
        )
    ).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    user_permissions = ROLE_PERMISSIONS.get(target_user.role, {})
    
    # Calcular estatísticas de acesso
    accessible_data = {
        "accounts": {
            "can_access": "read" in user_permissions.get("accounts", []),
            "can_modify": "update" in user_permissions.get("accounts", []),
            "count": db.query(Account).filter(Account.company_id == current_user.company_id).count()
        },
        "transactions": {
            "can_access": "read" in user_permissions.get("transactions", []),
            "can_modify": "update" in user_permissions.get("transactions", []),
            "count": db.query(Transaction).filter(Transaction.company_id == current_user.company_id).count()
        },
        "reports": {
            "can_access": "read" in user_permissions.get("reports", []),
            "can_export": "export" in user_permissions.get("reports", [])
        }
    }
    
    return {
        "user": {
            "id": target_user.id,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role.value
        },
        "permissions": user_permissions,
        "accessible_data": accessible_data
    }