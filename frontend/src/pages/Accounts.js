import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import axios from 'axios';

const Accounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'checking',
    initial_balance: 0,
    description: ''
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API call
      const mockAccounts = [
        {
          id: 1,
          name: 'Conta Corrente Principal',
          type: 'checking',
          balance: 15000.00,
          description: 'Conta principal da empresa',
          created_at: '2024-01-01'
        },
        {
          id: 2,
          name: 'Conta Poupança',
          type: 'savings',
          balance: 25000.00,
          description: 'Reserva de emergência',
          created_at: '2024-01-01'
        },
        {
          id: 3,
          name: 'Caixa',
          type: 'cash',
          balance: 500.00,
          description: 'Dinheiro em espécie',
          created_at: '2024-01-01'
        },
        {
          id: 4,
          name: 'Cartão de Crédito',
          type: 'credit_card',
          balance: -2500.00,
          description: 'Cartão empresarial',
          created_at: '2024-01-01'
        }
      ];
      
      setAccounts(mockAccounts);
    } catch (err) {
      setError('Erro ao carregar contas');
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

  const getAccountTypeLabel = (type) => {
    const types = {
      checking: 'Conta Corrente',
      savings: 'Poupança',
      cash: 'Caixa',
      credit_card: 'Cartão de Crédito',
      investment: 'Investimento'
    };
    return types[type] || type;
  };

  const getAccountTypeIcon = (type) => {
    switch (type) {
      case 'checking':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        );
      case 'savings':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
        );
      case 'cash':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 0h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v2M7 7h10" />
          </svg>
        );
      case 'credit_card':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // TODO: Implement API call
    console.log('Saving account:', formData);
    setShowModal(false);
    setEditingAccount(null);
    setFormData({ name: '', type: 'checking', initial_balance: 0, description: '' });
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setFormData({
      name: account.name,
      type: account.type,
      initial_balance: account.balance,
      description: account.description
    });
    setShowModal(true);
  };

  const handleDelete = async (accountId) => {
    if (window.confirm('Tem certeza que deseja excluir esta conta?')) {
      // TODO: Implement API call
      console.log('Deleting account:', accountId);
    }
  };

  const totalBalance = accounts.reduce((sum, account) => sum + account.balance, 0);

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
          <h1 className="text-2xl font-bold text-gray-900">Contas Financeiras</h1>
          <p className="text-gray-600">Gerencie suas contas bancárias, caixa e cartões</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Nova Conta
        </button>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Summary Card */}
      <div className="card card-body">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Saldo Total</h3>
            <p className="text-3xl font-bold text-gray-900">
              {formatCurrency(totalBalance)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">{accounts.length} contas ativas</p>
          </div>
        </div>
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <div key={account.id} className="card">
            <div className="card-body">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${
                    account.balance >= 0 
                      ? 'bg-primary-100 text-primary-600' 
                      : 'bg-danger-100 text-danger-600'
                  }`}>
                    {getAccountTypeIcon(account.type)}
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">
                      {account.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {getAccountTypeLabel(account.type)}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(account)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(account.id)}
                    className="text-gray-400 hover:text-danger-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div className="mt-4">
                <p className={`text-2xl font-bold ${
                  account.balance >= 0 ? 'text-gray-900' : 'text-danger-600'
                }`}>
                  {formatCurrency(account.balance)}
                </p>
                {account.description && (
                  <p className="text-sm text-gray-500 mt-1">
                    {account.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3 className="text-lg font-medium text-gray-900">
                {editingAccount ? 'Editar Conta' : 'Nova Conta'}
              </h3>
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingAccount(null);
                  setFormData({ name: '', type: 'checking', initial_balance: 0, description: '' });
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome da Conta
                  </label>
                  <input
                    type="text"
                    required
                    className="input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ex: Conta Corrente Principal"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Conta
                  </label>
                  <select
                    className="input"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    <option value="checking">Conta Corrente</option>
                    <option value="savings">Poupança</option>
                    <option value="cash">Caixa</option>
                    <option value="credit_card">Cartão de Crédito</option>
                    <option value="investment">Investimento</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Saldo Inicial
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={formData.initial_balance}
                    onChange={(e) => setFormData({ ...formData, initial_balance: parseFloat(e.target.value) || 0 })}
                    placeholder="0,00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrição (opcional)
                  </label>
                  <textarea
                    className="input"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descrição da conta..."
                  />
                </div>
              </div>
              
              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingAccount(null);
                    setFormData({ name: '', type: 'checking', initial_balance: 0, description: '' });
                  }}
                  className="btn btn-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingAccount ? 'Salvar' : 'Criar Conta'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Accounts;