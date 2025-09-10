"""Migração para adicionar funcionalidades avançadas do SaaS Financeiro

Esta migração adiciona:
- Novos campos na tabela Transaction (category_id, is_personal, ml_confidence, is_recurring)
- Novas tabelas: BankConnection, TransactionCategory, Debt, FinancialGoal, Alert, Achievement, Budget
- Novos enums para status e tipos
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers
revision = 'add_advanced_features'
down_revision = None  # Substitua pelo ID da migração anterior
branch_labels = None
depends_on = None

def upgrade():
    # Criar novos enums
    bank_connection_status = postgresql.ENUM(
        'CONNECTED', 'DISCONNECTED', 'ERROR', 'PENDING',
        name='bankconnectionstatus'
    )
    bank_connection_status.create(op.get_bind())
    
    debt_type = postgresql.ENUM(
        'CREDIT_CARD', 'LOAN', 'FINANCING', 'INSTALLMENT', 'OTHER',
        name='debttype'
    )
    debt_type.create(op.get_bind())
    
    debt_status = postgresql.ENUM(
        'ACTIVE', 'PAID', 'OVERDUE', 'CANCELLED',
        name='debtstatus'
    )
    debt_status.create(op.get_bind())
    
    goal_status = postgresql.ENUM(
        'ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED',
        name='goalstatus'
    )
    goal_status.create(op.get_bind())
    
    alert_type = postgresql.ENUM(
        'DEBT_REMINDER', 'GOAL_PROGRESS', 'BUDGET_EXCEEDED', 
        'UNUSUAL_SPENDING', 'ACHIEVEMENT', 'SYSTEM',
        name='alerttype'
    )
    alert_type.create(op.get_bind())
    
    achievement_type = postgresql.ENUM(
        'SAVINGS', 'SPENDING', 'GOAL', 'STREAK', 'MILESTONE',
        name='achievementtype'
    )
    achievement_type.create(op.get_bind())
    
    # Criar tabela TransactionCategory
    op.create_table(
        'transaction_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transaction_categories_company_id', 'transaction_categories', ['company_id'])
    op.create_index('ix_transaction_categories_name', 'transaction_categories', ['name'])
    
    # Criar tabela BankConnection
    op.create_table(
        'bank_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=False),
        sa.Column('bank_code', sa.String(10), nullable=True),
        sa.Column('account_number', sa.String(50), nullable=True),
        sa.Column('agency', sa.String(20), nullable=True),
        sa.Column('account_type', sa.String(20), nullable=True),
        sa.Column('status', bank_connection_status, nullable=False),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('sync_frequency', sa.Integer(), default=24, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('api_credentials', sa.JSON(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_connections_company_id', 'bank_connections', ['company_id'])
    op.create_index('ix_bank_connections_status', 'bank_connections', ['status'])
    
    # Criar tabela Debt
    op.create_table(
        'debts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('debt_type', debt_type, nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('installments_total', sa.Integer(), nullable=True),
        sa.Column('installments_paid', sa.Integer(), default=0, nullable=False),
        sa.Column('installment_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('next_payment_date', sa.Date(), nullable=True),
        sa.Column('status', debt_status, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_debts_company_id', 'debts', ['company_id'])
    op.create_index('ix_debts_status', 'debts', ['status'])
    op.create_index('ix_debts_due_date', 'debts', ['due_date'])
    
    # Criar tabela FinancialGoal
    op.create_table(
        'financial_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('current_amount', sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('monthly_contribution', sa.Numeric(15, 2), nullable=True),
        sa.Column('auto_transfer', sa.Boolean(), default=False, nullable=False),
        sa.Column('status', goal_status, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_financial_goals_company_id', 'financial_goals', ['company_id'])
    op.create_index('ix_financial_goals_status', 'financial_goals', ['status'])
    
    # Criar tabela Alert
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('alert_type', alert_type, nullable=False),
        sa.Column('priority', sa.String(10), default='medium', nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_company_id', 'alerts', ['company_id'])
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('ix_alerts_is_read', 'alerts', ['is_read'])
    
    # Criar tabela Achievement
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('achievement_type', achievement_type, nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('points', sa.Integer(), default=0, nullable=False),
        sa.Column('criteria', sa.JSON(), nullable=True),
        sa.Column('is_unlocked', sa.Boolean(), default=False, nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_achievements_company_id', 'achievements', ['company_id'])
    op.create_index('ix_achievements_user_id', 'achievements', ['user_id'])
    op.create_index('ix_achievements_type', 'achievements', ['achievement_type'])
    
    # Criar tabela Budget
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('amount_limit', sa.Numeric(15, 2), nullable=False),
        sa.Column('amount_spent', sa.Numeric(15, 2), default=0, nullable=False),
        sa.Column('period_type', sa.String(20), default='monthly', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('alert_threshold', sa.Numeric(5, 2), default=80, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_budgets_company_id', 'budgets', ['company_id'])
    op.create_index('ix_budgets_category', 'budgets', ['category'])
    
    # Adicionar novos campos à tabela transactions
    op.add_column('transactions', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column('is_personal', sa.Boolean(), nullable=True))
    op.add_column('transactions', sa.Column('ml_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('transactions', sa.Column('is_recurring', sa.Boolean(), default=False, nullable=False))
    
    # Criar foreign key para category_id
    op.create_foreign_key(
        'fk_transactions_category_id',
        'transactions', 'transaction_categories',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Criar índices para os novos campos
    op.create_index('ix_transactions_category_id', 'transactions', ['category_id'])
    op.create_index('ix_transactions_is_personal', 'transactions', ['is_personal'])
    op.create_index('ix_transactions_is_recurring', 'transactions', ['is_recurring'])
    
    # Inserir categorias padrão
    op.execute(
        text("""
        INSERT INTO transaction_categories (name, description, color, icon, is_default, company_id, created_at, updated_at)
        SELECT 
            category_name,
            category_description,
            category_color,
            category_icon,
            true,
            c.id,
            now(),
            now()
        FROM companies c
        CROSS JOIN (
            VALUES 
                ('Alimentação', 'Gastos com comida e bebida', '#FF6B6B', 'utensils'),
                ('Transporte', 'Gastos com locomoção', '#4ECDC4', 'car'),
                ('Saúde', 'Gastos médicos e farmácia', '#45B7D1', 'heart'),
                ('Educação', 'Gastos com ensino e cursos', '#96CEB4', 'graduation-cap'),
                ('Lazer', 'Entretenimento e diversão', '#FFEAA7', 'gamepad'),
                ('Casa', 'Gastos domésticos', '#DDA0DD', 'home'),
                ('Vestuário', 'Roupas e acessórios', '#98D8C8', 'tshirt'),
                ('Tecnologia', 'Eletrônicos e software', '#6C5CE7', 'laptop'),
                ('Investimentos', 'Aplicações financeiras', '#00B894', 'chart-line'),
                ('Impostos', 'Tributos e taxas', '#E17055', 'file-invoice'),
                ('Serviços', 'Prestação de serviços', '#74B9FF', 'tools'),
                ('Outros', 'Gastos diversos', '#A29BFE', 'ellipsis-h')
        ) AS default_categories(category_name, category_description, category_color, category_icon)
        """)
    )

def downgrade():
    # Remover foreign key
    op.drop_constraint('fk_transactions_category_id', 'transactions', type_='foreignkey')
    
    # Remover índices
    op.drop_index('ix_transactions_is_recurring', 'transactions')
    op.drop_index('ix_transactions_is_personal', 'transactions')
    op.drop_index('ix_transactions_category_id', 'transactions')
    
    # Remover colunas adicionadas
    op.drop_column('transactions', 'is_recurring')
    op.drop_column('transactions', 'ml_confidence')
    op.drop_column('transactions', 'is_personal')
    op.drop_column('transactions', 'category_id')
    
    # Remover tabelas
    op.drop_table('budgets')
    op.drop_table('achievements')
    op.drop_table('alerts')
    op.drop_table('financial_goals')
    op.drop_table('debts')
    op.drop_table('bank_connections')
    op.drop_table('transaction_categories')
    
    # Remover enums
    achievement_type = postgresql.ENUM(name='achievementtype')
    achievement_type.drop(op.get_bind())
    
    alert_type = postgresql.ENUM(name='alerttype')
    alert_type.drop(op.get_bind())
    
    goal_status = postgresql.ENUM(name='goalstatus')
    goal_status.drop(op.get_bind())
    
    debt_status = postgresql.ENUM(name='debtstatus')
    debt_status.drop(op.get_bind())
    
    debt_type = postgresql.ENUM(name='debttype')
    debt_type.drop(op.get_bind())
    
    bank_connection_status = postgresql.ENUM(name='bankconnectionstatus')
    bank_connection_status.drop(op.get_bind())