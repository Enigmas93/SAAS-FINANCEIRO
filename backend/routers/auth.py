from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models import User, Company, Subscription, SubscriptionPlan, SubscriptionStatus, UserRole
from schemas import UserLogin, UserRegister, Token, LoginResponse, User as UserSchema
from auth import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token, 
    get_password_hash,
    verify_token,
    security,
    get_current_active_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=dict)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registra um novo usuário e empresa"""
    
    # Verifica se o email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Cria a empresa
    company = Company(
        name=user_data.company_name,
        cnpj=user_data.company_cnpj
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # Cria o usuário admin da empresa
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=UserRole.ADMIN,
        company_id=company.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Cria assinatura trial de 14 dias
    trial_end = datetime.utcnow() + timedelta(days=14)
    subscription = Subscription(
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.TRIALING,
        trial_end=trial_end,
        company_id=company.id
    )
    db.add(subscription)
    db.commit()
    
    return {
        "message": "User and company created successfully",
        "user_id": user.id,
        "company_id": company.id,
        "trial_end": trial_end
    }

@router.post("/login", response_model=LoginResponse)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Autentica usuário e retorna tokens JWT"""
    
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Cria tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=Token)
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Renova o token de acesso usando o refresh token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verifica o refresh token
    token_data = verify_token(credentials.credentials, token_type="refresh")
    if token_data is None:
        raise credentials_exception
    
    # Busca o usuário
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Cria novos tokens
    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Retorna informações do usuário atual"""
    return current_user

@router.post("/logout")
def logout():
    """Logout do usuário (cliente deve descartar os tokens)"""
    return {"message": "Successfully logged out"}