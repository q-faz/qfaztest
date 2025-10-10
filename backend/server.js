const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// Servir frontend build do React
app.use(express.static(path.join(__dirname, "frontend/build")));

// Endpoint API exemplo
app.get("/api/hello", (req, res) => {
  res.json({ message: "Olá do backend!" });
});

// Rotas React
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "frontend/build", "index.html"));
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
