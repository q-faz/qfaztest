const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve frontend build
app.use(express.static(path.join(__dirname, 'frontend', 'build')));

// Proxy para backend se estiver separado
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8000', // ou seu backend real
  changeOrigin: true,
}));

// Todas as outras rotas vão para o index.html do React
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server rodando na porta ${PORT}`);
});
