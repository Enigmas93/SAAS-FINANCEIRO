import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  const features = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      title: 'Relatórios Completos',
      description: 'Fluxo de caixa, DRE simplificado e gráficos detalhados para acompanhar sua performance financeira.'
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      ),
      title: 'Controle Multi-Contas',
      description: 'Gerencie caixa, bancos e cartões em um só lugar. Transferências automáticas entre contas.'
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      title: 'Faturas e Recibos',
      description: 'Emita faturas profissionais em PDF e controle recebimentos de forma automatizada.'
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
        </svg>
      ),
      title: 'Importação CSV',
      description: 'Importe extratos bancários em CSV e automatize o lançamento de suas transações.'
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      title: 'Multi-Empresa',
      description: 'Gerencie múltiplas empresas com controle de usuários e permissões diferenciadas.'
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: 'Segurança Total',
      description: 'Autenticação JWT, criptografia de dados e backup automático para máxima segurança.'
    }
  ];

  const plans = [
    {
      name: 'Free',
      price: 'Grátis',
      period: '14 dias',
      description: 'Perfeito para testar todas as funcionalidades',
      features: [
        'Todas as funcionalidades',
        '1 empresa',
        '1 usuário',
        'Relatórios básicos',
        'Suporte por email'
      ],
      cta: 'Teste Grátis 14 Dias',
      popular: false
    },
    {
      name: 'Pro',
      price: 'R$ 29',
      period: '/mês',
      yearlyPrice: 'R$ 290/ano',
      description: 'Ideal para pequenos negócios em crescimento',
      features: [
        'Todas as funcionalidades',
        '1 empresa',
        'Usuários ilimitados',
        'Relatórios ilimitados',
        'Importação CSV',
        'Suporte prioritário'
      ],
      cta: 'Começar Agora',
      popular: true
    },
    {
      name: 'Business',
      price: 'R$ 79',
      period: '/mês',
      yearlyPrice: 'R$ 790/ano',
      description: 'Para empresas que precisam de múltiplas filiais',
      features: [
        'Todas as funcionalidades Pro',
        'Empresas ilimitadas',
        'API personalizada',
        'Relatórios avançados',
        'Suporte telefônico',
        'Gerente de conta dedicado'
      ],
      cta: 'Falar com Vendas',
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">FinanceControl</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-700 hover:text-gray-900">
                Entrar
              </Link>
              <Link to="/register" className="btn btn-primary">
                Teste Grátis
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Controle Financeiro
              <span className="block text-primary-200">Simples e Completo</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-primary-100 max-w-3xl mx-auto">
              Gerencie receitas, despesas e fluxo de caixa do seu negócio em uma plataforma intuitiva e segura.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn btn-lg bg-white text-primary-600 hover:bg-gray-100">
                🚀 Teste Grátis 14 Dias
              </Link>
              <button className="btn btn-lg border-2 border-white text-white hover:bg-white hover:text-primary-600">
                Ver Demo
              </button>
            </div>
            <p className="mt-4 text-primary-200">
              ✅ Sem cartão de crédito • ✅ Configuração em 2 minutos
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Tudo que você precisa para controlar suas finanças
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Uma solução completa para pequenos negócios que querem crescer com organização financeira.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card card-body text-center">
                <div className="flex justify-center mb-4">
                  <div className="p-3 bg-primary-100 text-primary-600 rounded-lg">
                    {feature.icon}
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Planos que crescem com seu negócio
            </h2>
            <p className="text-xl text-gray-600">
              Comece grátis e evolua conforme sua necessidade.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <div key={index} className={`card relative ${plan.popular ? 'ring-2 ring-primary-500' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Mais Popular
                    </span>
                  </div>
                )}
                
                <div className="card-body">
                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <div className="mb-2">
                      <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                      <span className="text-gray-600">{plan.period}</span>
                    </div>
                    {plan.yearlyPrice && (
                      <p className="text-sm text-gray-500">ou {plan.yearlyPrice} (2 meses grátis)</p>
                    )}
                    <p className="text-gray-600 mt-2">{plan.description}</p>
                  </div>
                  
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center">
                        <svg className="w-5 h-5 text-success-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <Link
                    to={plan.name === 'Business' ? '/contact' : '/register'}
                    className={`btn w-full ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 text-white py-16">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Pronto para organizar suas finanças?
          </h2>
          <p className="text-xl mb-8 text-primary-100">
            Junte-se a centenas de empresas que já transformaram sua gestão financeira.
          </p>
          <Link to="/register" className="btn btn-lg bg-white text-primary-600 hover:bg-gray-100">
            Começar Teste Grátis Agora
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">FinanceControl</h3>
              <p className="text-gray-400">
                A solução completa para controle financeiro de pequenos negócios.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Produto</h4>
              <ul className="space-y-2 text-gray-400">
                <li><button className="hover:text-white text-left">Funcionalidades</button></li>
                <li><button className="hover:text-white text-left">Preços</button></li>
                <li><button className="hover:text-white text-left">Demo</button></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Suporte</h4>
              <ul className="space-y-2 text-gray-400">
                <li><button className="hover:text-white text-left">Central de Ajuda</button></li>
                <li><button className="hover:text-white text-left">Contato</button></li>
                <li><button className="hover:text-white text-left">Status</button></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><button className="hover:text-white text-left">Privacidade</button></li>
                <li><button className="hover:text-white text-left">Termos</button></li>
                <li><button className="hover:text-white text-left">Cookies</button></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 FinanceControl. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;