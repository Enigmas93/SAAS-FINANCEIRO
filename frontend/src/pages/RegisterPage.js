import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const RegisterPage = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    // User data
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    // Company data
    company_name: '',
    company_document: '',
    company_phone: '',
    company_address: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateStep1 = () => {
    const newErrors = {};
    
    if (!formData.full_name) {
      newErrors.full_name = 'Nome completo é obrigatório';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email é obrigatório';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }
    
    if (!formData.password) {
      newErrors.password = 'Senha é obrigatória';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Senha deve ter pelo menos 6 caracteres';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Confirmação de senha é obrigatória';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Senhas não coincidem';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};
    
    if (!formData.company_name) {
      newErrors.company_name = 'Nome da empresa é obrigatório';
    }
    
    if (!formData.company_document) {
      newErrors.company_document = 'CNPJ/CPF é obrigatório';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handlePrevStep = () => {
    setStep(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep2()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const userData = {
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        company: {
          name: formData.company_name,
          document: formData.company_document,
          phone: formData.company_phone,
          address: formData.company_address
        }
      };
      
      const result = await register(userData);
      
      if (result.success) {
        navigate('/dashboard');
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Erro interno. Tente novamente.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <Link to="/" className="text-3xl font-bold text-primary-600">
            FinanceControl
          </Link>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Crie sua conta gratuita
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Ou{' '}
          <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
            entre na sua conta existente
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="card card-body">
          {/* Progress indicator */}
          <div className="mb-8">
            <div className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${step >= 1 ? 'bg-primary-600 text-white' : 'bg-gray-300 text-gray-600'}`}>
                1
              </div>
              <div className={`flex-1 h-1 mx-2 ${step >= 2 ? 'bg-primary-600' : 'bg-gray-300'}`} />
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${step >= 2 ? 'bg-primary-600 text-white' : 'bg-gray-300 text-gray-600'}`}>
                2
              </div>
            </div>
            <div className="flex justify-between mt-2 text-sm text-gray-600">
              <span>Dados pessoais</span>
              <span>Dados da empresa</span>
            </div>
          </div>

          {errors.general && (
            <div className="mb-6 bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded">
              {errors.general}
            </div>
          )}

          {step === 1 && (
            <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleNextStep(); }}>
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                  Nome completo
                </label>
                <div className="mt-1">
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    autoComplete="name"
                    required
                    className={`input ${errors.full_name ? 'input-error' : ''}`}
                    placeholder="Seu nome completo"
                    value={formData.full_name}
                    onChange={handleChange}
                  />
                  {errors.full_name && (
                    <p className="mt-1 text-sm text-danger-600">{errors.full_name}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    className={`input ${errors.email ? 'input-error' : ''}`}
                    placeholder="seu@email.com"
                    value={formData.email}
                    onChange={handleChange}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-danger-600">{errors.email}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Senha
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    className={`input ${errors.password ? 'input-error' : ''}`}
                    placeholder="Mínimo 6 caracteres"
                    value={formData.password}
                    onChange={handleChange}
                  />
                  {errors.password && (
                    <p className="mt-1 text-sm text-danger-600">{errors.password}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirmar senha
                </label>
                <div className="mt-1">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    className={`input ${errors.confirmPassword ? 'input-error' : ''}`}
                    placeholder="Digite a senha novamente"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                  />
                  {errors.confirmPassword && (
                    <p className="mt-1 text-sm text-danger-600">{errors.confirmPassword}</p>
                  )}
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  className="btn btn-primary w-full"
                >
                  Próximo
                </button>
              </div>
            </form>
          )}

          {step === 2 && (
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="company_name" className="block text-sm font-medium text-gray-700">
                  Nome da empresa
                </label>
                <div className="mt-1">
                  <input
                    id="company_name"
                    name="company_name"
                    type="text"
                    required
                    className={`input ${errors.company_name ? 'input-error' : ''}`}
                    placeholder="Nome da sua empresa"
                    value={formData.company_name}
                    onChange={handleChange}
                  />
                  {errors.company_name && (
                    <p className="mt-1 text-sm text-danger-600">{errors.company_name}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="company_document" className="block text-sm font-medium text-gray-700">
                  CNPJ/CPF
                </label>
                <div className="mt-1">
                  <input
                    id="company_document"
                    name="company_document"
                    type="text"
                    required
                    className={`input ${errors.company_document ? 'input-error' : ''}`}
                    placeholder="00.000.000/0000-00"
                    value={formData.company_document}
                    onChange={handleChange}
                  />
                  {errors.company_document && (
                    <p className="mt-1 text-sm text-danger-600">{errors.company_document}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="company_phone" className="block text-sm font-medium text-gray-700">
                  Telefone (opcional)
                </label>
                <div className="mt-1">
                  <input
                    id="company_phone"
                    name="company_phone"
                    type="tel"
                    className="input"
                    placeholder="(11) 99999-9999"
                    value={formData.company_phone}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="company_address" className="block text-sm font-medium text-gray-700">
                  Endereço (opcional)
                </label>
                <div className="mt-1">
                  <textarea
                    id="company_address"
                    name="company_address"
                    rows={3}
                    className="input"
                    placeholder="Endereço completo da empresa"
                    value={formData.company_address}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={handlePrevStep}
                  className="btn btn-secondary flex-1"
                >
                  Voltar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary flex-1 flex justify-center items-center"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Criando...
                    </>
                  ) : (
                    'Criar conta'
                  )}
                </button>
              </div>
            </form>
          )}

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Benefícios inclusos</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-success-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                14 dias grátis, sem cartão de crédito
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-success-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Todas as funcionalidades liberadas
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-success-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Suporte por email
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600">
            Já tem uma conta?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Faça login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;