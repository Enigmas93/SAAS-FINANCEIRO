from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

# Enums para schemas
class BankConnectionStatusSchema(str, Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"

class DebtTypeSchema(str, Enum):
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    FINANCING = "financing"
    INSTALLMENT = "installment"
    OTHER = "other"

class DebtStatusSchema(str, Enum):
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"

class GoalStatusSchema(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELED = "canceled"

class AlertTypeSchema(str, Enum):
    DEBT_DUE = "debt_due"
    GOAL_PROGRESS = "goal_progress"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNUSUAL_SPENDING = "unusual_spending"
    LOW_BALANCE = "low_balance"

class AchievementTypeSchema(str, Enum):
    SAVINGS_MILESTONE = "savings_milestone"
    DEBT_PAYMENT = "debt_payment"
    GOAL_COMPLETED = "goal_completed"
    STREAK_TRACKING = "streak_tracking"
    BUDGET_ADHERENCE = "budget_adherence"

# Schemas para BankConnection
class BankConnectionBase(BaseModel):
    bank_name: str = Field(..., max_length=100)
    bank_code: Optional[str] = Field(None, max_length=10)
    account_number: Optional[str] = Field(None, max_length=50)
    agency: Optional[str] = Field(None, max_length=10)
    sync_frequency: int = Field(24, ge=1, le=168)  # 1 hora a 1 semana
    auto_import: bool = True
    account_id: Optional[int] = None

class BankConnectionCreate(BankConnectionBase):
    connection_token: Optional[str] = None

class BankConnectionUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=100)
    sync_frequency: Optional[int] = Field(None, ge=1, le=168)
    auto_import: Optional[bool] = None
    account_id: Optional[int] = None

class BankConnection(BankConnectionBase):
    id: int
    status: BankConnectionStatusSchema
    last_sync: Optional[datetime]
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas para TransactionCategory
class TransactionCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    parent_id: Optional[int] = None
    ml_keywords: Optional[List[str]] = None

class TransactionCategoryCreate(TransactionCategoryBase):
    pass

class TransactionCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    parent_id: Optional[int] = None
    ml_keywords: Optional[List[str]] = None

class TransactionCategory(TransactionCategoryBase):
    id: int
    is_system: bool
    company_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Debt
class DebtBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    debt_type: DebtTypeSchema
    total_amount: Decimal = Field(..., gt=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    installments_total: Optional[int] = Field(None, gt=0)
    installment_amount: Optional[Decimal] = Field(None, gt=0)
    due_day: Optional[int] = Field(None, ge=1, le=31)
    creditor: Optional[str] = Field(None, max_length=200)

class DebtCreate(DebtBase):
    pass

class DebtUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    remaining_amount: Optional[Decimal] = Field(None, ge=0)
    installments_paid: Optional[int] = Field(None, ge=0)
    next_due_date: Optional[datetime] = None
    status: Optional[DebtStatusSchema] = None

class Debt(DebtBase):
    id: int
    remaining_amount: Decimal
    installments_paid: int
    next_due_date: Optional[datetime]
    status: DebtStatusSchema
    company_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas para FinancialGoal
class FinancialGoalBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    target_amount: Decimal = Field(..., gt=0)
    target_date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)
    auto_transfer: bool = False
    monthly_target: Optional[Decimal] = Field(None, gt=0)
    account_id: Optional[int] = None

class FinancialGoalCreate(FinancialGoalBase):
    pass

class FinancialGoalUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_amount: Optional[Decimal] = Field(None, gt=0)
    current_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[datetime] = None
    status: Optional[GoalStatusSchema] = None
    monthly_target: Optional[Decimal] = Field(None, gt=0)

class FinancialGoal(FinancialGoalBase):
    id: int
    current_amount: Decimal
    status: GoalStatusSchema
    company_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas para Alert
class AlertBase(BaseModel):
    title: str = Field(..., max_length=200)
    message: str
    alert_type: AlertTypeSchema
    priority: int = Field(1, ge=1, le=3)
    alert_metadata: Optional[Dict[str, Any]] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_active: Optional[bool] = None

class Alert(AlertBase):
    id: int
    is_read: bool
    is_active: bool
    company_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Achievement
class AchievementBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: str
    achievement_type: AchievementTypeSchema
    icon: Optional[str] = Field(None, max_length=50)
    points: int = Field(0, ge=0)
    progress_target: int = Field(..., gt=0)
    achievement_metadata: Optional[Dict[str, Any]] = None

class AchievementCreate(AchievementBase):
    pass

class AchievementUpdate(BaseModel):
    progress_current: Optional[int] = Field(None, ge=0)
    is_unlocked: Optional[bool] = None
    unlocked_at: Optional[datetime] = None

class Achievement(AchievementBase):
    id: int
    is_unlocked: bool
    unlocked_at: Optional[datetime]
    progress_current: int
    company_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Budget
class BudgetBase(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=100)
    amount_limit: Decimal = Field(..., gt=0)
    period_type: str = Field("monthly", pattern=r'^(monthly|weekly|yearly)$')
    start_date: datetime
    end_date: datetime
    alert_threshold: int = Field(80, ge=0, le=100)

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    amount_limit: Optional[Decimal] = Field(None, gt=0)
    amount_spent: Optional[Decimal] = Field(None, ge=0)
    alert_threshold: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

class Budget(BudgetBase):
    id: int
    amount_spent: Decimal
    is_active: bool
    company_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas para relatórios e dashboards
class DashboardStats(BaseModel):
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    pending_debts: int
    active_goals: int
    unread_alerts: int
    achievement_points: int

class CategorySpending(BaseModel):
    category: str
    amount: Decimal
    percentage: float
    color: Optional[str] = None

class MonthlyTrend(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    balance: Decimal

class FinancialReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    category_breakdown: List[CategorySpending]
    monthly_trends: List[MonthlyTrend]
    top_expenses: List[Dict[str, Any]]
    savings_rate: float

# Schema para importação bancária
class BankImportResult(BaseModel):
    success: bool
    transactions_imported: int
    transactions_duplicated: int
    errors: List[str]
    last_import_date: datetime

# Schema para categorização automática
class AutoCategorizationResult(BaseModel):
    transaction_id: int
    suggested_category: str
    confidence: float
    keywords_matched: List[str]