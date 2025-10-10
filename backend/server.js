const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Servir frontend
app.use(express.static(path.join(__dirname, '../frontend/build')));

// Rotas API exemplo
app.get('/api/hello', (req, res) => {
  res.json({ message: 'Hello from backend!' });
});

// Todas as outras rotas direcionam para index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build/index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
