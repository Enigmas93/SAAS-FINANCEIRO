from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import UserRole, AccountType, TransactionType, SubscriptionStatus, SubscriptionPlan

# Base schemas
class CompanyBase(BaseModel):
    name: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    company_id: Optional[int] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Account schemas
class AccountBase(BaseModel):
    name: str
    account_type: AccountType
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    is_active: bool = True

class AccountCreate(AccountBase):
    balance: Decimal = Decimal('0.00')

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    is_active: Optional[bool] = None

class Account(AccountBase):
    id: int
    balance: Decimal
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: Optional[str] = None
    transaction_date: datetime
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    
    @validator('from_account_id', 'to_account_id')
    def validate_accounts(cls, v, values):
        transaction_type = values.get('transaction_type')
        if transaction_type == TransactionType.TRANSFER:
            if not values.get('from_account_id') or not values.get('to_account_id'):
                raise ValueError('Transfer transactions require both from_account_id and to_account_id')
        return v

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None

class Transaction(TransactionBase):
    id: int
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    company_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Invoice schemas
class InvoiceBase(BaseModel):
    client_name: str
    client_email: Optional[str] = None
    client_document: Optional[str] = None
    amount: Decimal
    description: Optional[str] = None
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_document: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_paid: Optional[bool] = None
    paid_date: Optional[datetime] = None

class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    is_paid: bool
    paid_date: Optional[datetime] = None
    pdf_path: Optional[str] = None
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan
    status: SubscriptionStatus = SubscriptionStatus.TRIALING

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = None
    status: Optional[SubscriptionStatus] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None

class Subscription(SubscriptionBase):
    id: int
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: 'User'

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str
    company_cnpj: Optional[str] = None

# Dashboard schemas
class DashboardData(BaseModel):
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    pending_invoices: int
    recent_transactions: List[Transaction]
    
class FinancialReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_income: Decimal
    total_expenses: Decimal
    net_result: Decimal
    transactions_by_category: dict
    cash_flow: List[dict]