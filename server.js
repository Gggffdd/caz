const express = require('express');
const path = require('path');
const app = express();

// Раздаем статические файлы
app.use(express.static(path.join(__dirname, 'public')));

// API для получения данных пользователя
app.get('/api/user/:id', (req, res) => {
    // В реальном приложении здесь запрос к БД
    res.json({
        balance: 1000,
        bet: 50
    });
});

// Запуск сервера
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
