from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

class AccountType(enum.Enum):
    CASH = "cash"
    BANK = "bank"
    CREDIT_CARD = "credit_card"

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"

class BankConnectionStatus(enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"

class DebtType(enum.Enum):
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    FINANCING = "financing"
    INSTALLMENT = "installment"
    OTHER = "other"

class DebtStatus(enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"

class GoalStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELED = "canceled"

class AlertType(enum.Enum):
    DEBT_DUE = "debt_due"
    GOAL_PROGRESS = "goal_progress"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNUSUAL_SPENDING = "unusual_spending"
    LOW_BALANCE = "low_balance"

class AchievementType(enum.Enum):
    SAVINGS_MILESTONE = "savings_milestone"
    DEBT_PAYMENT = "debt_payment"
    GOAL_COMPLETED = "goal_completed"
    STREAK_TRACKING = "streak_tracking"
    BUDGET_ADHERENCE = "budget_adherence"

class SubscriptionPlan(enum.Enum):
    FREE = "free"
    PRO_MONTHLY = "pro_monthly"
    PRO_YEARLY = "pro_yearly"
    BUSINESS_MONTHLY = "business_monthly"

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="company")
    accounts = relationship("Account", back_populates="company")
    transactions = relationship("Transaction", back_populates="company")
    invoices = relationship("Invoice", back_populates="company")
    subscription = relationship("Subscription", back_populates="company", uselist=False)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="users")
    transactions = relationship("Transaction", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Numeric(15, 2), default=0.00)
    bank_name = Column(String(255), nullable=True)
    account_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(100), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    category = Column(String(100), nullable=True)  # categoria antiga (texto)
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=True)  # nova categoria
    is_personal = Column(Boolean, nullable=True)  # separação pessoal/empresarial
    ml_confidence = Column(Numeric(3, 2), nullable=True)  # confiança da categorização automática
    is_recurring = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
    transaction_category = relationship("TransactionCategory")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=True)
    client_document = Column(String(20), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    is_paid = Column(Boolean, default=False)
    pdf_path = Column(String(500), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="invoices")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)
    pagbrasil_payment_id = Column(String(255), unique=True, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    payment_method = Column(String(50), nullable=False)  # card, pix
    status = Column(String(50), nullable=False)  # pending, succeeded, failed
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription")

# Novos modelos para funcionalidades avançadas

class BankConnection(Base):
    __tablename__ = "bank_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(100), nullable=False)
    bank_code = Column(String(10), nullable=True)
    account_number = Column(String(50), nullable=True)
    agency = Column(String(10), nullable=True)
    connection_token = Column(Text, nullable=True)  # Token criptografado
    status = Column(Enum(BankConnectionStatus), default=BankConnectionStatus.PENDING)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(Integer, default=24)  # horas
    auto_import = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    account = relationship("Account")

class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # hex color
    parent_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=True)
    is_system = Column(Boolean, default=False)  # categorias do sistema vs personalizadas
    ml_keywords = Column(JSON, nullable=True)  # palavras-chave para ML
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parent = relationship("TransactionCategory", remote_side=[id])
    company = relationship("Company")

class Debt(Base):
    __tablename__ = "debts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    debt_type = Column(Enum(DebtType), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 4), nullable=True)  # taxa de juros mensal
    installments_total = Column(Integer, nullable=True)
    installments_paid = Column(Integer, default=0)
    installment_amount = Column(Numeric(15, 2), nullable=True)
    due_day = Column(Integer, nullable=True)  # dia do vencimento
    next_due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DebtStatus), default=DebtStatus.ACTIVE)
    creditor = Column(String(200), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")

class FinancialGoal(Base):
    __tablename__ = "financial_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0)
    target_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    category = Column(String(100), nullable=True)  # viagem, emergência, etc
    auto_transfer = Column(Boolean, default=False)
    monthly_target = Column(Numeric(15, 2), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  # conta destino
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")
    account = relationship("Account")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    is_read = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 1=baixa, 2=média, 3=alta
    alert_metadata = Column(JSON, nullable=True)  # dados específicos do alerta
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    achievement_type = Column(Enum(AchievementType), nullable=False)
    icon = Column(String(50), nullable=True)
    points = Column(Integer, default=0)
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    progress_current = Column(Integer, default=0)
    progress_target = Column(Integer, nullable=False)
    achievement_metadata = Column(JSON, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    amount_limit = Column(Numeric(15, 2), nullable=False)
    amount_spent = Column(Numeric(15, 2), default=0)
    period_type = Column(String(20), default="monthly")  # monthly, weekly, yearly
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    alert_threshold = Column(Integer, default=80)  # % para alertar
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")