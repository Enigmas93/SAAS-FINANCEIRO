-- Criação das extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Inserir empresa demo
INSERT INTO companies (id, name, cnpj, email, phone, address, created_at) 
VALUES (1, 'Empresa Demo', '12.345.678/0001-90', 'contato@empresademo.com', '(11) 99999-9999', 'Rua Demo, 123 - São Paulo, SP', NOW())
ON CONFLICT (id) DO NOTHING;

-- Inserir usuário admin demo
INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at)
VALUES (1, 'admin@empresademo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXzgVLvzgfRy', 'Administrador Demo', 'admin', true, 1, NOW())
ON CONFLICT (email) DO NOTHING;
-- Senha: demo123

-- Inserir contas demo
INSERT INTO accounts (id, name, account_type, balance, bank_name, account_number, is_active, company_id, created_at) VALUES
(1, 'Caixa Principal', 'cash', 5000.00, NULL, NULL, true, 1, NOW()),
(2, 'Banco do Brasil - CC', 'bank', 15000.00, 'Banco do Brasil', '12345-6', true, 1, NOW()),
(3, 'Cartão Empresarial', 'credit_card', -2500.00, 'Banco Itaú', '**** 1234', true, 1, NOW())
ON CONFLICT (id) DO NOTHING;

-- Inserir transações demo
INSERT INTO transactions (id, description, amount, transaction_type, category, transaction_date, from_account_id, to_account_id, company_id, user_id, notes, created_at) VALUES
(1, 'Venda de Produto A', 1500.00, 'income', 'Vendas', NOW() - INTERVAL '5 days', NULL, 1, 1, 1, 'Venda à vista', NOW() - INTERVAL '5 days'),
(2, 'Pagamento Fornecedor XYZ', 800.00, 'expense', 'Fornecedores', NOW() - INTERVAL '4 days', 2, NULL, 1, 1, 'Pagamento de mercadorias', NOW() - INTERVAL '4 days'),
(3, 'Transferência para Caixa', 1000.00, 'transfer', 'Transferência', NOW() - INTERVAL '3 days', 2, 1, 1, 1, 'Reforço de caixa', NOW() - INTERVAL '3 days'),
(4, 'Venda de Serviço B', 2200.00, 'income', 'Serviços', NOW() - INTERVAL '2 days', NULL, 2, 1, 1, 'Prestação de serviços', NOW() - INTERVAL '2 days'),
(5, 'Pagamento Aluguel', 1200.00, 'expense', 'Despesas Fixas', NOW() - INTERVAL '1 day', 2, NULL, 1, 1, 'Aluguel do escritório', NOW() - INTERVAL '1 day')
ON CONFLICT (id) DO NOTHING;

-- Inserir assinatura demo (trial)
INSERT INTO subscriptions (id, plan, status, trial_end, company_id, created_at) 
VALUES (1, 'free', 'trialing', NOW() + INTERVAL '14 days', 1, NOW())
ON CONFLICT (id) DO NOTHING;

-- Inserir fatura demo
INSERT INTO invoices (id, invoice_number, client_name, client_email, client_document, amount, description, due_date, is_paid, company_id, created_at) 
VALUES (1, 'INV-001', 'Cliente Demo Ltda', 'cliente@demo.com', '98.765.432/0001-10', 3500.00, 'Prestação de serviços de consultoria', NOW() + INTERVAL '30 days', false, 1, NOW())
ON CONFLICT (id) DO NOTHING;

-- Atualizar sequências
SELECT setval('companies_id_seq', (SELECT MAX(id) FROM companies));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('accounts_id_seq', (SELECT MAX(id) FROM accounts));
SELECT setval('transactions_id_seq', (SELECT MAX(id) FROM transactions));
SELECT setval('subscriptions_id_seq', (SELECT MAX(id) FROM subscriptions));
SELECT setval('invoices_id_seq', (SELECT MAX(id) FROM invoices));