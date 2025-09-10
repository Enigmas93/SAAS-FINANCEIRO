import re
import json
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session
from models import Transaction, TransactionCategory, TransactionType

class MLCategorizationService:
    """Serviço de categorização automática de transações usando regras e padrões"""
    
    def __init__(self):
        # Palavras-chave para categorização automática
        self.category_keywords = {
            "Alimentação": [
                "mercado", "supermercado", "padaria", "açougue", "hortifruti",
                "restaurante", "lanchonete", "pizzaria", "hamburgueria", "delivery",
                "ifood", "uber eats", "rappi", "mcdonalds", "burger king",
                "subway", "kfc", "pizza hut", "dominos", "outback",
                "pao de acucar", "carrefour", "extra", "walmart", "atacadao"
            ],
            "Transporte": [
                "uber", "99", "taxi", "combustivel", "gasolina", "etanol",
                "posto", "shell", "petrobras", "ipiranga", "ale",
                "estacionamento", "pedagio", "onibus", "metro", "trem",
                "bilhete unico", "cartao transporte", "veiculo", "carro",
                "moto", "manutencao", "oficina", "pneu", "oleo"
            ],
            "Saúde": [
                "farmacia", "drogaria", "hospital", "clinica", "medico",
                "dentista", "laboratorio", "exame", "consulta", "medicamento",
                "droga raia", "drogasil", "pacheco", "ultrafarma",
                "unimed", "amil", "bradesco saude", "sulamerica",
                "plano de saude", "convenio medico"
            ],
            "Educação": [
                "escola", "faculdade", "universidade", "curso", "aula",
                "mensalidade", "material escolar", "livro", "apostila",
                "udemy", "coursera", "alura", "rocketseat", "dio",
                "ingles", "idioma", "wizard", "ccaa", "cultura inglesa"
            ],
            "Lazer": [
                "cinema", "teatro", "show", "evento", "festa", "bar",
                "balada", "clube", "academia", "ginasio", "smartfit",
                "netflix", "spotify", "amazon prime", "disney plus",
                "youtube premium", "steam", "playstation", "xbox",
                "ingresso", "ticket", "viagem", "hotel", "pousada"
            ],
            "Casa": [
                "aluguel", "condominio", "iptu", "energia", "luz",
                "agua", "gas", "internet", "telefone", "celular",
                "limpeza", "detergente", "sabao", "amaciante",
                "moveis", "eletrodomesticos", "decoracao", "reforma",
                "construcao", "material construcao", "tinta", "cimento"
            ],
            "Vestuário": [
                "roupa", "sapato", "tenis", "sandalia", "camisa",
                "calca", "vestido", "saia", "blusa", "jaqueta",
                "nike", "adidas", "zara", "hm", "renner", "cea",
                "riachuelo", "marisa", "lojas americanas", "magazine luiza"
            ],
            "Tecnologia": [
                "celular", "smartphone", "computador", "notebook", "tablet",
                "software", "aplicativo", "app", "sistema", "programa",
                "microsoft", "google", "apple", "samsung", "xiaomi",
                "iphone", "android", "windows", "office", "adobe"
            ],
            "Investimentos": [
                "investimento", "aplicacao", "poupanca", "cdb", "lci",
                "lca", "tesouro", "acao", "fundo", "renda fixa",
                "corretora", "xp", "rico", "clear", "inter", "nubank",
                "btg", "itau", "bradesco", "santander", "banco do brasil"
            ],
            "Impostos": [
                "imposto", "taxa", "tributo", "irpf", "ipva", "iptu",
                "iss", "icms", "pis", "cofins", "csll", "irpj",
                "receita federal", "fazenda", "prefeitura", "detran"
            ],
            "Serviços": [
                "servico", "manutencao", "reparo", "conserto", "limpeza",
                "jardinagem", "pintura", "eletricista", "encanador",
                "marceneiro", "pedreiro", "domestica", "diarista",
                "seguranca", "alarme", "monitoramento", "seguro"
            ]
        }
        
        # Padrões de valores para diferentes categorias
        self.value_patterns = {
            "Alimentação": {"min": 5, "max": 500, "typical": [10, 50, 100]},
            "Transporte": {"min": 3, "max": 200, "typical": [8, 15, 30]},
            "Casa": {"min": 50, "max": 5000, "typical": [800, 1200, 2000]},
            "Lazer": {"min": 10, "max": 1000, "typical": [30, 80, 200]}
        }
    
    def categorize_transaction(self, description: str, amount: Decimal, 
                             transaction_type: TransactionType, 
                             existing_categories: List[str] = None) -> Tuple[str, float]:
        """Categoriza uma transação e retorna a categoria e confiança"""
        
        if not description:
            return "Outros", 0.1
        
        description_clean = self._clean_description(description)
        
        # Buscar por palavras-chave
        category_scores = defaultdict(float)
        
        for category, keywords in self.category_keywords.items():
            score = self._calculate_keyword_score(description_clean, keywords)
            if score > 0:
                category_scores[category] = score
        
        # Ajustar score baseado no valor
        for category in category_scores:
            value_score = self._calculate_value_score(amount, category)
            category_scores[category] *= (1 + value_score)
        
        # Ajustar score baseado no tipo de transação
        type_adjustment = self._get_type_adjustment(transaction_type)
        for category in category_scores:
            category_scores[category] *= type_adjustment.get(category, 1.0)
        
        # Encontrar melhor categoria
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            confidence = min(best_category[1], 1.0)  # Limitar confiança a 100%
            
            # Aplicar threshold mínimo de confiança
            if confidence >= 0.3:
                return best_category[0], confidence
        
        # Tentar categorização por padrões de valor
        value_category = self._categorize_by_value(amount, transaction_type)
        if value_category:
            return value_category, 0.4
        
        # Categoria padrão
        return "Outros", 0.1
    
    def _clean_description(self, description: str) -> str:
        """Limpa e normaliza a descrição"""
        # Converter para minúsculas
        clean = description.lower()
        
        # Remover caracteres especiais e números desnecessários
        clean = re.sub(r'[^a-záàâãéèêíìîóòôõúùûç\s]', ' ', clean)
        
        # Remover espaços extras
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
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
                    score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_value_score(self, amount: Decimal, category: str) -> float:
        """Calcula score baseado no valor da transação"""
        if category not in self.value_patterns:
            return 0.0
        
        pattern = self.value_patterns[category]
        amount_float = float(amount)
        
        # Verificar se está na faixa típica
        if pattern["min"] <= amount_float <= pattern["max"]:
            # Verificar se está próximo dos valores típicos
            for typical_value in pattern["typical"]:
                if abs(amount_float - typical_value) / typical_value < 0.5:
                    return 0.3
            return 0.1
        
        return 0.0
    
    def _get_type_adjustment(self, transaction_type: TransactionType) -> Dict[str, float]:
        """Ajustes baseados no tipo de transação"""
        if transaction_type == TransactionType.INCOME:
            return {
                "Investimentos": 1.5,
                "Serviços": 1.3,
                "Outros": 1.0
            }
        else:  # EXPENSE
            return {
                "Alimentação": 1.2,
                "Transporte": 1.2,
                "Casa": 1.1,
                "Saúde": 1.1,
                "Lazer": 1.0,
                "Outros": 1.0
            }
    
    def _categorize_by_value(self, amount: Decimal, transaction_type: TransactionType) -> Optional[str]:
        """Categorização baseada apenas no valor"""
        amount_float = float(amount)
        
        if transaction_type == TransactionType.EXPENSE:
            if amount_float > 1000:
                return "Casa"  # Provavelmente aluguel ou conta grande
            elif amount_float > 500:
                return "Serviços"  # Serviços caros
            elif 50 <= amount_float <= 200:
                return "Alimentação"  # Faixa típica de mercado
            elif amount_float < 20:
                return "Transporte"  # Pequenos gastos de transporte
        
        return None
    
    def batch_categorize(self, db: Session, company_id: int, limit: int = 100) -> Dict[str, int]:
        """Categoriza transações em lote"""
        
        # Buscar transações sem categoria ou com baixa confiança
        transactions = db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.category.is_(None) | (Transaction.ml_confidence < 0.5)
        ).limit(limit).all()
        
        results = {
            "processed": 0,
            "categorized": 0,
            "skipped": 0
        }
        
        for transaction in transactions:
            results["processed"] += 1
            
            try:
                category, confidence = self.categorize_transaction(
                    transaction.description,
                    transaction.amount,
                    transaction.transaction_type
                )
                
                # Só atualizar se a confiança for maior que a atual
                if confidence > (transaction.ml_confidence or 0):
                    transaction.category = category
                    transaction.ml_confidence = confidence
                    results["categorized"] += 1
                else:
                    results["skipped"] += 1
                    
            except Exception as e:
                print(f"Erro ao categorizar transação {transaction.id}: {e}")
                results["skipped"] += 1
        
        db.commit()
        return results
    
    def get_category_suggestions(self, description: str, amount: Decimal, 
                               transaction_type: TransactionType, 
                               top_n: int = 3) -> List[Dict[str, any]]:
        """Retorna sugestões de categorias com scores"""
        
        description_clean = self._clean_description(description)
        category_scores = defaultdict(float)
        
        # Calcular scores para todas as categorias
        for category, keywords in self.category_keywords.items():
            score = self._calculate_keyword_score(description_clean, keywords)
            if score > 0:
                value_score = self._calculate_value_score(amount, category)
                type_adjustment = self._get_type_adjustment(transaction_type)
                
                final_score = score * (1 + value_score) * type_adjustment.get(category, 1.0)
                category_scores[category] = min(final_score, 1.0)
        
        # Ordenar por score e retornar top N
        sorted_categories = sorted(
            category_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_n]
        
        suggestions = []
        for category, score in sorted_categories:
            if score >= 0.1:  # Threshold mínimo
                suggestions.append({
                    "category": category,
                    "confidence": round(score, 2),
                    "confidence_percentage": round(score * 100, 1)
                })
        
        return suggestions
    
    def analyze_spending_patterns(self, db: Session, company_id: int, 
                                days: int = 30) -> Dict[str, any]:
        """Analisa padrões de gastos para melhorar categorização"""
        
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.date >= start_date,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.category.isnot(None)
        ).all()
        
        # Análise por categoria
        category_analysis = defaultdict(lambda: {
            "count": 0,
            "total_amount": 0,
            "avg_amount": 0,
            "descriptions": [],
            "confidence_avg": 0
        })
        
        for transaction in transactions:
            category = transaction.category
            amount = float(transaction.amount)
            confidence = transaction.ml_confidence or 0
            
            category_analysis[category]["count"] += 1
            category_analysis[category]["total_amount"] += amount
            category_analysis[category]["descriptions"].append(transaction.description)
            category_analysis[category]["confidence_avg"] += confidence
        
        # Calcular médias
        for category, data in category_analysis.items():
            if data["count"] > 0:
                data["avg_amount"] = data["total_amount"] / data["count"]
                data["confidence_avg"] = data["confidence_avg"] / data["count"]
        
        # Encontrar padrões
        patterns = {
            "most_frequent_category": max(category_analysis.items(), key=lambda x: x[1]["count"])[0] if category_analysis else None,
            "highest_spending_category": max(category_analysis.items(), key=lambda x: x[1]["total_amount"])[0] if category_analysis else None,
            "lowest_confidence_categories": sorted(
                [(cat, data["confidence_avg"]) for cat, data in category_analysis.items()],
                key=lambda x: x[1]
            )[:3],
            "category_distribution": dict(category_analysis)
        }
        
        return patterns
    
    def train_from_user_corrections(self, db: Session, company_id: int) -> Dict[str, any]:
        """Aprende com correções manuais do usuário (simulado)"""
        
        # Em uma implementação real, isso analisaria correções manuais
        # e ajustaria os pesos das palavras-chave
        
        corrections_analyzed = 0
        patterns_learned = 0
        
        # Simular análise de correções
        transactions_with_low_confidence = db.query(Transaction).filter(
            Transaction.company_id == company_id,
            Transaction.ml_confidence < 0.5,
            Transaction.category.isnot(None)
        ).limit(50).all()
        
        for transaction in transactions_with_low_confidence:
            corrections_analyzed += 1
            
            # Simular aprendizado
            if transaction.description and transaction.category:
                # Em uma implementação real, isso atualizaria os pesos
                patterns_learned += 1
        
        return {
            "corrections_analyzed": corrections_analyzed,
            "patterns_learned": patterns_learned,
            "improvement_estimate": f"{patterns_learned * 2}% melhoria na precisão"
        }

# Instância global do serviço
ml_service = MLCategorizationService()