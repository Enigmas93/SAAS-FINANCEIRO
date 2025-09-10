from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import io
import re
from decimal import Decimal

from database import get_db
from models import (
    BankConnection, Transaction, Account, User, TransactionType,
    BankConnectionStatus, TransactionCategory
)
from schemas_advanced import (
    BankConnection as BankConnectionSchema,
    BankConnectionCreate, BankConnectionUpdate,
    BankImportResult, AutoCategorizationResult
)
from auth import get_current_active_user
from services.ml_categorization import ml_service
from services.personal_business_separator import separator_service

router = APIRouter(prefix="/bank-import", tags=["bank-import"])

# Configurações de bancos suportados
BANK_CONFIGS = {
    "nubank": {
        "date_column": "date",
        "description_column": "description",
        "amount_column": "amount",
        "date_format": "%Y-%m-%d"
    },
    "itau": {
        "date_column": "Data",
        "description_column": "Descrição",
        "amount_column": "Valor",
        "date_format": "%d/%m/%Y"
    },
    "bradesco": {
        "date_column": "Data",
        "description_column": "Histórico",
        "amount_column": "Valor",
        "date_format": "%d/%m/%Y"
    },
    "santander": {
        "date_column": "Data",
        "description_column": "Descrição",
        "amount_column": "Valor",
        "date_format": "%d/%m/%Y"
    }
}

# Palavras-chave para categorização automática
CATEGORY_KEYWORDS = {
    "Alimentação": ["mercado", "supermercado", "padaria", "restaurante", "lanchonete", "ifood", "uber eats", "rappi"],
    "Transporte": ["uber", "99", "posto", "combustivel", "gasolina", "metro", "onibus", "taxi"],
    "Saúde": ["farmacia", "hospital", "clinica", "medico", "dentista", "laboratorio"],
    "Educação": ["escola", "faculdade", "curso", "livro", "material escolar"],
    "Lazer": ["cinema", "teatro", "show", "netflix", "spotify", "amazon prime", "disney"],
    "Casa": ["aluguel", "condominio", "luz", "agua", "gas", "internet", "telefone"],
    "Vestuário": ["roupa", "sapato", "calcado", "loja", "shopping"],
    "Tecnologia": ["celular", "computador", "notebook", "software", "app"],
    "Investimentos": ["aplicacao", "investimento", "poupanca", "cdb", "tesouro"]
}

@router.get("/connections", response_model=List[BankConnectionSchema])
def get_bank_connections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista todas as conexões bancárias do usuário"""
    connections = db.query(BankConnection).filter(
        BankConnection.company_id == current_user.company_id
    ).all()
    return connections

@router.post("/connections", response_model=BankConnectionSchema)
def create_bank_connection(
    connection: BankConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova conexão bancária"""
    
    # Verificar se a conta existe
    if connection.account_id:
        account = db.query(Account).filter(
            and_(
                Account.id == connection.account_id,
                Account.company_id == current_user.company_id
            )
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada"
            )
    
    db_connection = BankConnection(
        **connection.dict(),
        company_id=current_user.company_id,
        status=BankConnectionStatus.PENDING
    )
    
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    
    return db_connection

@router.put("/connections/{connection_id}", response_model=BankConnectionSchema)
def update_bank_connection(
    connection_id: int,
    connection_update: BankConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma conexão bancária"""
    
    db_connection = db.query(BankConnection).filter(
        and_(
            BankConnection.id == connection_id,
            BankConnection.company_id == current_user.company_id
        )
    ).first()
    
    if not db_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conexão bancária não encontrada"
        )
    
    update_data = connection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_connection, field, value)
    
    db.commit()
    db.refresh(db_connection)
    
    return db_connection

@router.delete("/connections/{connection_id}")
def delete_bank_connection(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove uma conexão bancária"""
    
    db_connection = db.query(BankConnection).filter(
        and_(
            BankConnection.id == connection_id,
            BankConnection.company_id == current_user.company_id
        )
    ).first()
    
    if not db_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conexão bancária não encontrada"
        )
    
    db.delete(db_connection)
    db.commit()
    
    return {"message": "Conexão bancária removida com sucesso"}

@router.post("/upload-extract/{bank_name}", response_model=BankImportResult)
async def upload_bank_extract(
    bank_name: str,
    account_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Faz upload e processa extrato bancário"""
    
    if bank_name.lower() not in BANK_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Banco {bank_name} não suportado"
        )
    
    # Verificar se a conta existe
    account = db.query(Account).filter(
        and_(
            Account.id == account_id,
            Account.company_id == current_user.company_id
        )
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada"
        )
    
    try:
        # Ler arquivo CSV
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Processar transações
        result = await process_bank_extract(df, bank_name, account_id, current_user, db)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

async def process_bank_extract(
    df: pd.DataFrame,
    bank_name: str,
    account_id: int,
    current_user: User,
    db: Session
) -> BankImportResult:
    """Processa o extrato bancário e cria transações"""
    
    config = BANK_CONFIGS[bank_name.lower()]
    transactions_imported = 0
    transactions_duplicated = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # Extrair dados da linha
            date_str = str(row[config["date_column"]])
            description = str(row[config["description_column"]])
            amount_str = str(row[config["amount_column"]])
            
            # Converter data
            transaction_date = datetime.strptime(date_str, config["date_format"])
            
            # Converter valor
            amount = Decimal(amount_str.replace(',', '.').replace('R$', '').strip())
            
            # Determinar tipo de transação
            transaction_type = TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
            amount = abs(amount)
            
            # Verificar se transação já existe (evitar duplicatas)
            existing = db.query(Transaction).filter(
                and_(
                    Transaction.company_id == current_user.company_id,
                    Transaction.transaction_date == transaction_date,
                    Transaction.amount == amount,
                    Transaction.description.ilike(f"%{description[:50]}%")
                )
            ).first()
            
            if existing:
                transactions_duplicated += 1
                continue
            
            # Categorização automática
            category, confidence = auto_categorize_transaction(description)
            
            # Criar transação
            transaction = Transaction(
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                transaction_date=transaction_date,
                category=category,
                ml_confidence=confidence,
                from_account_id=account_id if transaction_type == TransactionType.EXPENSE else None,
                to_account_id=account_id if transaction_type == TransactionType.INCOME else None,
                company_id=current_user.company_id,
                user_id=current_user.id
            )
            
            db.add(transaction)
            transactions_imported += 1
            
        except Exception as e:
            errors.append(f"Linha {index + 1}: {str(e)}")
    
    db.commit()
    
    return BankImportResult(
        success=len(errors) == 0,
        transactions_imported=transactions_imported,
        transactions_duplicated=transactions_duplicated,
        errors=errors,
        last_import_date=datetime.now()
    )

def auto_categorize_transaction(description: str) -> tuple[str, float]:
    """Categoriza automaticamente uma transação baseada na descrição"""
    
    description_lower = description.lower()
    best_category = "Outros"
    best_confidence = 0.0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = 0
        for keyword in keywords:
            if keyword in description_lower:
                matches += 1
        
        if matches > 0:
            confidence = min(matches / len(keywords), 1.0)
            if confidence > best_confidence:
                best_category = category
                best_confidence = confidence
    
    return best_category, best_confidence

@router.post("/categorize/{transaction_id}", response_model=AutoCategorizationResult)
def auto_categorize_single_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Categoriza automaticamente uma transação específica"""
    
    transaction = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.company_id == current_user.company_id
        )
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    
    category, confidence = auto_categorize_transaction(transaction.description)
    
    # Atualizar transação
    transaction.category = category
    transaction.ml_confidence = confidence
    db.commit()
    
    # Encontrar palavras-chave que fizeram match
    keywords_matched = []
    description_lower = transaction.description.lower()
    
    if category in CATEGORY_KEYWORDS:
        for keyword in CATEGORY_KEYWORDS[category]:
            if keyword in description_lower:
                keywords_matched.append(keyword)
    
    return AutoCategorizationResult(
        transaction_id=transaction_id,
        suggested_category=category,
        confidence=confidence,
        keywords_matched=keywords_matched
    )

@router.post("/categorize-all")
def auto_categorize_all_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Categoriza automaticamente todas as transações sem categoria"""
    
    transactions = db.query(Transaction).filter(
        and_(
            Transaction.company_id == current_user.company_id,
            Transaction.category.is_(None)
        )
    ).all()
    
    categorized_count = 0
    
    for transaction in transactions:
        category, confidence = auto_categorize_transaction(transaction.description)
        
        if confidence > 0.3:  # Só aplicar se confiança > 30%
            transaction.category = category
            transaction.ml_confidence = confidence
            categorized_count += 1
    
    db.commit()
    
    return {
        "message": f"{categorized_count} transações categorizadas automaticamente",
        "total_processed": len(transactions),
        "categorized": categorized_count
    }

@router.post("/categorize-automatic")
async def categorize_transactions_automatic(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Categoriza automaticamente transações usando IA/ML"""
    
    try:
        # Usar o serviço de ML para categorização
        results = ml_service.batch_categorize(db, current_user.company_id, limit)
        
        return {
            "message": f"{results['categorized']} transações categorizadas automaticamente",
            "results": results,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na categorização automática: {str(e)}")

@router.post("/classify-personal-business")
async def classify_personal_business(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Classifica transações como pessoais ou empresariais automaticamente"""
    
    try:
        # Usar o serviço de separação para classificação
        results = separator_service.batch_classify(db, current_user.company_id, limit)
        
        return {
            "message": f"{results['processed']} transações classificadas",
            "results": results,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")

@router.get("/classification-analysis")
async def get_classification_analysis(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Análise de padrões de classificação pessoal vs empresarial"""
    
    try:
        analysis = separator_service.analyze_classification_patterns(
            db, current_user.company_id, days
        )
        
        return {
            "analysis": analysis,
            "period_days": days,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@router.get("/ml-insights")
async def get_ml_insights(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Insights de padrões de gastos usando ML"""
    
    try:
        # Análise de padrões de categorização
        spending_patterns = ml_service.analyze_spending_patterns(
            db, current_user.company_id, days
        )
        
        # Análise de classificação pessoal/empresarial
        classification_patterns = separator_service.analyze_classification_patterns(
            db, current_user.company_id, days
        )
        
        return {
            "spending_patterns": spending_patterns,
            "classification_patterns": classification_patterns,
            "period_days": days,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights: {str(e)}")

@router.get("/supported-banks")
def get_supported_banks():
    """Lista bancos suportados para importação"""
    return {
        "banks": list(BANK_CONFIGS.keys()),
        "formats": {
            bank: {
                "required_columns": [config["date_column"], config["description_column"], config["amount_column"]],
                "date_format": config["date_format"]
            }
            for bank, config in BANK_CONFIGS.items()
        }
    }