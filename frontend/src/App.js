import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const THEME_OPTIONS = [
  { 
    name: 'Claro Profissional', 
    value: 'light', 
    bg: 'bg-gradient-to-br from-gray-50 to-blue-50', 
    header: 'bg-white/90 backdrop-blur-sm shadow-lg border-b border-gray-200', 
    accent: 'blue', 
    isDark: false,
    primary: 'bg-blue-600 hover:bg-blue-700 text-white shadow-md',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-gray-700',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-blue-100 hover:bg-blue-200 text-blue-800',
    buttonBorder: 'border-blue-300'
  },
  { 
    name: 'Escuro Moderno', 
    value: 'dark', 
    bg: 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900', 
    header: 'bg-gray-800/90 backdrop-blur-sm shadow-2xl border-b border-gray-700', 
    accent: 'blue', 
    isDark: true,
    primary: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-gray-100 shadow-md',
    text: 'text-white',
    textSecondary: 'text-gray-300',
    cardBg: 'bg-gray-800/70 backdrop-blur-sm shadow-lg',
    buttonBg: 'bg-gray-700 hover:bg-gray-600 text-gray-100',
    buttonBorder: 'border-gray-600'
  },
  { 
    name: 'Azul Oceano', 
    value: 'ocean', 
    bg: 'bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50', 
    header: 'bg-cyan-500/20 backdrop-blur-sm shadow-lg border-b border-cyan-200', 
    accent: 'cyan', 
    isDark: false,
    primary: 'bg-cyan-600 hover:bg-cyan-700 text-white shadow-md',
    secondary: 'bg-cyan-100 hover:bg-cyan-200 text-cyan-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-cyan-900',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-cyan-100 hover:bg-cyan-200 text-cyan-900',
    buttonBorder: 'border-cyan-300'
  },
  { 
    name: 'Verde Natureza', 
    value: 'green', 
    bg: 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50', 
    header: 'bg-emerald-500/20 backdrop-blur-sm shadow-lg border-b border-emerald-200', 
    accent: 'emerald', 
    isDark: false,
    primary: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-md',
    secondary: 'bg-emerald-100 hover:bg-emerald-200 text-emerald-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-emerald-900',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-emerald-100 hover:bg-emerald-200 text-emerald-900',
    buttonBorder: 'border-emerald-300'
  },
  { 
    name: 'Roxo Elegante', 
    value: 'purple', 
    bg: 'bg-gradient-to-br from-purple-50 via-violet-50 to-indigo-50', 
    header: 'bg-purple-500/20 backdrop-blur-sm shadow-lg border-b border-purple-200', 
    accent: 'purple', 
    isDark: false,
    primary: 'bg-purple-600 hover:bg-purple-700 text-white shadow-md',
    secondary: 'bg-purple-100 hover:bg-purple-200 text-purple-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-purple-900',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-purple-100 hover:bg-purple-200 text-purple-900',
    buttonBorder: 'border-purple-300'
  },
  { 
    name: 'Rosa Vibrante', 
    value: 'pink', 
    bg: 'bg-gradient-to-br from-pink-50 via-rose-50 to-red-50', 
    header: 'bg-pink-500/20 backdrop-blur-sm shadow-lg border-b border-pink-200', 
    accent: 'pink', 
    isDark: false,
    primary: 'bg-pink-600 hover:bg-pink-700 text-white shadow-md',
    secondary: 'bg-pink-100 hover:bg-pink-200 text-pink-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-pink-900',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-pink-100 hover:bg-pink-200 text-pink-900',
    buttonBorder: 'border-pink-300'
  },
  { 
    name: 'Noite Estrelada', 
    value: 'night', 
    bg: 'bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900', 
    header: 'bg-slate-800/90 backdrop-blur-sm shadow-2xl border-b border-purple-500/30', 
    accent: 'indigo', 
    isDark: true,
    primary: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-purple-100 shadow-md',
    text: 'text-white',
    textSecondary: 'text-purple-200',
    cardBg: 'bg-slate-800/70 backdrop-blur-sm shadow-lg',
    buttonBg: 'bg-slate-700 hover:bg-slate-600 text-purple-100',
    buttonBorder: 'border-purple-500/30'
  },
  { 
    name: 'Laranja Sunset', 
    value: 'sunset', 
    bg: 'bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50', 
    header: 'bg-orange-500/20 backdrop-blur-sm shadow-lg border-b border-orange-200', 
    accent: 'orange', 
    isDark: false,
    primary: 'bg-orange-600 hover:bg-orange-700 text-white shadow-md',
    secondary: 'bg-orange-100 hover:bg-orange-200 text-orange-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-orange-900',
    cardBg: 'bg-white/80 backdrop-blur-sm shadow-md',
    buttonBg: 'bg-orange-100 hover:bg-orange-200 text-orange-900',
    buttonBorder: 'border-orange-300'
  }
];

function App() {
  const [stormFile, setStormFile] = useState(null);
  const [bankFiles, setBankFiles] = useState([]);
  const [stormUploaded, setStormUploaded] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [results, setResults] = useState(null);
  const [stormSummary, setStormSummary] = useState(null);
  const [errors, setErrors] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [currentTheme, setCurrentTheme] = useState('light');
  const [showThemeSelector, setShowThemeSelector] = useState(false);

  // Load theme from localStorage on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('app-theme');
    if (savedTheme && THEME_OPTIONS.some(t => t.value === savedTheme)) {
      setCurrentTheme(savedTheme);
    }
  }, []);

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('app-theme', currentTheme);
  }, [currentTheme]);

  // Clear errors after 8 seconds
  useEffect(() => {
    if (errors.length > 0) {
      const timer = setTimeout(() => {
        setErrors([]);
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [errors]);

  const addError = (message, type = 'error') => {
    setErrors(prev => [...prev, { id: Date.now(), message, type }]);
  };

  const getCurrentThemeConfig = () => {
    return THEME_OPTIONS.find(t => t.value === currentTheme) || THEME_OPTIONS[0];
  };

  const getThemeClasses = () => {
    const theme = getCurrentThemeConfig();
    const isDark = theme.isDark;
    
    return {
      bg: theme.bg,
      header: theme.header,
      accent: theme.accent,
      text: theme.text,
      secondaryText: theme.textSecondary,
      cardBg: theme.cardBg || (isDark ? 'bg-gray-800/50 backdrop-blur-sm' : 'bg-white/70 backdrop-blur-sm'),
      isDark: isDark,
      buttonPrimary: theme.primary,
      buttonSecondary: theme.secondary,
      border: isDark ? 'border-gray-700' : 'border-gray-300',
      input: isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900',
      hover: isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
      buttonBg: theme.buttonBg || (isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-100' : 'bg-gray-100 hover:bg-gray-200 text-gray-900'),
      buttonBorder: theme.buttonBorder || (isDark ? 'border-gray-600' : 'border-gray-300')
    };
  };

  const handleStormFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (validateFile(file, true)) {
        setStormFile(file);
        setStormUploaded(false);
        setResults(null);
        setErrors([]);
      }
    }
  };

  const handleBankFilesChange = (event) => {
    const files = Array.from(event.target.files);
    const validFiles = files.filter(file => validateFile(file, false));
    
    if (validFiles.length !== files.length) {
      addError(`${files.length - validFiles.length} arquivo(s) foram ignorados por formato inválido`, 'warning');
    }
    
    setBankFiles(validFiles);
    setResults(null);
  };

  const validateFile = (file, isStorm = false) => {
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validExtensions.includes(fileExtension)) {
      addError(`Arquivo ${file.name} tem formato inválido. Use CSV, XLSX ou XLS.`, 'error');
      return false;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      addError(`Arquivo ${file.name} é muito grande (máximo 50MB).`, 'error');
      return false;
    }

    if (isStorm) {
      const stormIndicators = ['storm', 'contratos', 'digitados', 'pagos'];
      const hasStormIndicator = stormIndicators.some(indicator => 
        file.name.toLowerCase().includes(indicator)
      );
      
      if (!hasStormIndicator) {
        addError(`⚠️ Arquivo ${file.name} não parece ser um relatório da Storm. Verifique se é o arquivo correto.`, 'warning');
        // Don't return false, just warn
      }
    }

    return true;
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e, isStorm = false) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    
    if (isStorm) {
      if (files.length > 0 && validateFile(files[0], true)) {
        setStormFile(files[0]);
        setStormUploaded(false);
        setResults(null);
        setErrors([]);
      }
    } else {
      const validFiles = files.filter(file => validateFile(file, false));
      setBankFiles(validFiles);
      setResults(null);
    }
  }, []);

  const uploadStormFile = async () => {
    if (!stormFile) {
      addError('Selecione o arquivo da Storm primeiro', 'error');
      return;
    }

    try {
      setProcessing(true);
      setProcessingStatus('Processando arquivo da Storm...');
      setErrors([]);
      
      const formData = new FormData();
      formData.append('file', stormFile);

      const response = await axios.post(`${API}/upload-storm`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 second timeout
      });

      setStormSummary(response.data);
      setStormUploaded(true);
      setProcessingStatus('');
      
      // Success notification
      const successMsg = `✅ Storm processada com sucesso! ${response.data.total_proposals} propostas encontradas, ${response.data.paid_cancelled} já processadas (PAGO/CANCELADO)`;
      addError(successMsg, 'success');
      
    } catch (error) {
      console.error('Erro ao fazer upload da Storm:', error);
      let errorMessage = 'Erro ao processar arquivo da Storm';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message.includes('timeout')) {
        errorMessage = 'Tempo limite excedido. Tente com um arquivo menor.';
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Erro de conexão. Verifique sua internet.';
      }
      
      addError(errorMessage, 'error');
    } finally {
      setProcessing(false);
      setProcessingStatus('');
    }
  };

  const processBankFiles = async () => {
    if (!stormUploaded) {
      addError('Primeiro faça upload do arquivo da Storm', 'error');
      return;
    }

    if (bankFiles.length === 0) {
      addError('Selecione pelo menos um arquivo de banco', 'error');
      return;
    }

    try {
      setProcessing(true);
      setProcessingStatus(`Processando ${bankFiles.length} arquivo(s) dos bancos com mapeamento automático...`);
      setErrors([]);
      
      const formData = new FormData();
      bankFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API}/process-banks`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minute timeout for bank processing
      });

      setResults(response.data);
      setProcessingStatus('');
      
      // Enhanced success notification
      const totalMapped = response.data.bank_summaries?.reduce((sum, bank) => sum + (bank.mapped_records || 0), 0) || 0;
      const successMsg = `✅ Processamento concluído! ${response.data.total_records} registros processados. ${totalMapped} registros mapeados automaticamente.`;
      addError(successMsg, 'success');
      
    } catch (error) {
      console.error('Erro ao processar arquivos dos bancos:', error);
      let errorMessage = 'Erro ao processar arquivos dos bancos';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message.includes('timeout')) {
        errorMessage = 'Tempo limite excedido. Tente com arquivos menores.';
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Erro de conexão. Verifique sua internet.';
      }
      
      addError(errorMessage, 'error');
    } finally {
      setProcessing(false);
      setProcessingStatus('');
    }
  };

  const downloadResult = () => {
    if (results && results.download_url) {
      const link = document.createElement('a');
      link.href = `${BACKEND_URL}${results.download_url}`;
      link.click();
    }
  };

  const resetAll = () => {
    setStormFile(null);
    setBankFiles([]);
    setStormUploaded(false);
    setResults(null);
    setStormSummary(null);
    setErrors([]);
    setProcessingStatus('');
  };

  const getErrorIcon = (type) => {
    switch(type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '❌';
    }
  };

  const getErrorColor = (type) => {
    const isDark = themeClasses.isDark;
    switch(type) {
      case 'success': return isDark ? 'bg-green-900 border-green-700 text-green-200' : 'bg-green-50 border-green-200 text-green-800';
      case 'warning': return isDark ? 'bg-yellow-900 border-yellow-700 text-yellow-200' : 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'error': return isDark ? 'bg-red-900 border-red-700 text-red-200' : 'bg-red-50 border-red-200 text-red-800';
      default: return isDark ? 'bg-red-900 border-red-700 text-red-200' : 'bg-red-50 border-red-200 text-red-800';
    }
  };

  const themeClasses = getThemeClasses();

  return (
    <div className={`min-h-screen ${themeClasses.bg} py-8 transition-colors duration-300`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header with Theme Selector */}
        <div className={`${themeClasses.header} rounded-lg shadow-md p-6 mb-8 transition-colors duration-300`}>
          <div className="flex justify-between items-center mb-4">
            <h1 className={`text-3xl font-bold ${themeClasses.text} flex items-center gap-3`}>
              <span className="bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">Q=FAZ</span>
              Sistema de Processamento de Relatórios Financeiros
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">v7.0.0</span>
            </h1>
            
            {/* Theme Selector */}
            <div className="relative">
              <button
                onClick={() => setShowThemeSelector(!showThemeSelector)}
                className={`p-3 rounded-lg ${themeClasses.buttonSecondary} ${themeClasses.text} border ${themeClasses.border} transition-all hover:shadow-md flex items-center space-x-2`}
                title="Alterar tema"
              >
                <span>🎨</span>
                <span className="font-medium">Tema</span>
              </button>
              
              {showThemeSelector && createPortal(
                <>
                  {/* Overlay para fechar ao clicar fora */}
                  <div 
                    className="fixed inset-0 bg-black bg-opacity-20 z-[9998]"
                    onClick={() => setShowThemeSelector(false)}
                  />
                  
                  {/* Dropdown de temas */}
                  <div 
                    className={`fixed top-24 right-8 ${themeClasses.cardBg} rounded-xl shadow-2xl border-2 ${themeClasses.border} p-4 min-w-[300px] max-h-[600px] overflow-y-auto z-[9999]`}
                    style={{ 
                      maxWidth: 'calc(100vw - 32px)',
                      animation: 'slideIn 0.2s ease-out'
                    }}
                  >
                    <div className="mb-3 pb-3 border-b border-gray-300">
                      <h3 className={`text-lg font-bold ${themeClasses.text} flex items-center justify-between`}>
                        <span>🎨 Escolha seu Tema</span>
                        <button
                          onClick={() => setShowThemeSelector(false)}
                          className="text-gray-500 hover:text-gray-700 text-xl"
                        >
                          ✕
                        </button>
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 gap-3">
                      {THEME_OPTIONS.map((theme) => (
                        <button
                          key={theme.value}
                          onClick={() => {
                            setCurrentTheme(theme.value);
                            setShowThemeSelector(false);
                          }}
                          className={`flex items-center space-x-3 p-4 rounded-lg transition-all ${
                            currentTheme === theme.value 
                              ? `${theme.primary} text-white ring-4 ring-${theme.accent}-300 shadow-lg transform scale-105` 
                              : `${themeClasses.hover} ${themeClasses.text} border ${themeClasses.border}`
                          }`}
                        >
                          <div 
                            className={`w-8 h-8 rounded-full ${theme.bg} border-2 shadow-md ${
                              currentTheme === theme.value ? 'border-white' : 'border-gray-400'
                            }`}
                          ></div>
                          <span className="text-sm font-semibold flex-1 text-left">{theme.name}</span>
                          {currentTheme === theme.value && (
                            <span className="text-xl">✓</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </>,
                document.body
              )}
            </div>
          </div>
          
          <div className="text-center">
            <p className={`${themeClasses.secondaryText} mb-2`}>
              Automatize o tratamento de relatórios da Storm e bancos com mapeamento automático
            </p>
            <p className={`text-sm text-${themeClasses.accent}-600 font-medium`}>
              🔄 V6.12.0 - 17 Bancos: Averbai, Digio, Prata, VCTEX, Daycoval, PAN, C6, Facta92, Santander, Crefaz, Quero Mais, Totalcash, Paulista, BRB, Qualibanking, Mercantil, Amigoz
            </p>
            
            {/* Reset Button */}
            <button
              onClick={resetAll}
              className={`mt-4 inline-flex items-center px-6 py-3 border-2 ${themeClasses.border} ${themeClasses.buttonSecondary} ${themeClasses.text} rounded-lg shadow-md text-sm font-semibold transition-all hover:shadow-lg hover:scale-105`}
            >
              🔄 Reiniciar Sistema
            </button>
          </div>
        </div>

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((error) => (
              <div
                key={error.id}
                className={`p-4 rounded-md border ${getErrorColor(error.type)} transition-all duration-300`}
              >
                <div className="flex items-start">
                  <span className="mr-3 text-lg">
                    {getErrorIcon(error.type)}
                  </span>
                  <p className="font-medium leading-relaxed">{error.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Processing Steps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Step 1: Storm Upload */}
          <div className={`${themeClasses.cardBg} rounded-lg shadow-md p-6 transition-all duration-300 hover:shadow-lg`}>
            <div className="flex items-center mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold mr-3 transition-colors ${
                stormUploaded ? 'bg-green-500' : `bg-${themeClasses.accent}-500`
              }`}>
                1
              </div>
              <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
                Upload da Storm
              </h2>
              {stormUploaded && <span className="ml-2 text-green-500">✅</span>}
            </div>
            
            <p className={`${themeClasses.secondaryText} mb-4`}>
              Faça upload do relatório de Contratos Digitados/Pagos da Storm para identificar duplicatas
            </p>

            {/* Drag and Drop Zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 ${
                dragOver 
                  ? `border-${themeClasses.accent}-500 bg-${themeClasses.accent}-50 transform scale-105` 
                  : `border-gray-300 hover:border-${themeClasses.accent}-400`
              } ${currentTheme === 'dark' ? 'border-gray-600 hover:border-gray-500' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, true)}
            >
              <div className="mb-4 text-4xl">
                📁
              </div>
              <div className={`mb-4 ${themeClasses.secondaryText}`}>
                Arraste o arquivo da Storm aqui ou clique para selecionar
              </div>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleStormFileChange}
                className={`block w-full text-sm ${themeClasses.secondaryText} file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-${themeClasses.accent}-50 file:text-${themeClasses.accent}-700 hover:file:bg-${themeClasses.accent}-100 transition-all`}
              />
            </div>

            {stormFile && (
              <div className={`mt-4 p-3 ${currentTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} rounded-md border ${currentTheme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
                <p className={`text-sm ${themeClasses.text} flex items-center`}>
                  <span className="mr-2">📄</span>
                  <span className="font-medium">{stormFile.name}</span>
                  <span className={`ml-auto ${themeClasses.secondaryText}`}>({(stormFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                </p>
              </div>
            )}

            <button
              onClick={uploadStormFile}
              disabled={!stormFile || processing}
              className={`w-full mt-4 py-4 px-6 rounded-lg font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 ${
                themeClasses.buttonPrimary
              }`}
            >
              {processing && processingStatus.includes('Storm') ? 
                '⏳ Processando...' : '🚀 Processar Storm'}
            </button>

            {stormSummary && (
              <div className={`mt-4 p-4 ${themeClasses.isDark ? 'bg-green-900 border-green-700' : 'bg-green-50 border-green-200'} rounded-md border`}>
                <h3 className={`font-semibold ${themeClasses.isDark ? 'text-green-200' : 'text-green-800'} mb-2 flex items-center`}>
                  <span className="mr-2">✅</span>
                  Resumo da Storm
                </h3>
                <div className={`text-sm ${themeClasses.isDark ? 'text-green-300' : 'text-green-700'} space-y-1`}>
                  <div className="flex justify-between">
                    <span>📊 Total de propostas:</span>
                    <strong>{stormSummary.total_proposals}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>🔒 Pagas/Canceladas:</span>
                    <strong>{stormSummary.paid_cancelled}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>📁 Arquivo:</span>
                    <span className="font-medium truncate ml-2">{stormSummary.filename}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Step 2: Bank Files Upload */}
          <div className={`${themeClasses.cardBg} rounded-lg shadow-md p-6 transition-all duration-300 hover:shadow-lg`}>
            <div className="flex items-center mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold mr-3 transition-colors ${
                results ? 'bg-green-500' : stormUploaded ? `bg-${themeClasses.accent}-500` : 'bg-gray-400'
              }`}>
                2
              </div>
              <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
                Upload dos Bancos
              </h2>
              {results && <span className="ml-2 text-green-500">✅</span>}
            </div>
            
            <p className={`${themeClasses.secondaryText} mb-4`}>
              Selecione múltiplos arquivos dos bancos com mapeamento automático
            </p>

            {/* Bank Icons */}
            <div className="flex justify-center space-x-2 mb-4 flex-wrap gap-1">
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Averbai</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>VCTEX</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Digio</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Prata</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Daycoval</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>PAN</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>C6 Bank</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Facta92</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Santander</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Crefaz</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Quero Mais</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Totalcash</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>BRB</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Qualibanking</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Mercantil</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Amigoz</span>
              <span className={`px-3 py-1.5 ${themeClasses.buttonBg} border ${themeClasses.buttonBorder} rounded-full text-xs font-semibold shadow-sm`}>Paulista</span>
            </div>

            {/* Drag and Drop Zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 ${
                dragOver 
                  ? 'border-green-500 bg-green-50 transform scale-105' 
                  : 'border-gray-300 hover:border-green-400'
              } ${!stormUploaded ? 'opacity-50' : ''} ${currentTheme === 'dark' ? 'border-gray-600 hover:border-gray-500' : ''}`}
              onDragOver={!stormUploaded ? undefined : handleDragOver}
              onDragLeave={!stormUploaded ? undefined : handleDragLeave}
              onDrop={!stormUploaded ? undefined : (e) => handleDrop(e, false)}
            >
              <div className="mb-4 text-4xl">
                🏦
              </div>
              <div className={`mb-4 ${themeClasses.secondaryText}`}>
                {stormUploaded ? 'Arraste os arquivos dos bancos aqui ou clique para selecionar' : 'Primeiro processe a Storm'}
              </div>
              <input
                type="file"
                multiple
                accept=".csv,.xlsx,.xls"
                onChange={handleBankFilesChange}
                disabled={!stormUploaded}
                className={`block w-full text-sm ${themeClasses.secondaryText} file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100 disabled:opacity-50 transition-all`}
              />
            </div>

            {bankFiles.length > 0 && (
              <div className={`mt-4 max-h-32 overflow-y-auto border rounded-md ${currentTheme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
                <div className={`p-3 ${currentTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} border-b ${currentTheme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
                  <p className={`text-sm ${themeClasses.secondaryText} font-medium`}>📁 Arquivos selecionados ({bankFiles.length}):</p>
                </div>
                <ul className={`text-xs ${themeClasses.secondaryText} divide-y ${currentTheme === 'dark' ? 'divide-gray-600' : 'divide-gray-200'}`}>
                  {bankFiles.map((file, index) => (
                    <li key={index} className={`flex items-center justify-between p-2 ${currentTheme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-50'}`}>
                      <span className="flex items-center truncate">
                        <span className="mr-2">📄</span>
                        <span className="font-medium">{file.name}</span>
                      </span>
                      <span className={`${themeClasses.secondaryText} ml-2 flex-shrink-0`}>
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              onClick={processBankFiles}
              disabled={!stormUploaded || bankFiles.length === 0 || processing}
              className={`w-full mt-4 py-4 px-6 rounded-lg font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 ${
                themeClasses.buttonPrimary
              }`}
            >
              {processing && processingStatus.includes('bancos') ? 
                '⏳ Processando...' : '🏦 Processar Bancos com Mapeamento'}
            </button>
          </div>
        </div>

        {/* Processing Status */}
        {processing && (
          <div className={`${currentTheme === 'dark' ? 'bg-blue-900 border-blue-700' : 'bg-blue-50 border-blue-200'} border rounded-lg p-6 mb-6`}>
            <div className="flex items-center mb-3">
              <div className={`animate-spin rounded-full h-6 w-6 border-b-2 border-${themeClasses.accent}-600 mr-3`}></div>
              <p className={`${currentTheme === 'dark' ? 'text-blue-200' : 'text-blue-800'} font-medium text-lg`}>{processingStatus}</p>
            </div>
            <div className={`w-full ${currentTheme === 'dark' ? 'bg-blue-800' : 'bg-blue-200'} rounded-full h-3`}>
              <div className={`bg-${themeClasses.accent}-600 h-3 rounded-full animate-pulse transition-all duration-500`} style={{width: '75%'}}></div>
            </div>
            <p className={`${currentTheme === 'dark' ? 'text-blue-300' : 'text-blue-600'} text-sm mt-2`}>⚡ Aplicando mapeamento automático e removendo duplicatas...</p>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className={`${themeClasses.cardBg} rounded-lg shadow-md p-6 mb-6 card-animation`}>
            <h2 className={`text-2xl font-semibold ${themeClasses.text} mb-4 flex items-center`}>
              <span className="mr-3">🎉</span>
              Resultados do Processamento
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className={`${currentTheme === 'dark' ? 'bg-blue-900 border-blue-700' : 'bg-blue-50 border-blue-200'} p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-blue-200' : 'text-blue-800'} flex items-center mb-2`}>
                  <span className="mr-2">📊</span>
                  Total de Registros
                </h3>
                <p className={`text-2xl font-bold ${currentTheme === 'dark' ? 'text-blue-300' : 'text-blue-600'}`}>{results.total_records}</p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-green-900 border-green-700' : 'bg-green-50 border-green-200'} p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-green-200' : 'text-green-800'} flex items-center mb-2`}>
                  <span className="mr-2">🏦</span>
                  Bancos Processados
                </h3>
                <p className={`text-2xl font-bold ${currentTheme === 'dark' ? 'text-green-300' : 'text-green-600'}`}>{results.bank_summaries?.length || 0}</p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-purple-900 border-purple-700' : 'bg-purple-50 border-purple-200'} p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-purple-200' : 'text-purple-800'} flex items-center mb-2`}>
                  <span className="mr-2">🎯</span>
                  Mapeados
                </h3>
                <p className={`text-2xl font-bold ${currentTheme === 'dark' ? 'text-purple-300' : 'text-purple-600'}`}>
                  {results.bank_summaries?.reduce((sum, bank) => sum + (bank.mapped_records || 0), 0) || 0}
                </p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-orange-900 border-orange-700' : 'bg-orange-50 border-orange-200'} p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-orange-200' : 'text-orange-800'} flex items-center mb-2`}>
                  <span className="mr-2">✅</span>
                  Status
                </h3>
                <p className={`text-lg font-bold ${currentTheme === 'dark' ? 'text-orange-300' : 'text-orange-600'}`}>Concluído</p>
              </div>
            </div>

            {/* Enhanced Bank Summaries */}
            {results.bank_summaries && results.bank_summaries.length > 0 && (
              <div className="mb-6">
                <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4 flex items-center`}>
                  <span className="mr-2">📋</span>
                  Resumo Detalhado por Banco
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {results.bank_summaries.map((summary, index) => (
                    <div key={index} className={`border ${currentTheme === 'dark' ? 'border-gray-600 bg-gradient-to-br from-gray-700 to-gray-800' : 'border-gray-200 bg-gradient-to-br from-gray-50 to-white'} rounded-lg p-4 hover:shadow-md transition-shadow`}>
                      <h4 className={`font-semibold ${themeClasses.text} mb-3 flex items-center`}>
                        <span className="mr-2">🏦</span>
                        {summary.bank_name}
                      </h4>
                      <div className={`text-sm ${themeClasses.secondaryText} space-y-2`}>
                        <div className="flex justify-between items-center">
                          <span>📊 Registros:</span>
                          <strong className={`${currentTheme === 'dark' ? 'text-blue-300' : 'text-blue-600'}`}>{summary.total_records}</strong>
                        </div>
                        <div className="flex justify-between items-center">
                          <span>🗑️ Duplicatas removidas:</span>
                          <strong className={`${currentTheme === 'dark' ? 'text-red-300' : 'text-red-600'}`}>{summary.duplicates_removed}</strong>
                        </div>
                        <div className="flex justify-between items-center">
                          <span>🎯 Mapeados:</span>
                          <strong className={`${currentTheme === 'dark' ? 'text-green-300' : 'text-green-600'}`}>{summary.mapped_records || 0}</strong>
                        </div>
                        <div className="flex justify-between items-center">
                          <span>⚪ Não mapeados:</span>
                          <strong className={themeClasses.secondaryText}>{summary.unmapped_records || 0}</strong>
                        </div>
                        
                        {Object.keys(summary.status_distribution).length > 0 && (
                          <div className={`mt-3 pt-3 border-t ${currentTheme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
                            <p className={`font-medium ${themeClasses.text} mb-2 flex items-center`}>
                              <span className="mr-1">📈</span>
                              Distribuição de Status:
                            </p>
                            <div className="space-y-1">
                              {Object.entries(summary.status_distribution).map(([status, count]) => (
                                <div key={status} className="flex justify-between text-xs">
                                  <span className={themeClasses.secondaryText}>• {status}:</span>
                                  <strong className={themeClasses.text}>{count}</strong>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Download Button */}
            <div className="text-center">
              <button
                onClick={downloadResult}
                className={`py-4 px-8 rounded-lg font-bold text-lg shadow-xl transition-all transform hover:scale-110 active:scale-95 mb-3 ${
                  themeClasses.buttonPrimary
                }`}
              >
                <span className="mr-2">📥</span>
                Baixar Relatório Final (CSV)
              </button>
              <p className={`text-sm ${themeClasses.secondaryText}`}>
                Arquivo formatado e otimizado para importar na Storm
              </p>
              <p className={`text-xs ${currentTheme === 'dark' ? 'text-green-300' : 'text-green-600'} mt-1`}>
                ✅ Com mapeamento automático de códigos de tabela aplicado
              </p>
            </div>
          </div>
        )}

        {/* Enhanced Instructions */}
        <div className={`${themeClasses.cardBg} rounded-lg shadow-md p-6`}>
          <h2 className={`text-xl font-semibold ${themeClasses.text} mb-4 flex items-center`}>
            <span className="mr-2">📖</span>
            Guia de Utilização - V6.12.0 com 17 Bancos
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className={`font-semibold ${themeClasses.text} mb-3 flex items-center`}>
                <span className="mr-2">🔄</span>
                Fluxo de Processamento
              </h3>
              <ol className={`list-decimal list-inside space-y-2 ${themeClasses.secondaryText} text-sm`}>
                <li><strong>Storm primeiro:</strong> Upload do relatório da Storm para identificar propostas já processadas</li>
                <li><strong>Bancos depois:</strong> Upload de múltiplos relatórios dos bancos</li>
                <li><strong>Mapeamento automático:</strong> Sistema aplica códigos de tabela baseado em banco + órgão + operação</li>
                <li><strong>Remoção de duplicatas:</strong> Elimina propostas já PAGAS/CANCELADAS na Storm</li>
                <li><strong>Download:</strong> Arquivo final padronizado para importar na Storm</li>
              </ol>
            </div>
            
            <div>
              <h3 className={`font-semibold ${themeClasses.text} mb-3 flex items-center`}>
                <span className="mr-2">🏦</span>
                Bancos com Mapeamento Automático (13 Bancos)
              </h3>
              <ul className={`space-y-2 text-sm ${themeClasses.secondaryText}`}>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                  <strong>Averbai:</strong> INSS, FGTS (múltiplas operações)
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  <strong>VCTEX:</strong> FGTS, INSS (tabelas específicas)
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                  <strong>Digio:</strong> INSS, Prefeituras (códigos TKT)
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                  <strong>Prata:</strong> FGTS (Shake de Morango)
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                  <strong>Daycoval:</strong> INSS, Gov SP, Prefeituras
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
                  <strong>PAN:</strong> INSS Cartão, Benefícios
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-pink-500 rounded-full mr-2"></span>
                  <strong>C6 Bank:</strong> Consignado em geral
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyan-500 rounded-full mr-2"></span>
                  <strong>Facta92:</strong> Múltiplos convênios
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                  <strong>Santander:</strong> Prefeituras, Seguro
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-teal-500 rounded-full mr-2"></span>
                  <strong>Crefaz:</strong> Energia, Boleto
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-rose-500 rounded-full mr-2"></span>
                  <strong>Quero Mais:</strong> INSS, Gov SP
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                  <strong>Totalcash:</strong> Consignado
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-lime-500 rounded-full mr-2"></span>
                  <strong>Paulista:</strong> Múltiplos convênios
                </li>
                <li className={`${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  <strong>BRB:</strong> INSS, Federal (Brasília)
                </li>
                <li className={`${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  <strong>Qualibanking:</strong> INSS (múltiplas tabelas)
                </li>
                <li className={`${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  <strong>Mercantil:</strong> FGTS e INSS
                </li>
                <li className={`${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  <strong>Amigoz:</strong> Cartão Benefício/Consignado INSS
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className={`p-4 ${currentTheme === 'dark' ? 'bg-blue-900 border-blue-700' : 'bg-blue-50 border-blue-200'} border rounded-md`}>
              <h4 className={`font-semibold ${currentTheme === 'dark' ? 'text-blue-200' : 'text-blue-800'} mb-2 flex items-center`}>
                <span className="mr-2">✨</span>
                Funcionalidades V6.12.0
              </h4>
              <ul className={`text-sm ${currentTheme === 'dark' ? 'text-blue-300' : 'text-blue-700'} space-y-1`}>
                <li>• <strong>17 Bancos suportados:</strong> Máxima cobertura do mercado</li>
                <li>• <strong>DIGIO melhorado:</strong> Detecção de prefeituras e correção de códigos/taxas</li>
                <li>• <strong>VCTEX melhorado:</strong> Correção automática de datas trocadas</li>
                <li>• <strong>AVERBAI melhorado:</strong> Reconhecimento automático códigos 992, 1016, 1017+</li>
                <li>• <strong>Sistema robusto:</strong> Prevenção duplo mapeamento, priorização inteligente</li>
                <li>• <strong>Formatação CSV:</strong> Otimizada para Storm</li>
              </ul>
            </div>
            
            <div className={`p-4 ${currentTheme === 'dark' ? 'bg-green-900 border-green-700' : 'bg-green-50 border-green-200'} border rounded-md`}>
              <h4 className={`font-semibold ${currentTheme === 'dark' ? 'text-green-200' : 'text-green-800'} mb-2 flex items-center`}>
                <span className="mr-2">📋</span>
                Formatos e Limites
              </h4>
              <ul className={`text-sm ${currentTheme === 'dark' ? 'text-green-300' : 'text-green-700'} space-y-1`}>
                <li>• <strong>Aceitos:</strong> CSV, XLSX, XLS</li>
                <li>• <strong>Tamanho máximo:</strong> 50MB por arquivo</li>
                <li>• <strong>Múltiplos arquivos:</strong> Sim para bancos</li>
                <li>• <strong>Encoding:</strong> UTF-8, Latin-1, CP1252</li>
                <li>• <strong>Separadores:</strong> ; , \t (detecção automática)</li>
              </ul>
            </div>
          </div>

          <div className={`mt-6 p-4 ${currentTheme === 'dark' ? 'bg-yellow-900 border-yellow-700' : 'bg-yellow-50 border-yellow-200'} border rounded-md`}>
            <h4 className={`font-semibold ${currentTheme === 'dark' ? 'text-yellow-200' : 'text-yellow-800'} mb-2 flex items-center`}>
              <span className="mr-2">⚠️</span>
              Importante para Importação na Storm
            </h4>
            <ul className={`text-sm ${currentTheme === 'dark' ? 'text-yellow-300' : 'text-yellow-700'} space-y-1`}>
              <li>• O arquivo final está formatado com separador <strong>ponto e vírgula (;)</strong></li>
              <li>• Códigos de tabela são mapeados automaticamente quando possível</li>
              <li>• Registros não mapeados mantêm valores originais</li>
              <li>• Sempre verifique o resumo antes de importar na Storm</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 pb-4">
          <p className={`${themeClasses.secondaryText} text-sm`}>
            Desenvolvido com 💙 para Q-FAZ | Versão 7.0.0
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;