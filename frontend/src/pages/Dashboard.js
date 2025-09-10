import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import axios from 'axios';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API call
      const mockData = {
        summary: {
          total_income: 15000.00,
          total_expenses: 8500.00,
          net_profit: 6500.00,
          accounts_count: 4
        },
        recent_transactions: [
          {
            id: 1,
            description: 'Venda de produto',
            amount: 1200.00,
            type: 'income',
            date: '2024-01-15',
            account: 'Conta Corrente'
          },
          {
            id: 2,
            description: 'Pagamento fornecedor',
            amount: -850.00,
            type: 'expense',
            date: '2024-01-14',
            account: 'Conta Corrente'
          },
          {
            id: 3,
            description: 'Recebimento cliente',
            amount: 2500.00,
            type: 'income',
            date: '2024-01-13',
            account: 'Conta Poupança'
          }
        ],
        monthly_chart: {
          labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
          income: [12000, 15000, 18000, 16000, 20000, 22000],
          expenses: [8000, 9500, 11000, 10500, 12000, 13500]
        }
      };
      
      setDashboardData(mockData);
    } catch (err) {
      setError('Erro ao carregar dados do dashboard');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Bem-vindo, {user?.full_name}!
        </h1>
        <p className="text-primary-100">
          Aqui está um resumo da situação financeira da {user?.company?.name}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-success-100 text-success-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Receitas</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData?.summary?.total_income || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-danger-100 text-danger-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Despesas</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData?.summary?.total_expenses || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 text-primary-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Lucro Líquido</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData?.summary?.net_profit || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 text-yellow-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Contas</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.summary?.accounts_count || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Transações Recentes</h3>
          </div>
          <div className="card-body p-0">
            <div className="overflow-hidden">
              <table className="table">
                <thead>
                  <tr>
                    <th>Descrição</th>
                    <th>Valor</th>
                    <th>Data</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData?.recent_transactions?.map((transaction) => (
                    <tr key={transaction.id}>
                      <td>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {transaction.description}
                          </div>
                          <div className="text-sm text-gray-500">
                            {transaction.account}
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`text-sm font-medium ${
                          transaction.type === 'income' 
                            ? 'text-success-600' 
                            : 'text-danger-600'
                        }`}>
                          {transaction.type === 'income' ? '+' : ''}
                          {formatCurrency(transaction.amount)}
                        </span>
                      </td>
                      <td className="text-sm text-gray-500">
                        {formatDate(transaction.date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card-footer">
            <a href="/transactions" className="text-sm text-primary-600 hover:text-primary-500">
              Ver todas as transações →
            </a>
          </div>
        </div>

        {/* Monthly Chart Placeholder */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Receitas vs Despesas</h3>
          </div>
          <div className="card-body">
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">Gráfico em desenvolvimento</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Chart.js será integrado em breve
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Ações Rápidas</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/transactions?type=income"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="p-2 bg-success-100 text-success-600 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Nova Receita</p>
                <p className="text-sm text-gray-500">Registrar entrada</p>
              </div>
            </a>

            <a
              href="/transactions?type=expense"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="p-2 bg-danger-100 text-danger-600 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Nova Despesa</p>
                <p className="text-sm text-gray-500">Registrar saída</p>
              </div>
            </a>

            <a
              href="/accounts"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="p-2 bg-primary-100 text-primary-600 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Gerenciar Contas</p>
                <p className="text-sm text-gray-500">Ver saldos</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;