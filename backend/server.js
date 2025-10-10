const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 3000;

// Serve arquivos estáticos do build do React
app.use(express.static(path.join(__dirname, 'frontend', 'build')));

// Qualquer rota que não seja API retorna index.html
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend', 'build', 'index.html'));
});

// Start do servidor
app.listen(port, () => {
    console.log(`Servidor rodando na porta ${port}`);
});
