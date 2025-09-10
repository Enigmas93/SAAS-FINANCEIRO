import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';

const Reports = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [reportData, setReportData] = useState({
    summary: {
      totalIncome: 0,
      totalExpenses: 0,
      netIncome: 0,
      transactionCount: 0
    },
    categoryBreakdown: [],
    monthlyTrend: [],
    accountBalances: []
  });

  useEffect(() => {
    fetchReportData();
  }, [dateRange]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      
      // Mock data for reports
      const mockData = {
        summary: {
          totalIncome: 12500.00,
          totalExpenses: 8750.00,
          netIncome: 3750.00,
          transactionCount: 45
        },
        categoryBreakdown: [
          { category: 'Serviços', amount: 7500.00, type: 'income', percentage: 60 },
          { category: 'Vendas', amount: 5000.00, type: 'income', percentage: 40 },
          { category: 'Aluguel', amount: 2400.00, type: 'expense', percentage: 27.4 },
          { category: 'Salários', amount: 3500.00, type: 'expense', percentage: 40 },
          { category: 'Marketing', amount: 1200.00, type: 'expense', percentage: 13.7 },
          { category: 'Escritório', amount: 850.00, type: 'expense', percentage: 9.7 },
          { category: 'Outros Gastos', amount: 800.00, type: 'expense', percentage: 9.1 }
        ],
        monthlyTrend: [
          { month: 'Jan', income: 12500, expenses: 8750, net: 3750 },
          { month: 'Fev', income: 11200, expenses: 9100, net: 2100 },
          { month: 'Mar', income: 13800, expenses: 8900, net: 4900 },
          { month: 'Abr', income: 10500, expenses: 7800, net: 2700 },
          { month: 'Mai', income: 14200, expenses: 9500, net: 4700 },
          { month: 'Jun', income: 12800, expenses: 8200, net: 4600 }
        ],
        accountBalances: [
          { name: 'Conta Corrente Principal', balance: 15000.00, type: 'checking' },
          { name: 'Conta Poupança', balance: 25000.00, type: 'savings' },
          { name: 'Caixa', balance: 500.00, type: 'cash' },
          { name: 'Cartão de Crédito', balance: -2500.00, type: 'credit_card' }
        ]
      };
      
      setReportData(mockData);
    } catch (err) {
      setError('Erro ao carregar relatórios');
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

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const exportToPDF = () => {
    // TODO: Implement PDF export
    alert('Funcionalidade de exportação em PDF será implementada em breve!');
  };

  const exportToCSV = () => {
    // TODO: Implement CSV export
    alert('Funcionalidade de exportação em CSV será implementada em breve!');
  };

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
          <h1 className="text-2xl font-bold text-gray-900">Relatórios Financeiros</h1>
          <p className="text-gray-600">Análise detalhada das suas finanças</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={exportToCSV}
            className="btn btn-secondary"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Exportar CSV
          </button>
          <button
            onClick={exportToPDF}
            className="btn btn-primary"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Exportar PDF
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Date Range Filter */}
      <div className="card card-body">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Período de Análise</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Inicial
            </label>
            <input
              type="date"
              className="input"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Final
            </label>
            <input
              type="date"
              className="input"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchReportData}
              className="btn btn-primary w-full"
            >
              Atualizar Relatório
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-success-100 text-success-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Receitas</p>
              <p className="text-xl font-bold text-success-600">
                {formatCurrency(reportData.summary.totalIncome)}
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
              <p className="text-sm text-gray-600">Total Despesas</p>
              <p className="text-xl font-bold text-danger-600">
                {formatCurrency(reportData.summary.totalExpenses)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className={`p-3 rounded-lg ${
              reportData.summary.netIncome >= 0 
                ? 'bg-primary-100 text-primary-600' 
                : 'bg-warning-100 text-warning-600'
            }`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Lucro Líquido</p>
              <p className={`text-xl font-bold ${
                reportData.summary.netIncome >= 0 ? 'text-primary-600' : 'text-warning-600'
              }`}>
                {formatCurrency(reportData.summary.netIncome)}
              </p>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <div className="flex items-center">
            <div className="p-3 bg-gray-100 text-gray-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Transações</p>
              <p className="text-xl font-bold text-gray-900">
                {reportData.summary.transactionCount}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Breakdown por Categoria</h3>
            
            {/* Income Categories */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-success-600 mb-3">Receitas</h4>
              <div className="space-y-3">
                {reportData.categoryBreakdown
                  .filter(item => item.type === 'income')
                  .map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <span className="text-sm text-gray-700 w-24">{item.category}</span>
                        <div className="flex-1 mx-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-success-500 h-2 rounded-full" 
                              style={{ width: `${item.percentage}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-sm text-gray-500 w-12">
                          {formatPercentage(item.percentage)}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-success-600 ml-4">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                  ))
                }
              </div>
            </div>
            
            {/* Expense Categories */}
            <div>
              <h4 className="text-md font-medium text-danger-600 mb-3">Despesas</h4>
              <div className="space-y-3">
                {reportData.categoryBreakdown
                  .filter(item => item.type === 'expense')
                  .map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <span className="text-sm text-gray-700 w-24">{item.category}</span>
                        <div className="flex-1 mx-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-danger-500 h-2 rounded-full" 
                              style={{ width: `${item.percentage}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-sm text-gray-500 w-12">
                          {formatPercentage(item.percentage)}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-danger-600 ml-4">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                  ))
                }
              </div>
            </div>
          </div>
        </div>

        {/* Monthly Trend */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Tendência Mensal</h3>
            <div className="space-y-4">
              {reportData.monthlyTrend.map((month, index) => (
                <div key={index} className="border-b border-gray-200 pb-3 last:border-b-0">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-gray-900">{month.month}</span>
                    <span className={`font-medium ${
                      month.net >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}>
                      {formatCurrency(month.net)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Receitas:</span>
                      <span className="text-success-600">{formatCurrency(month.income)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Despesas:</span>
                      <span className="text-danger-600">{formatCurrency(month.expenses)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Account Balances */}
      <div className="card">
        <div className="card-body">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Saldos por Conta</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {reportData.accountBalances.map((account, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{account.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{account.type.replace('_', ' ')}</p>
                  </div>
                  <div className={`text-right ${
                    account.balance >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    <p className="text-lg font-bold">
                      {formatCurrency(account.balance)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Cash Flow Statement */}
      <div className="card">
        <div className="card-body">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Demonstrativo de Fluxo de Caixa</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="font-medium text-gray-900">Receitas Operacionais</span>
              <span className="font-medium text-success-600">
                {formatCurrency(reportData.summary.totalIncome)}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-200">
              <span className="font-medium text-gray-900">Despesas Operacionais</span>
              <span className="font-medium text-danger-600">
                ({formatCurrency(reportData.summary.totalExpenses)})
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b-2 border-gray-300">
              <span className="font-bold text-gray-900">Fluxo de Caixa Líquido</span>
              <span className={`font-bold text-lg ${
                reportData.summary.netIncome >= 0 ? 'text-success-600' : 'text-danger-600'
              }`}>
                {formatCurrency(reportData.summary.netIncome)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;