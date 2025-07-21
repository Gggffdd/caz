const tg = window.Telegram.WebApp;
tg.expand();

const symbols = ["🍒", "🍋", "🍊", "⭐", "7️⃣", "💎"];
document.getElementById('spin-btn').addEventListener('click', () => {
    const result = [
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)],
        symbols[Math.floor(Math.random() * symbols.length)]
    ];
    
    document.getElementById('reels').textContent = result.join(' ');
    tg.sendData(JSON.stringify({ symbols: result }));
});
