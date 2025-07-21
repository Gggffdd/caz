const express = require('express');
const { createCrypto } = require('telegram-webapp');
const app = express();

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Валидация данных WebApp
app.post('/api/validate', (req, res) => {
  const { initData } = req.body;
  const crypto = createCrypto(process.env.TELEGRAM_BOT_TOKEN);
  
  try {
    const isValid = crypto.validate(initData);
    res.json({ valid: isValid });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Получение баланса пользователя
app.get('/api/balance/:userId', (req, res) => {
  // Здесь должна быть ваша логика получения баланса
  res.json({ 
    balance: 1000,
    currency: '₿'
  });
});

// Обработка ошибок
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

module.exports = app;
