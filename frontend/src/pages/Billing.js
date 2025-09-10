import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const Billing = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      
      // Mock subscription data
      const mockSubscription = {
        id: 1,
        plan: 'Pro',
        status: 'active',
        current_period_start: '2024-01-01',
        current_period_end: '2024-02-01',
        amount: 49.90,
        currency: 'BRL'
      };
      
      // Mock invoices data
      const mockInvoices = [
        {
          id: 1,
          amount: 49.90,
          currency: 'BRL',
          status: 'paid',
          created_at: '2024-01-01',
          period_start: '2024-01-01',
          period_end: '2024-02-01'
        },
        {
          id: 2,
          amount: 49.90,
          currency: 'BRL',
          status: 'paid',
          created_at: '2023-12-01',
          period_start: '2023-12-01',
          period_end: '2024-01-01'
        }
      ];
      
      setSubscription(mockSubscription);
      setInvoices(mockInvoices);
    } catch (error) {
      console.error('Error fetching billing data:', error);
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

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { label: 'Ativo', class: 'badge-success' },
      canceled: { label: 'Cancelado', class: 'badge-danger' },
      past_due: { label: 'Em Atraso', class: 'badge-warning' },
      paid: { label: 'Pago', class: 'badge-success' },
      pending: { label: 'Pendente', class: 'badge-warning' },
      failed: { label: 'Falhou', class: 'badge-danger' }
    };
    
    const config = statusConfig[status] || { label: status, class: 'badge-secondary' };
    return <span className={`badge ${config.class}`}>{config.label}</span>;
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
          <h1 className="text-2xl font-bold text-gray-900">Cobrança e Assinatura</h1>
          <p className="text-gray-600">Gerencie sua assinatura e histórico de pagamentos</p>
        </div>
      </div>

      {/* Current Subscription */}
      {subscription && (
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Assinatura Atual</h3>
              {getStatusBadge(subscription.status)}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-600">Plano</p>
                <p className="text-xl font-bold text-gray-900">{subscription.plan}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-600">Valor Mensal</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(subscription.amount)}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-600">Próxima Cobrança</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatDate(subscription.current_period_end)}
                </p>
              </div>
            </div>
            
            <div className="mt-6 flex space-x-4">
              <button className="btn btn-primary">
                Alterar Plano
              </button>
              <button className="btn btn-secondary">
                Atualizar Método de Pagamento
              </button>
              <button className="btn btn-danger">
                Cancelar Assinatura
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Method */}
      <div className="card">
        <div className="card-body">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Método de Pagamento</h3>
            <button className="btn btn-secondary">
              Alterar
            </button>
          </div>
          
          <div className="flex items-center">
            <div className="p-3 bg-gray-100 rounded-lg">
              <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">•••• •••• •••• 4242</p>
              <p className="text-sm text-gray-600">Expira em 12/2025</p>
            </div>
          </div>
        </div>
      </div>

      {/* Billing History */}
      <div className="card">
        <div className="card-body">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Histórico de Cobrança</h3>
          
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Período</th>
                  <th>Valor</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="text-sm text-gray-600">
                      {formatDate(invoice.created_at)}
                    </td>
                    <td className="text-sm text-gray-600">
                      {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                    </td>
                    <td className="font-medium text-gray-900">
                      {formatCurrency(invoice.amount)}
                    </td>
                    <td>
                      {getStatusBadge(invoice.status)}
                    </td>
                    <td>
                      <button className="text-primary-600 hover:text-primary-800 text-sm">
                        Baixar PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Usage Information */}
      <div className="card">
        <div className="card-body">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Uso do Plano</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Empresas</span>
                <span className="text-sm font-medium">1 / 5</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full" style={{ width: '20%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Usuários</span>
                <span className="text-sm font-medium">2 / 10</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full" style={{ width: '20%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Transações/mês</span>
                <span className="text-sm font-medium">45 / 1000</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full" style={{ width: '4.5%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Billing;