import re
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, time
from collections import defaultdict

from sqlalchemy.orm import Session
from models import Transaction, TransactionType, User

class PersonalBusinessSeparator:
    """Serviço para separar automaticamente transações pessoais de empresariais"""
    
    def __init__(self):
        # Palavras-chave que indicam transações empresariais
        self.business_keywords = {
            "fornecedores": [
                "fornecedor", "supplier", "distribuidor", "atacado", "atacadista",
                "industria", "fabrica", "comercial", "ltda", "eireli", "me",
                "cnpj", "nota fiscal", "nf", "fatura", "pedido", "compra empresarial"
            ],
            "servicos_empresariais": [
                "contador", "contabilidade", "advocacia", "juridico", "consultoria",
                "marketing", "publicidade", "design", "desenvolvimento", "ti",
                "manutencao equipamento", "software empresarial", "licenca",
                "hospedagem", "dominio", "servidor", "cloud", "aws", "azure"
            ],
            "impostos_taxas": [
                "simples nacional", "mei", "irpj", "csll", "pis", "cofins",
                "iss", "icms", "receita federal", "fazenda estadual",
                "prefeitura", "alvara", "licenca funcionamento", "bombeiros"
            ],
            "funcionarios": [
                "salario", "folha pagamento", "inss", "fgts", "vale transporte",
                "vale refeicao", "plr", "bonus", "comissao", "funcionario",
                "colaborador", "empregado", "terceirizado", "freelancer"
            ],
            "infraestrutura": [
                "aluguel comercial", "escritorio", "loja", "galpao", "deposito",
                "energia comercial", "agua comercial", "telefone comercial",
                "internet empresarial", "seguranca empresarial", "limpeza comercial"
            ],
            "equipamentos": [
                "computador empresarial", "notebook trabalho", "impressora",
                "scanner", "equipamento", "maquinario", "ferramenta",
                "veiculo comercial", "caminhao", "van", "moto entrega"
            ],
            "vendas_receitas": [
                "venda", "receita", "faturamento", "cliente", "pagamento recebido",
                "transferencia cliente", "deposito cliente", "pix cliente",
                "cartao credito", "cartao debito", "boleto pago"
            ]
        }
        
        # Palavras-chave que indicam transações pessoais
        self.personal_keywords = {
            "alimentacao_pessoal": [
                "mercado pessoal", "supermercado casa", "feira", "padaria casa",
                "restaurante familia", "lanche pessoal", "ifood casa",
                "delivery pessoal", "groceries", "food personal"
            ],
            "saude_familia": [
                "medico familia", "dentista pessoal", "farmacia casa",
                "plano saude familia", "consulta pessoal", "exame pessoal",
                "medicamento familia", "hospital pessoal"
            ],
            "educacao_familia": [
                "escola filho", "faculdade pessoal", "curso pessoal",
                "material escolar", "uniforme escola", "mensalidade escola",
                "livro pessoal", "curso online pessoal"
            ],
            "lazer_familia": [
                "cinema familia", "teatro pessoal", "viagem pessoal",
                "hotel pessoal", "passeio familia", "festa pessoal",
                "presente", "aniversario", "natal", "dia das maes"
            ],
            "casa_pessoal": [
                "aluguel casa", "condominio residencial", "iptu residencial",
                "energia residencial", "agua residencial", "gas residencial",
                "internet casa", "telefone casa", "celular pessoal"
            ],
            "transporte_pessoal": [
                "combustivel pessoal", "uber pessoal", "taxi pessoal",
                "manutencao carro pessoal", "ipva", "seguro carro pessoal",
                "estacionamento pessoal", "pedagio pessoal"
            ]
        }
        
        # Padrões de horário (transações empresariais geralmente em horário comercial)
        self.business_hours = {
            "start": time(8, 0),  # 08:00
            "end": time(18, 0),   # 18:00
            "weekdays_only": True
        }
        
        # Padrões de valor para diferentes tipos
        self.value_patterns = {
            "business": {
                "typical_ranges": [
                    {"min": 1000, "max": 50000, "confidence": 0.7},  # Valores altos
                    {"min": 500, "max": 5000, "confidence": 0.4},    # Valores médios
                ],
                "round_values": True  # Valores redondos são mais comuns em negócios
            },
            "personal": {
                "typical_ranges": [
                    {"min": 5, "max": 500, "confidence": 0.6},      # Gastos pessoais típicos
                    {"min": 500, "max": 2000, "confidence": 0.3},   # Gastos maiores pessoais
                ],
                "irregular_values": True  # Valores irregulares são mais comuns
            }
        }
    
    def classify_transaction(self, description: str, amount: Decimal, 
                           transaction_date: datetime, 
                           transaction_type: TransactionType,
                           user_context: Dict = None) -> Tuple[bool, float, str]:
        """Classifica se uma transação é pessoal (False) ou empresarial (True)
        
        Returns:
            Tuple[bool, float, str]: (is_business, confidence, reason)
        """
        
        if not description:
            return False, 0.1, "Descrição vazia - assumindo pessoal"
        
        description_clean = self._clean_description(description)
        
        # Calcular scores
        business_score = self._calculate_business_score(description_clean, amount, transaction_date, transaction_type)
        personal_score = self._calculate_personal_score(description_clean, amount, transaction_date, transaction_type)
        
        # Aplicar contexto do usuário se disponível
        if user_context:
            business_score *= user_context.get("business_multiplier", 1.0)
            personal_score *= user_context.get("personal_multiplier", 1.0)
        
        # Determinar classificação
        total_score = business_score + personal_score
        
        if total_score == 0:
            return False, 0.1, "Sem indicadores claros - assumindo pessoal"
        
        business_confidence = business_score / total_score
        personal_confidence = personal_score / total_score
        
        if business_confidence > 0.6:
            return True, business_confidence, f"Indicadores empresariais (score: {business_score:.2f})"
        elif personal_confidence > 0.6:
            return False, personal_confidence, f"Indicadores pessoais (score: {personal_score:.2f})"
        else:
            # Em caso de empate, usar heurísticas adicionais
            tie_breaker = self._resolve_tie(description_clean, amount, transaction_date, transaction_type)
            return tie_breaker[0], 0.5, tie_breaker[1]
    
    def _clean_description(self, description: str) -> str:
        """Limpa e normaliza a descrição"""
        clean = description.lower()
        clean = re.sub(r'[^a-záàâãéèêíìîóòôõúùûç\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _calculate_business_score(self, description: str, amount: Decimal, 
                                transaction_date: datetime, 
                                transaction_type: TransactionType) -> float:
        """Calcula score para classificação empresarial"""
        score = 0.0
        
        # Score por palavras-chave
        for category, keywords in self.business_keywords.items():
            keyword_score = self._calculate_keyword_score(description, keywords)
            
            # Pesos diferentes por categoria
            weights = {
                "fornecedores": 1.0,
                "servicos_empresariais": 0.9,
                "impostos_taxas": 1.0,
                "funcionarios": 0.8,
                "infraestrutura": 0.7,
                "equipamentos": 0.6,
                "vendas_receitas": 0.9
            }
            
            score += keyword_score * weights.get(category, 0.5)
        
        # Score por horário (transações em horário comercial)
        time_score = self._calculate_time_score(transaction_date, "business")
        score += time_score * 0.3
        
        # Score por valor
        value_score = self._calculate_value_score(amount, "business")
        score += value_score * 0.4
        
        # Score por tipo de transação
        if transaction_type == TransactionType.INCOME:
            score += 0.5  # Receitas são mais prováveis de serem empresariais
        
        return min(score, 2.0)  # Limitar score máximo
    
    def _calculate_personal_score(self, description: str, amount: Decimal, 
                                transaction_date: datetime, 
                                transaction_type: TransactionType) -> float:
        """Calcula score para classificação pessoal"""
        score = 0.0
        
        # Score por palavras-chave
        for category, keywords in self.personal_keywords.items():
            keyword_score = self._calculate_keyword_score(description, keywords)
            
            # Pesos diferentes por categoria
            weights = {
                "alimentacao_pessoal": 0.8,
                "saude_familia": 0.7,
                "educacao_familia": 0.6,
                "lazer_familia": 0.9,
                "casa_pessoal": 0.8,
                "transporte_pessoal": 0.7
            }
            
            score += keyword_score * weights.get(category, 0.5)
        
        # Score por horário (transações fora do horário comercial)
        time_score = self._calculate_time_score(transaction_date, "personal")
        score += time_score * 0.2
        
        # Score por valor
        value_score = self._calculate_value_score(amount, "personal")
        score += value_score * 0.3
        
        # Score por tipo de transação
        if transaction_type == TransactionType.EXPENSE:
            score += 0.3  # Despesas pequenas são mais prováveis de serem pessoais
        
        return min(score, 2.0)  # Limitar score máximo
    
    def _calculate_keyword_score(self, description: str, keywords: List[str]) -> float:
        """Calcula score baseado em palavras-chave"""
        score = 0.0
        words = description.split()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Busca exata
            if keyword_lower in description:
                score += 0.8
            
            # Busca por palavras individuais
            for word in words:
                if keyword_lower in word or word in keyword_lower:
                    score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_time_score(self, transaction_date: datetime, context: str) -> float:
        """Calcula score baseado no horário da transação"""
        transaction_time = transaction_date.time()
        weekday = transaction_date.weekday()  # 0 = Monday, 6 = Sunday
        
        is_business_hours = (
            self.business_hours["start"] <= transaction_time <= self.business_hours["end"]
            and (not self.business_hours["weekdays_only"] or weekday < 5)
        )
        
        if context == "business":
            return 0.5 if is_business_hours else 0.0
        else:  # personal
            return 0.3 if not is_business_hours else 0.0
    
    def _calculate_value_score(self, amount: Decimal, context: str) -> float:
        """Calcula score baseado no valor da transação"""
        amount_float = float(abs(amount))
        patterns = self.value_patterns[context]
        
        score = 0.0
        
        # Verificar faixas típicas
        for range_pattern in patterns["typical_ranges"]:
            if range_pattern["min"] <= amount_float <= range_pattern["max"]:
                score += range_pattern["confidence"]
        
        # Verificar padrões específicos
        if context == "business":
            # Valores redondos são mais comuns em negócios
            if patterns.get("round_values") and amount_float % 100 == 0:
                score += 0.2
            
            # Valores muito altos são mais prováveis de serem empresariais
            if amount_float > 5000:
                score += 0.4
        
        elif context == "personal":
            # Valores irregulares são mais comuns em gastos pessoais
            if patterns.get("irregular_values") and amount_float % 10 != 0:
                score += 0.1
            
            # Valores muito baixos são mais prováveis de serem pessoais
            if amount_float < 50:
                score += 0.3
        
        return min(score, 1.0)
    
    def _resolve_tie(self, description: str, amount: Decimal, 
                   transaction_date: datetime, 
                   transaction_type: TransactionType) -> Tuple[bool, str]:
        """Resolve empates usando heurísticas adicionais"""
        
        # Heurística 1: Valores muito altos tendem a ser empresariais
        if float(abs(amount)) > 10000:
            return True, "Valor alto - provavelmente empresarial"
        
        # Heurística 2: Finais de semana tendem a ser pessoais
        if transaction_date.weekday() >= 5:  # Sábado ou domingo
            return False, "Final de semana - provavelmente pessoal"
        
        # Heurística 3: Receitas em horário comercial tendem a ser empresariais
        if (transaction_type == TransactionType.INCOME and 
            self.business_hours["start"] <= transaction_date.time() <= self.business_hours["end"]):
            return True, "Receita em horário comercial - provavelmente empresarial"
        
        # Heurística 4: Despesas pequenas tendem a ser pessoais
        if transaction_type == TransactionType.EXPENSE and float(abs(amount)) < 100:
            return False, "Despesa pequena - provavelmente pessoal"
        
        # Padrão: assumir pessoal
        return False, "Sem indicadores claros - assumindo pessoal por padrão"
    
    def batch_classify(self, db: Session, company_id: int, limit: int = 100) -> Dict[str, int]:
        """Classifica transações em lote"""
        
        # Buscar transações sem classificação
        transactions = db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.is_personal.is_(None)
        ).limit(limit).all()
        
        results = {
            "processed": 0,
            "business": 0,
            "personal": 0,
            "low_confidence": 0
        }
        
        for transaction in transactions:
            results["processed"] += 1
            
            try:
                is_business, confidence, reason = self.classify_transaction(
                    transaction.description,
                    transaction.amount,
                    transaction.date,
                    transaction.transaction_type
                )
                
                transaction.is_personal = not is_business
                transaction.ml_confidence = confidence
                
                if is_business:
                    results["business"] += 1
                else:
                    results["personal"] += 1
                
                if confidence < 0.6:
                    results["low_confidence"] += 1
                    
            except Exception as e:
                print(f"Erro ao classificar transação {transaction.id}: {e}")
        
        db.commit()
        return results
    
    def get_classification_suggestions(self, description: str, amount: Decimal, 
                                     transaction_date: datetime, 
                                     transaction_type: TransactionType) -> Dict[str, any]:
        """Retorna sugestões de classificação com detalhes"""
        
        is_business, confidence, reason = self.classify_transaction(
            description, amount, transaction_date, transaction_type
        )
        
        return {
            "classification": "empresarial" if is_business else "pessoal",
            "confidence": round(confidence, 2),
            "confidence_percentage": round(confidence * 100, 1),
            "reason": reason,
            "suggestions": {
                "high_confidence": confidence >= 0.7,
                "review_recommended": confidence < 0.6,
                "alternative_classification": "pessoal" if is_business else "empresarial"
            }
        }
    
    def analyze_classification_patterns(self, db: Session, company_id: int, 
                                      days: int = 30) -> Dict[str, any]:
        """Analisa padrões de classificação para melhorar o modelo"""
        
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.date >= start_date,
            Transaction.is_personal.isnot(None)
        ).all()
        
        business_transactions = [t for t in transactions if not t.is_personal]
        personal_transactions = [t for t in transactions if t.is_personal]
        
        analysis = {
            "total_transactions": len(transactions),
            "business_count": len(business_transactions),
            "personal_count": len(personal_transactions),
            "business_percentage": round(len(business_transactions) / len(transactions) * 100, 1) if transactions else 0,
            "personal_percentage": round(len(personal_transactions) / len(transactions) * 100, 1) if transactions else 0,
            "avg_business_amount": sum(float(t.amount) for t in business_transactions) / len(business_transactions) if business_transactions else 0,
            "avg_personal_amount": sum(float(t.amount) for t in personal_transactions) / len(personal_transactions) if personal_transactions else 0,
            "low_confidence_count": len([t for t in transactions if (t.ml_confidence or 0) < 0.6]),
            "patterns": {
                "business_peak_hours": self._analyze_time_patterns(business_transactions),
                "personal_peak_hours": self._analyze_time_patterns(personal_transactions),
                "common_business_descriptions": self._get_common_descriptions(business_transactions, 5),
                "common_personal_descriptions": self._get_common_descriptions(personal_transactions, 5)
            }
        }
        
        return analysis
    
    def _analyze_time_patterns(self, transactions: List[Transaction]) -> Dict[str, int]:
        """Analisa padrões de horário das transações"""
        hour_counts = defaultdict(int)
        
        for transaction in transactions:
            hour = transaction.date.hour
            hour_counts[hour] += 1
        
        # Retornar os 3 horários mais comuns
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return {f"{hour}h": count for hour, count in sorted_hours}
    
    def _get_common_descriptions(self, transactions: List[Transaction], limit: int) -> List[str]:
        """Retorna as descrições mais comuns"""
        description_counts = defaultdict(int)
        
        for transaction in transactions:
            if transaction.description:
                # Pegar primeiras 3 palavras da descrição
                words = transaction.description.lower().split()[:3]
                key = " ".join(words)
                description_counts[key] += 1
        
        sorted_descriptions = sorted(description_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [desc for desc, count in sorted_descriptions]

# Instância global do serviço
separator_service = PersonalBusinessSeparator()