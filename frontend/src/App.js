import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import './App.css';
import axios from 'axios';

// Resolve BACKEND URL with fallbacks:
// 1) build-time env variable REACT_APP_BACKEND_URL
// 2) runtime override window.__BACKEND_URL__ (allows changing backend without rebuilding)
// 3) empty string -> fallback to relative '/api' (same origin / proxy)
const getRuntimeBackendUrl = () => {
  try {
    // runtime override (can be injected into index.html in production)
    if (typeof window !== 'undefined' && window.__BACKEND_URL__) {
      return window.__BACKEND_URL__;
    }
  } catch (e) {
    // ignore
  }

  if (process.env.REACT_APP_BACKEND_URL) return process.env.REACT_APP_BACKEND_URL;
  return '';
};

const BACKEND_URL = getRuntimeBackendUrl();
// Support runtime list of backends injected via index.html
const getRuntimeBackendList = () => {
  try {
    if (typeof window !== 'undefined' && window.__BACKEND_URLS__ && Array.isArray(window.__BACKEND_URLS__)) {
      return window.__BACKEND_URLS__;
    }
  } catch (e) {}
  return BACKEND_URL ? [BACKEND_URL] : [];
};

const BACKEND_LIST = getRuntimeBackendList();
const API = (base) => base ? `${base}/api` : '/api';

// Helper: try primary backend, on network error/timeout try next
const apiPostWithFallback = async (path, formData, config = {}) => {
  const list = BACKEND_LIST.length ? BACKEND_LIST : [''];
  let lastError = null;
  for (let i = 0; i < list.length; i++) {
    const base = list[i];
    const url = base ? `${API(base)}${path}` : `${API('')}${path}`;
    try {
      const resp = await axios.post(url, formData, config);
      // set global chosen backend for download links
      try { if (typeof window !== 'undefined') window.__BACKEND_USED__ = base || ''; } catch(e){}
      return resp;
    } catch (err) {
      lastError = err;
      // if it's a network error or timeout, try next backend
      const isNetwork = err.message && (err.message.includes('Network Error') || err.message.includes('timeout'));
      if (!isNetwork) throw err; // server responded with 4xx/5xx - don't fallback
      // otherwise continue to next
    }
  }
  // all tried
  throw lastError;
};

const THEME_OPTIONS = [
  { 
    name: '🏢 Q-FAZ Oficial', 
    value: 'qfaz', 
    bg: 'bg-gradient-to-br from-blue-50 via-white to-orange-50', 
    header: 'bg-gradient-to-r from-[#07398b]/10 to-[#ee7803]/10 backdrop-blur-sm shadow-xl border-b border-[#07398b]/20', 
    accent: 'blue', 
    isDark: false,
    primary: 'bg-gradient-to-r from-[#07398b] to-[#ee7803] hover:from-[#062d73] hover:to-[#d66a02] text-white shadow-lg transform hover:shadow-xl hover:scale-105',
    secondary: 'bg-gradient-to-r from-blue-100 to-orange-100 hover:from-blue-200 hover:to-orange-200 text-[#07398b] shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-[#07398b]',
    cardBg: 'bg-white/90 backdrop-blur-sm shadow-lg border border-[#07398b]/10',
    buttonBg: 'bg-gradient-to-r from-blue-100 to-orange-100 hover:from-blue-200 hover:to-orange-200 text-[#07398b]',
    buttonBorder: 'border-[#07398b]/20'
  },
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
    name: 'Rosa Dourado', 
    value: 'pink', 
    bg: 'bg-gradient-to-br from-rose-100 via-pink-50 to-orange-100', 
    header: 'bg-gradient-to-r from-rose-500/20 to-pink-500/20 backdrop-blur-sm shadow-xl border-b border-rose-300/50', 
    accent: 'rose', 
    isDark: false,
    primary: 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-700 hover:to-pink-700 text-white shadow-lg transform hover:shadow-xl',
    secondary: 'bg-rose-100 hover:bg-rose-200 text-rose-900 shadow-sm',
    text: 'text-gray-900',
    textSecondary: 'text-rose-800',
    cardBg: 'bg-white/90 backdrop-blur-sm shadow-lg border border-rose-200/50',
    buttonBg: 'bg-gradient-to-r from-rose-100 to-pink-100 hover:from-rose-200 hover:to-pink-200 text-rose-900',
    buttonBorder: 'border-rose-300'
  },
  { 
    name: 'Noite Estrelada Rosa', 
    value: 'night', 
    bg: 'bg-gradient-to-br from-slate-900 via-purple-900/80 to-rose-900/60', 
    header: 'bg-gradient-to-r from-slate-800/95 to-purple-800/95 backdrop-blur-sm shadow-2xl border-b border-rose-500/40', 
    accent: 'rose', 
    isDark: true,
    primary: 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-lg transform hover:shadow-xl',
    secondary: 'bg-slate-700/80 hover:bg-slate-600/80 text-rose-100 shadow-md border border-rose-500/30',
    text: 'text-white',
    textSecondary: 'text-rose-200',
    cardBg: 'bg-slate-800/80 backdrop-blur-sm shadow-xl border border-rose-500/20',
    buttonBg: 'bg-slate-700/70 hover:bg-slate-600/70 text-rose-100 border border-rose-500/30',
    buttonBorder: 'border-rose-500/30'
  },
  { 
    name: 'Céu Estrelado Premium', 
    value: 'starry', 
    bg: 'bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900', 
    header: 'bg-gradient-to-r from-indigo-800/95 to-purple-800/95 backdrop-blur-sm shadow-2xl border-b border-indigo-400/40', 
    accent: 'indigo', 
    isDark: true,
    primary: 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-xl transform hover:shadow-2xl hover:scale-105',
    secondary: 'bg-indigo-800/60 hover:bg-indigo-700/60 text-indigo-100 shadow-lg border border-indigo-400/30',
    text: 'text-white',
    textSecondary: 'text-indigo-200',
    cardBg: 'bg-slate-800/70 backdrop-blur-md shadow-2xl border border-indigo-400/30',
    buttonBg: 'bg-indigo-800/50 hover:bg-indigo-700/50 text-indigo-100 border border-indigo-400/30',
    buttonBorder: 'border-indigo-400/30'
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
  // Links dos bancos para redirecionamento
  const bankLinks = {
    'Averbai': 'https://fintechdocorban.nossafintech.com.br/session/login',
    'VCTEX': 'https://www.appvctex.com.br/login',
    'C6': 'https://c6.c6consig.com.br/WebAutorizador/?FISession=792239cfb4b1',
    'Crefaz': 'https://crefazon.com.br/login',
    'BRB': 'https://q-faz.consig360.com.br/',
    'Digio': 'https://funcaoconsig.digio.com.br/FIMENU/Login/AC.UI.LOGIN.aspx?FISession=1e30f0e19730',
    'Paulista': 'https://creditmanager.bancopaulista.com.br/Login.aspx?ReturnUrl=%2fDefault.aspx',
    'Totalcash': 'https://totalcash.net.br',
    'Prata': 'https://admin.bancoprata.com.br/',
    'Daycoval': 'https://consignado.daycoval.com.br/Autorizador/Login/AC.UI.LOGIN.aspx',
    'Qualibanking': 'https://quali.joinbank.com.br/loans',
    'Quero Mais': 'https://queromaiscredito.app/WebFIMenuMVC/Login/AC.UI.LOGIN.aspx?FISession=d0ce92c59bbe',
    'Amigoz': 'https://amigozconsig.com.br/login',
  'Facta Financeira': 'https://desenv.facta.com.br/sistemaNovo/login.php',
    'Santander': 'https://gestorcf.com.br/corretores/index.php?erro=logoff',
    'PAN': '#', // Link não fornecido
    'Mercantil': '#' // Link não fornecido
  };

  const [stormFile, setStormFile] = useState(null);
  const [bankFiles, setBankFiles] = useState([]);
  const [stormUploaded, setStormUploaded] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [results, setResults] = useState(null);
  const [stormSummary, setStormSummary] = useState(null);
  const [errors, setErrors] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [currentTheme, setCurrentTheme] = useState('qfaz');
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

      const response = await apiPostWithFallback('/upload-storm', formData, {
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

      const response = await apiPostWithFallback('/process-banks', formData, {
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
      // Prefer the backend that answered (set by apiPostWithFallback) or runtime primary
      const used = (typeof window !== 'undefined' && window.__BACKEND_USED__) ? window.__BACKEND_USED__ : (BACKEND_LIST[0] || '');
      const link = document.createElement('a');
      link.href = `${used}${results.download_url}`;
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
    <div className={`min-h-screen ${themeClasses.bg} py-4 sm:py-8 transition-colors duration-300`}>
      <style jsx>{`
        /* Beautiful professional animations */
        @keyframes slideIn {
          0% { 
            opacity: 0; 
            transform: translateY(-20px) scale(0.9); 
          }
          100% { 
            opacity: 1; 
            transform: translateY(0) scale(1); 
          }
        }

        @keyframes fadeInUp {
          0% {
            opacity: 0;
            transform: translateY(30px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes shimmer {
          0% { background-position: -200px 0; }
          100% { background-position: calc(200px + 100%) 0; }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          33% { transform: translateY(-8px) rotate(1deg); }
          66% { transform: translateY(-4px) rotate(-1deg); }
        }

        @keyframes gentleFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-3px); }
        }

        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.4); }
          50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.8), 0 0 30px rgba(59, 130, 246, 0.4); }
        }

        @keyframes qfaz-pulse-glow {
          0%, 100% { 
            box-shadow: 0 0 8px rgba(7, 57, 139, 0.3), 0 0 16px rgba(238, 120, 3, 0.2); 
          }
          50% { 
            box-shadow: 0 0 25px rgba(7, 57, 139, 0.7), 0 0 40px rgba(238, 120, 3, 0.5), 0 0 60px rgba(7, 57, 139, 0.3); 
          }
        }

        @keyframes backgroundMove {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        /* Enhanced bank cards com cores Q-FAZ */
        .bank-card-with-link {
          background: linear-gradient(135deg, rgba(7, 57, 139, 0.05) 0%, #f3f4f6 50%, rgba(238, 120, 3, 0.05) 100%) !important;
          border: 1px solid rgba(7, 57, 139, 0.3) !important;
          color: #07398b !important;
          box-shadow: 0 8px 16px rgba(7, 57, 139, 0.1), 0 4px 8px rgba(238, 120, 3, 0.05) !important;
          position: relative;
          overflow: visible;
          padding: 8px 16px !important;
          border-radius: 12px !important;
          display: inline-flex !important;
          align-items: center;
          justify-content: center;
          min-height: 42px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          backdrop-filter: blur(8px);
        }

        .bank-card-with-link:hover {
          transform: translateY(-4px) scale(1.02) !important;
          box-shadow: 0 16px 32px rgba(7, 57, 139, 0.2), 0 8px 16px rgba(238, 120, 3, 0.1) !important;
          border-color: rgba(238, 120, 3, 0.6) !important;
          background: linear-gradient(135deg, rgba(7, 57, 139, 0.1) 0%, #f1f5f9 50%, rgba(238, 120, 3, 0.1) 100%) !important;
          animation: qfaz-pulse-glow 2s infinite;
        }

        .bank-card-without-link {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
          border: 1px solid rgba(148, 163, 184, 0.3) !important;
          color: #64748b !important;
          box-shadow: 0 4px 8px rgba(148, 163, 184, 0.1) !important;
          padding: 8px 16px !important;
          border-radius: 12px !important;
          display: inline-flex !important;
          align-items: center;
          justify-content: center;
          min-height: 42px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          backdrop-filter: blur(4px);
        }

        .bank-card-without-link:hover {
          transform: translateY(-2px) scale(1.01) !important;
          box-shadow: 0 8px 16px rgba(148, 163, 184, 0.15) !important;
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        }

        .bank-link {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          text-decoration: none;
          color: inherit;
        }

        /* Header improvements com cores Q-FAZ */
        .qfaz-gradient-text {
          background: linear-gradient(135deg, #07398b 0%, #ee7803 50%, #07398b 100%);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: shimmer 3s infinite;
          background-size: 200px 100%;
        }

        /* Card animations */
        .card-animation {
          animation: slideIn 0.6s ease-out;
        }

        .floating-element {
          animation: float 3s ease-in-out infinite;
        }

        /* Custom scrollbar com cores Q-FAZ */
        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.1);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
          background: linear-gradient(135deg, #07398b, #ee7803);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(135deg, #062d73, #d66a02);
        }

        /* Backdrop blur support */
        .backdrop-blur-glass {
          backdrop-filter: blur(20px);
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
      `}</style>
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        {/* Header Professional - Mobile Responsive */}
        <div className={`${themeClasses.header} rounded-2xl shadow-2xl p-6 sm:p-8 mb-8 sm:mb-12 transition-all duration-500 relative overflow-hidden`}
             style={{animation: 'fadeInUp 0.8s ease-out'}}>
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-[#ee7803]/10 to-transparent rounded-full -mr-16 -mt-16"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-[#07398b]/10 to-transparent rounded-full -ml-12 -mb-12"></div>
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 space-y-4 sm:space-y-0">
            <div className="flex flex-col space-y-3">
              {/* Título Principal */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center lg:justify-start gap-4 sm:gap-6 mb-2">
                {/* Título Principal Limpo */}
                <div className="flex items-center justify-center sm:justify-start">
                  <h1 className={`text-4xl sm:text-6xl lg:text-7xl font-black ${themeClasses.text} flex items-center gap-1`}>
                    <span style={{color: '#07398b', textShadow: '2px 2px 4px rgba(7,57,139,0.3)'}}>Q-</span>
                    <span style={{color: '#ee7803', textShadow: '2px 2px 4px rgba(238,120,3,0.3)'}}>FAZ</span>
                  </h1>
                </div>
                
                {/* Badges Profissionais */}
                <div className="flex flex-wrap items-center gap-3 justify-center sm:justify-start">
                  <span className="px-5 py-2 bg-gradient-to-r from-[#07398b] to-[#ee7803] text-white text-xs sm:text-sm rounded-full font-bold shadow-xl transform hover:scale-105 transition-all duration-300 cursor-pointer floating-element border-2 border-white/20">
                    ✨ v7.0.0 PRO
                  </span>
                  <span className="px-4 py-2 bg-gradient-to-r from-[#ee7803] to-[#07398b] text-white text-xs sm:text-sm rounded-full font-bold shadow-lg hover:shadow-xl transition-all duration-300 border border-white/30">
                    🏦 17 Bancos
                  </span>
                  <span className="px-3 py-1 bg-white/90 text-[#07398b] text-xs rounded-full font-semibold shadow-md border border-[#07398b]/20">
                    🚀 IA Powered
                  </span>
                </div>
              </div>
              
              {/* Subtítulo Profissional */}
              <div className="text-center sm:text-left space-y-3">
                <h2 className={`text-xl sm:text-3xl font-bold ${themeClasses.text} leading-tight`}
                    style={{animation: 'fadeInUp 0.8s ease-out 0.2s both'}}>
                  Sistema Inteligente de Processamento de Relatórios Financeiros
                </h2>
                <div className="flex flex-wrap items-center gap-2 justify-center sm:justify-start text-sm sm:text-base">
                  <span className={`${themeClasses.secondaryText} flex items-center gap-1`}>
                    <span className="w-2 h-2 bg-[#07398b] rounded-full animate-pulse"></span>
                    Automação Completa
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className={`${themeClasses.secondaryText} flex items-center gap-1`}>
                    <span className="w-2 h-2 bg-[#ee7803] rounded-full animate-pulse"></span>
                    Mapeamento IA
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className={`${themeClasses.secondaryText} flex items-center gap-1`}>
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    99.9% Precisão
                  </span>
                </div>
              </div>
            </div>
            
            {/* Theme Selector - Mobile Responsive */}
            <div className="relative">
              <button
                onClick={() => setShowThemeSelector(!showThemeSelector)}
                className={`p-3 sm:p-4 rounded-xl ${themeClasses.buttonSecondary} ${themeClasses.text} border ${themeClasses.border} transition-all hover:shadow-xl hover:scale-105 flex items-center space-x-2 sm:space-x-3 text-sm sm:text-base transform active:scale-95 backdrop-blur-sm`}
                title="Alterar tema"
              >
                <span className="text-lg">🎨</span>
                <span className="font-semibold hidden sm:inline">Personalizar</span>
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
                    className={`fixed top-20 sm:top-24 right-2 sm:right-8 ${themeClasses.cardBg} rounded-xl shadow-2xl border-2 ${themeClasses.border} p-3 sm:p-4 min-w-[280px] sm:min-w-[300px] max-h-[70vh] sm:max-h-[600px] overflow-y-auto z-[9999]`}
                    style={{ 
                      maxWidth: 'calc(100vw - 16px)',
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
                    <div className="grid grid-cols-1 gap-2 sm:gap-3">
                      {THEME_OPTIONS.map((theme) => (
                        <button
                          key={theme.value}
                          onClick={() => {
                            setCurrentTheme(theme.value);
                            setShowThemeSelector(false);
                          }}
                          className={`flex items-center space-x-2 sm:space-x-3 p-3 sm:p-4 rounded-lg transition-all ${
                            currentTheme === theme.value 
                              ? `${theme.primary} text-white ring-2 sm:ring-4 ring-${theme.accent}-300 shadow-lg transform scale-105` 
                              : `${themeClasses.hover} ${themeClasses.text} border ${themeClasses.border}`
                          }`}
                        >
                          <div 
                            className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full ${theme.bg} border-2 shadow-md ${
                              currentTheme === theme.value ? 'border-white' : 'border-gray-400'
                            }`}
                          ></div>
                          <span className="text-xs sm:text-sm font-semibold flex-1 text-left">{theme.name}</span>
                          {currentTheme === theme.value && (
                            <span className="text-lg sm:text-xl">✓</span>
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
          
          <div className="text-center space-y-8 relative">
            {/* Descrição Principal Melhorada */}
            <div className="max-w-4xl mx-auto space-y-4"
                 style={{animation: 'fadeInUp 0.8s ease-out 0.4s both'}}>
              <p className={`${themeClasses.secondaryText} text-lg sm:text-xl leading-relaxed px-4 font-medium`}>
                🚀 Revolucione seu processamento financeiro com inteligência artificial
              </p>
              <p className={`${themeClasses.secondaryText} text-sm sm:text-base leading-relaxed px-6 opacity-90`}>
                Automatize completamente o tratamento de relatórios da Storm e bancos com mapeamento automático,
                eliminação inteligente de duplicatas e formatação otimizada para máxima eficiência.
              </p>
              
              {/* Estatísticas Impressionantes */}
              <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto mt-6">
                <div className="text-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                  <div className="text-2xl sm:text-3xl font-bold text-[#07398b]">17</div>
                  <div className="text-xs sm:text-sm text-gray-600">Bancos Suportados</div>
                </div>
                <div className="text-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                  <div className="text-2xl sm:text-3xl font-bold text-[#ee7803]">99.9%</div>
                  <div className="text-xs sm:text-sm text-gray-600">Precisão IA</div>
                </div>
                <div className="text-center p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                  <div className="text-2xl sm:text-3xl font-bold text-green-600">10x</div>
                  <div className="text-xs sm:text-sm text-gray-600">Mais Rápido</div>
                </div>
              </div>
            </div>

            {/* Grid de Bancos Profissional */}
            <div className="flex flex-col items-center space-y-6"
                 style={{animation: 'fadeInUp 0.8s ease-out 0.6s both'}}>
              {/* Título dos Bancos Melhorado */}
              <div className="text-center mb-4">
                <div className="inline-flex items-center gap-3 mb-3">
                  <div className="w-12 h-0.5 bg-gradient-to-r from-transparent to-[#07398b]"></div>
                  <h3 className={`text-xl sm:text-2xl font-bold ${themeClasses.text} flex items-center gap-2`}>
                    <span className="text-2xl">🏦</span>
                    Ecossistema Bancário Completo
                  </h3>
                  <div className="w-12 h-0.5 bg-gradient-to-l from-transparent to-[#ee7803]"></div>
                </div>
                <p className={`text-sm sm:text-base ${themeClasses.secondaryText} max-w-lg mx-auto`}>
                  Integração direta com os principais bancos e instituições financeiras do mercado
                </p>
                <p className={`text-xs ${themeClasses.secondaryText} mt-2 opacity-75`}>
                  💡 Clique nos bancos destacados para acessar seus sistemas de login
                </p>
              </div>
              
              {/* Grid de Bancos Melhorado */}
              <div className="max-w-4xl mx-auto">
                <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-9 gap-2 sm:gap-3">
                  {['Averbai', 'Digio', 'Prata', 'VCTEX', 'Daycoval', 'PAN', 'C6', 'Facta Financeira', 'Santander', 'Crefaz', 'Quero Mais', 'Totalcash', 'Paulista', 'BRB', 'Qualibanking', 'Mercantil', 'Amigoz'].map((bank, index) => {
                    const hasLink = bankLinks[bank] && bankLinks[bank] !== '#';
                    const BankComponent = hasLink ? 'a' : 'div';
                    const linkProps = hasLink ? {
                      href: bankLinks[bank],
                      target: '_blank',
                      rel: 'noopener noreferrer'
                    } : {};
                    
                    return (
                      <BankComponent
                        key={bank} 
                        {...linkProps}
                        className={`bank-link group relative px-4 py-3 ${hasLink ? 'bank-card-with-link' : 'bank-card-without-link'} rounded-xl transition-all duration-300 ${hasLink ? 'cursor-pointer' : 'cursor-default'} block`}
                        style={{ animationDelay: `${index * 50}ms` }}
                        title={hasLink ? `Clique para acessar o sistema do ${bank}` : `${bank} - Sistema não disponível`}
                      >
                        <div className="flex flex-col items-center justify-center gap-1 min-h-[45px]">
                          <span className={`text-xs sm:text-sm font-semibold text-center ${hasLink ? 'text-blue-800' : 'text-gray-600'}`}>
                            {bank}
                          </span>
                          {/* removed link emoji as requested */}
                          {!hasLink && <span className="text-gray-400 text-xs">�</span>}
                        </div>
                      </BankComponent>
                    );
                  })}
                </div>
              </div>
            </div>
            
            {/* Botão Reset Premium */}
            <div className="pt-8 flex justify-center">
              <button
                onClick={resetAll}
                className={`group relative inline-flex items-center px-10 py-4 bg-gradient-to-r from-gray-600 via-gray-700 to-gray-800 hover:from-gray-700 hover:via-gray-800 hover:to-gray-900 text-white rounded-2xl shadow-xl text-sm sm:text-base font-bold transition-all duration-500 hover:shadow-2xl hover:scale-110 active:scale-95 border border-white/10`}
                style={{animation: 'gentleFloat 4s ease-in-out infinite'}}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-[#07398b]/20 to-[#ee7803]/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <span className="relative mr-3 group-hover:rotate-180 transition-transform duration-500 text-lg">🔄</span>
                <span className="relative">Reiniciar Sistema</span>
                <div className="absolute -inset-1 bg-gradient-to-r from-[#07398b]/30 via-gray-600/30 to-[#ee7803]/30 rounded-2xl opacity-0 group-hover:opacity-50 transition-opacity duration-300 blur-sm"></div>
              </button>
            </div>
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

        {/* Processing Steps Premium - Mobile Responsive */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 mb-8 sm:mb-12"
             style={{animation: 'fadeInUp 0.8s ease-out 0.8s both'}}>
          {/* Step 1: Storm Upload Premium - Mobile Responsive */}
          <div className={`${themeClasses.cardBg} rounded-2xl shadow-2xl p-6 sm:p-8 transition-all duration-500 hover:shadow-3xl hover:-translate-y-2 border border-[#07398b]/10 relative overflow-hidden group`}>
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-[#07398b]/5 to-transparent rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
            
            <div className="flex items-center mb-6 relative z-10">
              <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center text-white font-bold mr-4 text-base sm:text-lg transition-all duration-300 shadow-lg ${
                stormUploaded 
                  ? 'bg-gradient-to-r from-green-500 to-green-600 animate-pulse' 
                  : 'bg-gradient-to-r from-[#07398b] to-[#07398b]/80'
              }`}>
                {stormUploaded ? '✓' : '1'}
              </div>
              <div className="flex-1">
                <h2 className={`text-xl sm:text-2xl font-bold ${themeClasses.text} mb-1`}>
                  📊 Upload da Storm
                </h2>
                <p className={`text-sm ${themeClasses.secondaryText} opacity-75`}>
                  Base de dados para identificação de duplicatas
                </p>
              </div>
              {stormUploaded && (
                <div className="ml-3">
                  <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full border border-green-300">
                    ✅ Concluído
                  </span>
                </div>
              )}
            </div>
            
            <p className={`${themeClasses.secondaryText} mb-4 text-sm sm:text-base`}>
              Faça upload do relatório de Contratos Digitados/Pagos da Storm para identificar duplicatas
            </p>

            {/* Drag and Drop Zone - Mobile Responsive */}
            <div
              className={`border-2 border-dashed rounded-lg p-4 sm:p-6 text-center transition-all duration-300 ${
                dragOver 
                  ? `border-${themeClasses.accent}-500 bg-${themeClasses.accent}-50 transform scale-105` 
                  : `border-gray-300 hover:border-${themeClasses.accent}-400`
              } ${currentTheme === 'dark' ? 'border-gray-600 hover:border-gray-500' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, true)}
            >
              <div className="mb-3 text-2xl sm:text-4xl">
                📁
              </div>
              <div className={`mb-4 ${themeClasses.secondaryText} text-xs sm:text-sm`}>
                <span className="hidden sm:inline">Arraste o arquivo da Storm aqui ou clique para selecionar</span>
                <span className="sm:hidden">Toque para selecionar arquivo da Storm</span>
              </div>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleStormFileChange}
                className={`block w-full text-xs sm:text-sm ${themeClasses.secondaryText} file:mr-2 sm:file:mr-4 file:py-1 sm:file:py-2 file:px-2 sm:file:px-4 file:rounded-full file:border-0 file:text-xs sm:file:text-sm file:font-semibold file:bg-${themeClasses.accent}-50 file:text-${themeClasses.accent}-700 hover:file:bg-${themeClasses.accent}-100 transition-all`}
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
              className={`w-full mt-4 py-3 sm:py-4 px-4 sm:px-6 rounded-lg font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 text-sm sm:text-base ${
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

          {/* Step 2: Bank Files Upload Premium - Mobile Responsive */}
          <div className={`${themeClasses.cardBg} rounded-2xl shadow-2xl p-6 sm:p-8 transition-all duration-500 hover:shadow-3xl hover:-translate-y-2 border border-[#ee7803]/10 relative overflow-hidden group ${
            !stormUploaded ? 'opacity-60' : ''
          }`}>
            {/* Background decoration */}
            <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-[#ee7803]/5 to-transparent rounded-full -ml-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
            
            <div className="flex items-center mb-6 relative z-10">
              <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center text-white font-bold mr-4 text-base sm:text-lg transition-all duration-300 shadow-lg ${
                results 
                  ? 'bg-gradient-to-r from-green-500 to-green-600 animate-pulse'
                  : stormUploaded 
                    ? 'bg-gradient-to-r from-[#ee7803] to-[#ee7803]/80'
                    : 'bg-gray-400'
              }`}>
                {results ? '✓' : '2'}
              </div>
              <div className="flex-1">
                <h2 className={`text-xl sm:text-2xl font-bold ${themeClasses.text} mb-1`}>
                  🏦 Upload dos Bancos
                </h2>
                <p className={`text-sm ${themeClasses.secondaryText} opacity-75`}>
                  Processamento inteligente com IA
                </p>
              </div>
              {results && (
                <div className="ml-3">
                  <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full border border-green-300">
                    ✅ Processado
                  </span>
                </div>
              )}
            </div>
            
            <p className={`${themeClasses.secondaryText} mb-4`}>
              Selecione múltiplos arquivos dos bancos com mapeamento automático
            </p>

            {/* Bank Icons - Mobile Responsive Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1 sm:gap-2 mb-4 text-center">
              {['Averbai', 'VCTEX', 'Digio', 'Prata', 'Daycoval', 'PAN', 'C6 Bank', 'Facta Financeira', 'Santander', 'Crefaz', 'Quero Mais', 'Totalcash', 'BRB', 'Qualibanking', 'Mercantil', 'Amigoz', 'Paulista'].map(bank => {
                const hasLink = bankLinks[bank] && bankLinks[bank] !== '#';
                // In the upload section badges should NOT be clickable — only the top grid is clickable
                return (
                  <span key={bank} className={`inline-flex items-center px-2 sm:px-3 py-1 ${hasLink ? 'bank-card-with-link' : 'bank-card-without-link'} text-xs font-semibold shadow-sm`}>
                    <span className={`${hasLink ? 'text-blue-800' : ''}`}>{bank}</span>
                  </span>
                );
              })}
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
            
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
              <div className={`${currentTheme === 'dark' ? 'bg-blue-900 border-blue-700' : 'bg-blue-50 border-blue-200'} p-3 sm:p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-blue-200' : 'text-blue-800'} flex items-center mb-2 text-sm sm:text-base`}>
                  <span className="mr-1 sm:mr-2">📊</span>
                  <span className="hidden sm:inline">Total de Registros</span>
                  <span className="sm:hidden">Registros</span>
                </h3>
                <p className={`text-xl sm:text-2xl font-bold ${currentTheme === 'dark' ? 'text-blue-300' : 'text-blue-600'}`}>{results.total_records}</p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-green-900 border-green-700' : 'bg-green-50 border-green-200'} p-3 sm:p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-green-200' : 'text-green-800'} flex items-center mb-2 text-sm sm:text-base`}>
                  <span className="mr-1 sm:mr-2">🏦</span>
                  <span className="hidden sm:inline">Bancos Processados</span>
                  <span className="sm:hidden">Bancos</span>
                </h3>
                <p className={`text-xl sm:text-2xl font-bold ${currentTheme === 'dark' ? 'text-green-300' : 'text-green-600'}`}>{results.bank_summaries?.length || 0}</p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-purple-900 border-purple-700' : 'bg-purple-50 border-purple-200'} p-3 sm:p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-purple-200' : 'text-purple-800'} flex items-center mb-2 text-sm sm:text-base`}>
                  <span className="mr-1 sm:mr-2">🎯</span>
                  Mapeados
                </h3>
                <p className={`text-xl sm:text-2xl font-bold ${currentTheme === 'dark' ? 'text-purple-300' : 'text-purple-600'}`}>
                  {results.bank_summaries?.reduce((sum, bank) => sum + (bank.mapped_records || 0), 0) || 0}
                </p>
              </div>
              
              <div className={`${currentTheme === 'dark' ? 'bg-orange-900 border-orange-700' : 'bg-orange-50 border-orange-200'} p-3 sm:p-4 rounded-lg border`}>
                <h3 className={`font-semibold ${currentTheme === 'dark' ? 'text-orange-200' : 'text-orange-800'} flex items-center mb-2 text-sm sm:text-base`}>
                  <span className="mr-1 sm:mr-2">✅</span>
                  Status
                </h3>
                <p className={`text-base sm:text-lg font-bold ${currentTheme === 'dark' ? 'text-orange-300' : 'text-orange-600'}`}>Concluído</p>
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

            {/* Download Button - Mobile Responsive */}
            <div className="text-center px-4">
              <button
                onClick={downloadResult}
                className={`w-full sm:w-auto py-3 sm:py-4 px-6 sm:px-8 rounded-lg font-bold text-base sm:text-lg shadow-xl transition-all transform hover:scale-110 active:scale-95 mb-3 ${
                  themeClasses.buttonPrimary
                }`}
              >
                <span className="mr-2">📥</span>
                <span className="hidden sm:inline">Baixar Relatório Final (CSV)</span>
                <span className="sm:hidden">Baixar Relatório</span>
              </button>
              <p className={`text-xs sm:text-sm ${themeClasses.secondaryText} px-2`}>
                Arquivo formatado e otimizado para importar na Storm
              </p>
              <p className={`text-xs ${currentTheme === 'dark' ? 'text-green-300' : 'text-green-600'} mt-1 px-2`}>
                ✅ Com mapeamento automático de códigos de tabela aplicado
              </p>
            </div>
          </div>
        )}

        {/* Enhanced Instructions */}
        <div className={`${themeClasses.cardBg} rounded-lg shadow-md p-6`}>
          <h2 className={`text-xl font-semibold ${themeClasses.text} mb-4 flex items-center`}>
            <span className="mr-2">📖</span>
            Guia de Utilização - V7.0.0 com 17 Bancos
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
                  <strong>Facta Financeira:</strong> Múltiplos convênios
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
                Funcionalidades V7.0.0
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

        {/* Footer - Mobile Responsive */}
        <div className="text-center mt-6 sm:mt-8 pb-4 px-4">
          <p className={`${themeClasses.secondaryText} text-xs sm:text-sm`}>
            Desenvolvido com 💙 para Q-FAZ | Versão 7.0.0
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;