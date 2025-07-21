const tg = window.Telegram.WebApp;
tg.expand();

// Элементы интерфейса
const reelsElement = document.getElementById('reels');
const spinBtn = document.getElementById('spin-btn');
const balanceElement = document.getElementById('balance');
const betElement = document.getElementById('bet');

// Символы для слотов
const symbols = ["🍒", "🍋", "🍊", "⭐", "7️⃣", "💎", "🐶", "🎁"];

// Получаем начальные данные от бота
const initData = tg.initDataUnsafe;
let userBalance = initData.user?.balance || 1000;
let currentBet = initData.user?.bet || 50;

// Обновляем интерфейс
function updateUI() {
    balanceElement.textContent = `${userBalance}₿`;
    betElement.textContent = `Ставка: ${currentBet}₿`;
}

// Обработчик спина
spinBtn.addEventListener('click', () => {
    // Генерируем результат
    const result = [
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)]
    ];
    
    // Отображаем результат
    reelsElement.textContent = result.join(' ');
    
    // Отправляем данные боту
    tg.sendData(JSON.stringify({ 
        action: "spin",
        bet: currentBet,
        symbols: result
    }));
    
    // Визуальные эффекты
    spinBtn.disabled = true;
    setTimeout(() => spinBtn.disabled = false, 1000);
});

// Инициализация
updateUI();
tg.ready();
