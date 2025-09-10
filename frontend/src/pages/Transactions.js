import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [filters, setFilters] = useState({
    type: 'all',
    account_id: 'all',
    category: 'all',
    date_from: '',
    date_to: ''
  });
  const [formData, setFormData] = useState({
    type: 'income',
    amount: 0,
    description: '',
    category: '',
    account_id: '',
    date: new Date().toISOString().split('T')[0],
    notes: ''
  });

  const categories = {
    income: [
      'Vendas',
      'Serviços',
      'Investimentos',
      'Outros Recebimentos'
    ],
    expense: [
      'Alimentação',
      'Transporte',
      'Escritório',
      'Marketing',
      'Impostos',
      'Salários',
      'Aluguel',
      'Utilities',
      'Outros Gastos'
    ]
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Mock accounts data
      const mockAccounts = [
        { id: 1, name: 'Conta Corrente Principal', type: 'checking' },
        { id: 2, name: 'Conta Poupança', type: 'savings' },
        { id: 3, name: 'Caixa', type: 'cash' },
        { id: 4, name: 'Cartão de Crédito', type: 'credit_card' }
      ];
      
      // Mock transactions data
      const mockTransactions = [
        {
          id: 1,
          type: 'income',
          amount: 5000.00,
          description: 'Venda de serviços',
          category: 'Serviços',
          account_id: 1,
          account_name: 'Conta Corrente Principal',
          date: '2024-01-15',
          notes: 'Cliente ABC Ltda',
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 2,
          type: 'expense',
          amount: 1200.00,
          description: 'Aluguel do escritório',
          category: 'Aluguel',
          account_id: 1,
          account_name: 'Conta Corrente Principal',
          date: '2024-01-10',
          notes: 'Pagamento mensal',
          created_at: '2024-01-10T14:30:00Z'
        },
        {
          id: 3,
          type: 'expense',
          amount: 350.00,
          description: 'Material de escritório',
          category: 'Escritório',
          account_id: 1,
          account_name: 'Conta Corrente Principal',
          date: '2024-01-08',
          notes: 'Papelaria e suprimentos',
          created_at: '2024-01-08T09:15:00Z'
        },
        {
          id: 4,
          type: 'income',
          amount: 2500.00,
          description: 'Consultoria técnica',
          category: 'Serviços',
          account_id: 2,
          account_name: 'Conta Poupança',
          date: '2024-01-05',
          notes: 'Projeto XYZ',
          created_at: '2024-01-05T16:45:00Z'
        },
        {
          id: 5,
          type: 'transfer',
          amount: 1000.00,
          description: 'Transferência entre contas',
          category: 'Transferência',
          account_id: 1,
          account_name: 'Conta Corrente Principal',
          date: '2024-01-03',
          notes: 'Para conta poupança',
          created_at: '2024-01-03T11:20:00Z'
        }
      ];
      
      setAccounts(mockAccounts);
      setTransactions(mockTransactions);
    } catch (err) {
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'income':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
          </svg>
        );
      case 'expense':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
          </svg>
        );
      case 'transfer':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'income':
        return 'text-success-600 bg-success-100';
      case 'expense':
        return 'text-danger-600 bg-danger-100';
      case 'transfer':
        return 'text-primary-600 bg-primary-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTransactionLabel = (type) => {
    const labels = {
      income: 'Receita',
      expense: 'Despesa',
      transfer: 'Transferência'
    };
    return labels[type] || type;
  };

  const filteredTransactions = transactions.filter(transaction => {
    if (filters.type !== 'all' && transaction.type !== filters.type) return false;
    if (filters.account_id !== 'all' && transaction.account_id !== parseInt(filters.account_id)) return false;
    if (filters.category !== 'all' && transaction.category !== filters.category) return false;
    if (filters.date_from && transaction.date < filters.date_from) return false;
    if (filters.date_to && transaction.date > filters.date_to) return false;
    return true;
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    // TODO: Implement API call
    console.log('Saving transaction:', formData);
    setShowModal(false);
    setEditingTransaction(null);
    setFormData({
      type: 'income',
      amount: 0,
      description: '',
      category: '',
      account_id: '',
      date: new Date().toISOString().split('T')[0],
      notes: ''
    });
  };

  const handleEdit = (transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      type: transaction.type,
      amount: transaction.amount,
      description: transaction.description,
      category: transaction.category,
      account_id: transaction.account_id,
      date: transaction.date,
      notes: transaction.notes
    });
    setShowModal(true);
  };

  const handleDelete = async (transactionId) => {
    if (window.confirm('Tem certeza que deseja excluir esta transação?')) {
      // TODO: Implement API call
      console.log('Deleting transaction:', transactionId);
    }
  };

  const totalIncome = filteredTransactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = filteredTransactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  const netBalance = totalIncome - totalExpenses;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transações</h1>
          <p className="text-gray-600">Gerencie receitas, despesas e transferências</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Nova Transação
        </button>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 text-success-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Receitas</p>
              <p className="text-2xl font-bold text-success-600">
                {formatCurrency(totalIncome)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-2 bg-danger-100 text-danger-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Despesas</p>
              <p className="text-2xl font-bold text-danger-600">
                {formatCurrency(totalExpenses)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${
              netBalance >= 0 
                ? 'bg-primary-100 text-primary-600' 
                : 'bg-warning-100 text-warning-600'
            }`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Saldo Líquido</p>
              <p className={`text-2xl font-bold ${
                netBalance >= 0 ? 'text-primary-600' : 'text-warning-600'
              }`}>
                {formatCurrency(netBalance)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card card-body">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo
            </label>
            <select
              className="input"
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
            >
              <option value="all">Todos</option>
              <option value="income">Receitas</option>
              <option value="expense">Despesas</option>
              <option value="transfer">Transferências</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conta
            </label>
            <select
              className="input"
              value={filters.account_id}
              onChange={(e) => setFilters({ ...filters, account_id: e.target.value })}
            >
              <option value="all">Todas</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Inicial
            </label>
            <input
              type="date"
              className="input"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Final
            </label>
            <input
              type="date"
              className="input"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => setFilters({
                type: 'all',
                account_id: 'all',
                category: 'all',
                date_from: '',
                date_to: ''
              })}
              className="btn btn-secondary w-full"
            >
              Limpar
            </button>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card">
        <div className="card-body">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Descrição</th>
                  <th>Categoria</th>
                  <th>Conta</th>
                  <th>Data</th>
                  <th>Valor</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td>
                      <div className="flex items-center">
                        <div className={`p-1 rounded ${getTransactionColor(transaction.type)}`}>
                          {getTransactionIcon(transaction.type)}
                        </div>
                        <span className="ml-2 text-sm">
                          {getTransactionLabel(transaction.type)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div>
                        <p className="font-medium text-gray-900">
                          {transaction.description}
                        </p>
                        {transaction.notes && (
                          <p className="text-sm text-gray-500">
                            {transaction.notes}
                          </p>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-secondary">
                        {transaction.category}
                      </span>
                    </td>
                    <td className="text-sm text-gray-600">
                      {transaction.account_name}
                    </td>
                    <td className="text-sm text-gray-600">
                      {formatDate(transaction.date)}
                    </td>
                    <td>
                      <span className={`font-medium ${
                        transaction.type === 'income' 
                          ? 'text-success-600' 
                          : transaction.type === 'expense'
                          ? 'text-danger-600'
                          : 'text-primary-600'
                      }`}>
                        {transaction.type === 'expense' ? '-' : '+'}
                        {formatCurrency(transaction.amount)}
                      </span>
                    </td>
                    <td>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEdit(transaction)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(transaction.id)}
                          className="text-gray-400 hover:text-danger-600"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredTransactions.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">Nenhuma transação encontrada</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3 className="text-lg font-medium text-gray-900">
                {editingTransaction ? 'Editar Transação' : 'Nova Transação'}
              </h3>
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingTransaction(null);
                  setFormData({
                    type: 'income',
                    amount: 0,
                    description: '',
                    category: '',
                    account_id: '',
                    date: new Date().toISOString().split('T')[0],
                    notes: ''
                  });
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="modal-body space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo
                    </label>
                    <select
                      className="input"
                      value={formData.type}
                      onChange={(e) => setFormData({ ...formData, type: e.target.value, category: '' })}
                    >
                      <option value="income">Receita</option>
                      <option value="expense">Despesa</option>
                      <option value="transfer">Transferência</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      className="input"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                      placeholder="0,00"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrição
                  </label>
                  <input
                    type="text"
                    required
                    className="input"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descrição da transação"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Categoria
                    </label>
                    <select
                      className="input"
                      required
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    >
                      <option value="">Selecione uma categoria</option>
                      {(formData.type === 'transfer' ? ['Transferência'] : categories[formData.type] || []).map(category => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Conta
                    </label>
                    <select
                      className="input"
                      required
                      value={formData.account_id}
                      onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                    >
                      <option value="">Selecione uma conta</option>
                      {accounts.map(account => (
                        <option key={account.id} value={account.id}>
                          {account.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data
                  </label>
                  <input
                    type="date"
                    required
                    className="input"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observações (opcional)
                  </label>
                  <textarea
                    className="input"
                    rows={3}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Observações adicionais..."
                  />
                </div>
              </div>
              
              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingTransaction(null);
                    setFormData({
                      type: 'income',
                      amount: 0,
                      description: '',
                      category: '',
                      account_id: '',
                      date: new Date().toISOString().split('T')[0],
                      notes: ''
                    });
                  }}
                  className="btn btn-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingTransaction ? 'Salvar' : 'Criar Transação'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transactions;