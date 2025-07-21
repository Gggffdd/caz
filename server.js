const express = require('express');
const app = express();

// Раздаем статические файлы
app.use(express.static('public'));

// Старт сервера
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
