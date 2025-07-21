class MiniApp {
  constructor() {
    this.tg = window.Telegram?.WebApp;
    this.init();
  }

  async init() {
    try {
      // 1. Инициализация WebApp
      if (!this.tg) throw new Error('Telegram WebApp not loaded');
      
      this.tg.expand();
      this.tg.enableClosingConfirmation();
      
      // 2. Получение данных пользователя
      const user = this.tg.initDataUnsafe.user || {};
      const userId = user.id || new URLSearchParams(window.location.search).get('user_id');
      
      // 3. Валидация данных
      const isValid = await this.validateData();
      if (!isValid) throw new Error('Invalid init data');
      
      // 4. Загрузка данных пользователя
      const balance = await this.fetchBalance(userId);
      
      // 5. Инициализация UI
      this.initUI(user, balance);
      
      console.log('MiniApp initialized successfully');
    } catch (error) {
      console.error('Initialization error:', error);
      this.showError(error.message);
    }
  }

  async validateData() {
    if (!this.tg.initData) return true; // Пропускаем если нет данных
    
    try {
      const response = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: this.tg.initData })
      });
      
      const { valid } = await response.json();
      return valid;
    } catch (error) {
      return false;
    }
  }

  async fetchBalance(userId) {
    const response = await fetch(`/api/balance/${userId}`);
    return await response.json();
  }

  initUI(user, balance) {
    // Обновление DOM
    document.getElementById('user-name').textContent = 
      [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Гость';
    
    document.getElementById('user-balance').textContent = 
      `${balance.balance}${balance.currency}`;
    
    // Инициализация кнопок
    this.tg.MainButton
      .setText('Закрыть')
      .onClick(() => this.tg.close())
      .show();
    
    document.getElementById('spin-btn').addEventListener('click', () => {
      this.tg.showAlert(`Ваш баланс: ${balance.balance}${balance.currency}`);
    });
  }

  showError(message) {
    document.getElementById('app-container').innerHTML = `
      <div class="error">
        <h3>Ошибка</h3>
        <p>${message}</p>
        <button onclick="window.location.reload()">Перезагрузить</button>
      </div>
    `;
  }
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
  new MiniApp();
});
