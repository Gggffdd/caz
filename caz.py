import os
import random
import asyncio
import logging
import datetime
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from aiogram.types import WebAppData

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = "7523520150:AAGMPibPAl8D0I0E6ZeNR3zuIp0qKcshXN0"
WEB_APP_URL = "https://caz-mj5j43cm9-gggffdds-projects.vercel.app"
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Игровые константы
INITIAL_BALANCE = 1000
MIN_BET = 10
MAX_BET = 500
JACKPOT = 5000
DAILY_BONUS = 50
REFERRAL_BONUS = 100
FREE_SPINS_AFTER = 20
LEVEL_EXPERIENCE = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000]

# Символы для слотов (эмодзи)
SLOT_SYMBOLS = {
    "🍒": {"name": "Cherry", "multiplier": [0, 0, 2, 5, 10], "color": "#FF0000"},
    "🍋": {"name": "Lemon", "multiplier": [0, 0, 2, 5, 10], "color": "#FFFF00"},
    "🍊": {"name": "Orange", "multiplier": [0, 0, 3, 10, 15], "color": "#FFA500"},
    "🍇": {"name": "Grapes", "multiplier": [0, 0, 5, 15, 25], "color": "#800080"},
    "🔔": {"name": "Bell", "multiplier": [0, 0, 10, 20, 50], "color": "#FFD700"},
    "⭐": {"name": "Star", "multiplier": [0, 0, 15, 30, 75], "color": "#FFFFFF"},
    "7️⃣": {"name": "Seven", "multiplier": [0, 0, 25, 50, 100], "color": "#00FF00"},
    "💎": {"name": "Diamond", "multiplier": [0, 0, 50, 100, 250], "color": "#00FFFF"},
    "🐶": {"name": "Dog", "multiplier": [0, 0, 0, 0, 0], "is_wild": True, "color": "#FF69B4"},
    "🎁": {"name": "Bonus", "multiplier": [0, 0, 0, 0, 0], "is_scatter": True, "color": "#32CD32"}
}

# Веса символов для реалистичности
SYMBOL_WEIGHTS = [10, 10, 10, 8, 6, 5, 3, 2, 5, 1]  # Соответствует порядку SLOT_SYMBOLS.keys()

# База данных пользователей (в реальном проекте используйте БД)
user_data = {}

# Достижения
ACHIEVEMENTS = {
    "first_win": {"name": "Первая победа", "reward": 50, "emoji": "🥇"},
    "big_win": {"name": "Крупный выигрыш", "reward": 100, "emoji": "💰"},
    "jackpot": {"name": "Джекпот", "reward": 500, "emoji": "🏆"},
    "level_5": {"name": "Мастер слотов", "reward": 200, "emoji": "🎓"},
    "referral": {"name": "Социальная активность", "reward": 150, "emoji": "👥"}
}

# ===== КЛАВИАТУРЫ =====
def get_main_keyboard(user_id):
    user = user_data.get(user_id, {"balance": INITIAL_BALANCE, "current_bet": MIN_BET})
    current_bet = user["current_bet"]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"🎰 Крутить ({current_bet}₿)", callback_data="spin"),
        InlineKeyboardButton(text="💰 Баланс", callback_data="balance")
    )
    builder.row(
        InlineKeyboardButton(text="➖", callback_data="decrease_bet"),
        InlineKeyboardButton(text=f"Ставка: {current_bet}₿", callback_data="change_bet"),
        InlineKeyboardButton(text="➕", callback_data="increase_bet")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Таблица выплат", callback_data="paytable"),
        InlineKeyboardButton(text="🎁 Бонусы", callback_data="bonuses"),
        InlineKeyboardButton(text="🏆 Лидеры", callback_data="leaders")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Моя статистика", callback_data="stats"),
        InlineKeyboardButton(text="🏅 Достижения", callback_data="achievements"),
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
    )
    # Добавляем кнопку для Mini App
    builder.row(
        InlineKeyboardButton(
            text="🕹️ Играть в Fullscreen", 
            web_app=WebAppInfo(url=f"{WEB_APP_URL}/?user_id={user_id}")
        )
    )
    return builder.as_markup()

def get_paytable_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_help_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    builder.add(InlineKeyboardButton(text="📱 Техподдержка", url="https://t.me/username"))
    return builder.as_markup()

def get_referral_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="👥 Пригласить друзей", 
        url=f"https://t.me/share/url?url=/start=ref_{user_id}"
    ))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_achievements_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

# ===== ИГРОВАЯ ЛОГИКА =====
async def spin_reels():
    symbols = list(SLOT_SYMBOLS.keys())
    
    reels = [
        random.choices(symbols, weights=SYMBOL_WEIGHTS, k=3),
        random.choices(symbols, weights=SYMBOL_WEIGHTS, k=3),
        random.choices(symbols, weights=SYMBOL_WEIGHTS, k=3)
    ]
    
    return reels

def check_win(reels, bet):
    lines = [
        [reels[0][0], reels[1][0], reels[2][0]],  # Верхняя
        [reels[0][1], reels[1][1], reels[2][1]],  # Центральная
        [reels[0][2], reels[1][2], reels[2][2]],  # Нижняя
        [reels[0][0], reels[1][1], reels[2][2]],  # Диагональ \
        [reels[0][2], reels[1][1], reels[2][0]]   # Диагональ /
    ]
    
    total_win = 0
    winning_lines = []
    bonus_triggered = False
    free_spins = 0
    jackpot_won = False
    
    for line_num, line in enumerate(lines):
        # Проверка на бонус (scatter символы)
        scatter_count = line.count("🎁")
        if scatter_count >= 3:
            bonus_triggered = True
            free_spins = scatter_count * 5  # 3+ scatter = фриспины
        
        # Wild символ (🐶) заменяет любые другие (кроме scatter)
        normalized_line = []
        for symbol in line:
            if symbol == "🐶":
                # Ищем следующий не-wild и не-scatter символ в линии
                for s in line:
                    if s != "🐶" and s != "🎁":
                        normalized_line.append(s)
                        break
                else:
                    normalized_line.append("🐶")
            else:
                normalized_line.append(symbol)
        
        # Проверяем комбинации
        for symbol in SLOT_SYMBOLS:
            if symbol == "🎁" or symbol == "🐶":
                continue
                
            count = normalized_line.count(symbol)
            if count >= 3:
                multiplier = SLOT_SYMBOLS[symbol]["multiplier"][count]
                win_amount = bet * multiplier
                total_win += win_amount
                winning_lines.append((line_num, symbol, count, win_amount))
                
                # Проверка на джекпот (5 алмазов)
                if symbol == "💎" and count == 5:
                    total_win += JACKPOT
                    jackpot_won = True
                break
    
    return {
        "total_win": total_win,
        "winning_lines": winning_lines,
        "bonus_triggered": bonus_triggered,
        "free_spins": free_spins,
        "jackpot_won": jackpot_won,
        "reels": reels
    }

async def show_spin_animation(message, chat_id, message_id, duration=1.5):
    symbols = list(SLOT_SYMBOLS.keys())
    frames = 12  # Количество кадров анимации
    
    # Разные скорости для реалистичности
    speeds = [0.05, 0.05, 0.05, 0.07, 0.09, 0.1, 0.12, 0.15, 0.2, 0.3, 0.4, 0.5]
    
    for frame in range(frames):
        try:
            fake_reels = [
                [random.choice(symbols) for _ in range(3)],
                [random.choice(symbols) for _ in range(3)],
                [random.choice(symbols) for _ in range(3)]
            ]
            
            # Создаем эффект замедления
            spin_text = "<b>🎰 DOG HOUSE SLOTS 🎰</b>\n\n"
            spin_text += "╔══════╦══════╦══════╗\n"
            for row in range(3):
                spin_text += "║  " + "  ║  ".join([fake_reels[col][row] for col in range(3)]) + "  ║\n"
                if row < 2:
                    spin_text += "╠══════╬══════╬══════╣\n"
            spin_text += "╚══════╩══════╩══════╝\n\n"
            
            # Добавляем звуковые эффекты
            sound_emojis = ["🔊", "🔉", "🔈"]
            spin_text += f"{sound_emojis[frame % 3]} Барабаны крутятся... {'🎵' * (frame % 3)}\n"
            
            await bot.edit_message_text(
                spin_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=get_main_keyboard(message.from_user.id)
            )
            await asyncio.sleep(speeds[frame] if frame < len(speeds) else 0.1)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Ошибка анимации: {e}")
        except Exception as e:
            logger.error(f"Ошибка анимации: {e}")

def format_reels(reels, winning_lines=None):
    if winning_lines is None:
        winning_lines = []
    
    # Создаем матрицу для подсветки выигрышных позиций
    highlight = [[False for _ in range(3)] for _ in range(3)]
    
    for line in winning_lines:
        line_num = line[0]
        if line_num == 0:  # Верхняя линия
            highlight[0][0] = True
            highlight[1][0] = True
            highlight[2][0] = True
        elif line_num == 1:  # Средняя линия
            highlight[0][1] = True
            highlight[1][1] = True
            highlight[2][1] = True
        elif line_num == 2:  # Нижняя линия
            highlight[0][2] = True
            highlight[1][2] = True
            highlight[2][2] = True
        elif line_num == 3:  # Диагональ \
            highlight[0][0] = True
            highlight[1][1] = True
            highlight[2][2] = True
        elif line_num == 4:  # Диагональ /
            highlight[0][2] = True
            highlight[1][1] = True
            highlight[2][0] = True
    
    result = "╔══════╦══════╦══════╗\n"
    for row in range(3):
        line = "║"
        for col in range(3):
            symbol = reels[col][row]
            if highlight[col][row]:
                line += f" 🔥{symbol}🔥 "
            else:
                line += f"  {symbol}  "
            if col < 2:
                line += "║"
        line += "║\n"
        result += line
        
        if row < 2:
            result += "╠══════╬══════╬══════╣\n"
    result += "╚══════╩══════╩══════╝"
    return result

def check_achievements(user_id, win_amount=0, is_jackpot=False):
    user = user_data[user_id]
    new_achievements = []
    
    # Проверка достижений
    if win_amount > 0 and "first_win" not in user.get("achievements", []):
        user.setdefault("achievements", []).append("first_win")
        new_achievements.append("first_win")
    
    if win_amount >= 500 and "big_win" not in user.get("achievements", []):
        user.setdefault("achievements", []).append("big_win")
        new_achievements.append("big_win")
    
    if is_jackpot and "jackpot" not in user.get("achievements", []):
        user.setdefault("achievements", []).append("jackpot")
        new_achievements.append("jackpot")
    
    if user.get("level", 0) >= 5 and "level_5" not in user.get("achievements", []):
        user.setdefault("achievements", []).append("level_5")
        new_achievements.append("level_5")
    
    if user.get("referrals", 0) >= 3 and "referral" not in user.get("achievements", []):
        user.setdefault("achievements", []).append("referral")
        new_achievements.append("referral")
    
    # Начисление наград за новые достижения
    for achievement in new_achievements:
        reward = ACHIEVEMENTS[achievement]["reward"]
        user["balance"] += reward
    
    return new_achievements

# ===== ОБРАБОТЧИКИ КОМАНД =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    referrer_id = None
    
    # Обработка реферальной ссылки
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith("ref_"):
            try:
                referrer_id = int(ref_code[4:])
            except ValueError:
                pass
    
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": INITIAL_BALANCE,
            "current_bet": MIN_BET,
            "total_spins": 0,
            "total_wins": 0,
            "bonuses": 3,
            "biggest_win": 0,
            "level": 1,
            "experience": 0,
            "referrals": 0,
            "last_bonus": None,
            "last_spins": [],
            "achievements": []
        }
        
        # Начисление бонуса за приглашение
        if referrer_id and referrer_id in user_data and referrer_id != user_id:
            user_data[referrer_id]["balance"] += REFERRAL_BONUS
            user_data[referrer_id]["referrals"] += 1
            await bot.send_message(
                referrer_id,
                f"🎉 По вашей ссылке зарегистрировался новый игрок!\n"
                f"💰 Вы получили {REFERRAL_BONUS}₿ бонуса!"
            )
            # Новый игрок тоже получает бонус
            user_data[user_id]["balance"] += REFERRAL_BONUS
    
    user = user_data[user_id]
    
    welcome_text = f"""
🎰 <b>Добро пожаловать в Dog House Slots!</b> 🐶

💰 <b>Ваш баланс:</b> {user['balance']}₿
🎁 <b>Бонусные спины:</b> {user['bonuses']}
🏅 <b>Уровень:</b> {user['level']}

✨ <b>Специальные возможности:</b>
- Дикие символы 🐶 заменяют любые другие
- Бонусные символы 🎁 запускают фриспины
- Джекпот {JACKPOT}₿ за 5 бриллиантов 💎
- Анимированные вращения и звуковые эффекты

🎯 <b>Используйте кнопки ниже для игры!</b>
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(user_id)
    )

# Обработчик для Mini App
@dp.message(WebAppData)
async def web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        
        if user_id not in user_data:
            await message.answer("Пожалуйста, начните игру с /start")
            return
            
        action = data.get("action")
        
        if action == "get_user_data":
            user = user_data[user_id]
            response = {
                "status": "success",
                "data": {
                    "balance": user["balance"],
                    "current_bet": user["current_bet"],
                    "bonuses": user["bonuses"],
                    "level": user["level"],
                    "experience": user["experience"],
                    "next_level_exp": LEVEL_EXPERIENCE[user["level"]] if user["level"] < len(LEVEL_EXPERIENCE) else 0,
                    "achievements": user.get("achievements", [])
                }
            }
            await message.answer(json.dumps(response))
            
        elif action == "spin":
            user = user_data[user_id]
            bet = data.get("bet", user["current_bet"])
            
            if bet < MIN_BET or bet > MAX_BET:
                await message.answer(json.dumps({"status": "error", "message": "Недопустимая ставка"}))
                return
                
            if user["balance"] < bet and user["bonuses"] == 0:
                await message.answer(json.dumps({"status": "error", "message": "Недостаточно средств"}))
                return
                
            use_bonus = False
            if user["bonuses"] > 0:
                user["bonuses"] -= 1
                use_bonus = True
            else:
                user["balance"] -= bet
                
            spin_result = await spin_reels()
            win_info = check_win(spin_result, bet)
            win_amount = win_info["total_win"]
            user["balance"] += win_amount
            user["total_spins"] += 1
            
            if win_amount > 0:
                user["total_wins"] += 1
                if win_amount > user["biggest_win"]:
                    user["biggest_win"] = win_amount
            
            # Добавляем опыт
            exp_gain = min(1 + win_amount // 100, 10)
            user["experience"] += exp_gain
            
            # Проверяем повышение уровня
            level_up = False
            while user["level"] < len(LEVEL_EXPERIENCE) and user["experience"] >= LEVEL_EXPERIENCE[user["level"]]:
                user["level"] += 1
                level_up = True
                level_bonus = user["level"] * 100
                user["balance"] += level_bonus
            
            # Проверка достижений
            new_achievements = check_achievements(user_id, win_amount, win_info["jackpot_won"])
            
            response = {
                "status": "success",
                "data": {
                    "reels": spin_result,
                    "win_amount": win_amount,
                    "winning_lines": win_info["winning_lines"],
                    "bonus_triggered": win_info["bonus_triggered"],
                    "free_spins": win_info["free_spins"],
                    "jackpot_won": win_info["jackpot_won"],
                    "new_balance": user["balance"],
                    "use_bonus": use_bonus,
                    "remaining_bonuses": user["bonuses"],
                    "level_up": level_up,
                    "new_level": user["level"] if level_up else None,
                    "new_achievements": new_achievements,
                    "experience": user["experience"],
                    "next_level_exp": LEVEL_EXPERIENCE[user["level"]] if user["level"] < len(LEVEL_EXPERIENCE) else 0
                }
            }
            
            if win_info["bonus_triggered"]:
                user["bonuses"] += win_info["free_spins"]
                response["data"]["remaining_bonuses"] = user["bonuses"]
            
            await message.answer(json.dumps(response))
            
        elif action == "change_bet":
            user = user_data[user_id]
            new_bet = data.get("bet", MIN_BET)
            
            if MIN_BET <= new_bet <= MAX_BET:
                user["current_bet"] = new_bet
                await message.answer(json.dumps({
                    "status": "success",
                    "new_bet": new_bet
                }))
            else:
                await message.answer(json.dumps({
                    "status": "error",
                    "message": f"Ставка должна быть между {MIN_BET} и {MAX_BET}"
                }))
                
    except Exception as e:
        logger.error(f"WebApp error: {e}")
        await message.answer(json.dumps({
            "status": "error",
            "message": "Произошла ошибка"
        }))

@dp.callback_query(lambda c: c.data == "spin")
async def process_spin(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    bet = user["current_bet"]
    use_bonus = False
    
    # Проверяем, есть ли бонусные спины
    if user["bonuses"] > 0:
        user["bonuses"] -= 1
        use_bonus = True
        await callback.answer("🎁 Использован бонусный спин!")
    else:
        if user["balance"] < bet:
            await callback.answer("❌ Недостаточно средств! Уменьшите ставку.", show_alert=True)
            return
        user["balance"] -= bet
    
    # Начинаем вращение
    user["total_spins"] += 1
    
    # Показываем анимацию
    await show_spin_animation(callback.message, callback.message.chat.id, callback.message.message_id)
    
    # Получаем результат
    spin_result = await spin_reels()
    win_info = check_win(spin_result, bet)
    
    # Обновляем баланс
    win_amount = win_info["total_win"]
    user["balance"] += win_amount
    
    # Обновляем статистику
    if win_amount > 0:
        user["total_wins"] += 1
        if win_amount > user["biggest_win"]:
            user["biggest_win"] = win_amount
    
    # Добавляем опыт
    exp_gain = min(1 + win_amount // 100, 10)  # Опыт зависит от выигрыша
    user["experience"] += exp_gain
    
    # Проверяем повышение уровня
    level_up = False
    while user["level"] < len(LEVEL_EXPERIENCE) and user["experience"] >= LEVEL_EXPERIENCE[user["level"]]:
        user["level"] += 1
        level_up = True
        # Награда за уровень
        level_bonus = user["level"] * 100
        user["balance"] += level_bonus
    
    # Добавляем в историю
    user["last_spins"].append({
        "reels": spin_result,
        "win": win_amount,
        "timestamp": datetime.datetime.now().isoformat()
    })
    if len(user["last_spins"]) > 10:
        user["last_spins"].pop(0)
    
    # Проверка на бонусный раунд
    if win_info["bonus_triggered"]:
        free_spins = win_info["free_spins"]
        user["bonuses"] += free_spins
    
    # Проверка достижений
    new_achievements = check_achievements(user_id, win_amount, win_info["jackpot_won"])
    
    # Формируем результат
    result_text = "<b>🎰 DOG HOUSE SLOTS 🎰</b>\n\n"
    
    # Отображаем барабаны с подсветкой выигрышных линий
    result_text += format_reels(spin_result, win_info["winning_lines"]) + "\n\n"
    
    # Показываем выигрышные линии
    if win_info["winning_lines"]:
        result_text += "🎉 <b>ВЫИГРЫШ!</b> 🎉\n"
        for line in win_info["winning_lines"]:
            line_num, symbol, count, win = line
            line_names = ["Верхняя", "Центральная", "Нижняя", "Диагональ \\", "Диагональ /"]
            result_text += (
                f"➡️ <b>{line_names[line_num]} линия:</b> "
                f"{count}x {symbol} = <b>{win}₿</b>\n"
            )
        result_text += f"\n💰 <b>Общий выигрыш:</b> {win_amount}₿\n"
    else:
        result_text += "😢 <b>Повезёт в следующий раз!</b>\n"
    
    # Джекпот
    if win_info["jackpot_won"]:
        result_text += f"\n🏆 <b>ДЖЕКПОТ!!!</b> 🏆\nВы выиграли {JACKPOT}₿ дополнительно!\n"
    
    # Бонусный раунд
    if win_info["bonus_triggered"]:
        result_text += f"\n🎁 <b>БОНУСНЫЙ РАУНД!</b> 🎁\nВы получили {win_info['free_spins']} бесплатных спинов!"
    
    # Уровень
    if level_up:
        result_text += f"\n🏆 <b>УРОВЕНЬ ПОВЫШЕН!</b> 🏆\nТеперь вы на уровне {user['level']}!"
    
    # Достижения
    if new_achievements:
        result_text += "\n\n🏅 <b>НОВЫЕ ДОСТИЖЕНИЯ!</b> 🏅\n"
        for achievement in new_achievements:
            ach_data = ACHIEVEMENTS[achievement]
            reward = ach_data["reward"]
            result_text += f"{ach_data['emoji']} {ach_data['name']} +{reward}₿\n"
    
    # Общая информация
    result_text += (
        f"\n💵 <b>Ставка:</b> {bet}₿"
        f"\n💰 <b>Баланс:</b> {user['balance']}₿"
        f"\n🏅 <b>Уровень:</b> {user['level']} (+{exp_gain} опыта)"
    )
    
    if use_bonus:
        result_text += f"\n🎁 <b>Осталось бонусных спинов:</b> {user['bonuses']}"
    
    # Особые уведомления
    if win_amount >= JACKPOT:
        result_text += "\n\n🎆 <b>МЕГА ДЖЕКПОТ!!!</b> 🎆"
    elif win_amount >= bet * 50:
        result_text += "\n\n🔥 <b>ОГРОМНЫЙ ВЫИГРЫШ!</b> 🔥"
    elif win_amount >= bet * 20:
        result_text += "\n\n✨ <b>ОТЛИЧНЫЙ РЕЗУЛЬТАТ!</b> ✨"
    
    # Бесплатные спины за активность
    if user["total_spins"] % FREE_SPINS_AFTER == 0:
        user["bonuses"] += 1
        result_text += f"\n\n🎉 <b>Бонус за активность!</b> 🎉\nВы получили 1 бесплатный спин!"
    
    # Обновляем сообщение
    try:
        await bot.edit_message_text(
            result_text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=get_main_keyboard(user_id)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Ошибка при обновлении сообщения: {e}")

@dp.callback_query(lambda c: c.data in ["increase_bet", "decrease_bet"])
async def change_bet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    current_bet = user["current_bet"]
    
    if callback.data == "increase_bet":
        new_bet = min(current_bet * 2, MAX_BET)
    else:
        new_bet = max(current_bet // 2, MIN_BET)
    
    if new_bet != current_bet:
        user["current_bet"] = new_bet
        await callback.answer(f"Ставка изменена: {new_bet}₿")
    else:
        if callback.data == "increase_bet":
            await callback.answer(f"Максимальная ставка: {MAX_BET}₿")
        else:
            await callback.answer(f"Минимальная ставка: {MIN_BET}₿")
    
    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=get_main_keyboard(user_id)
        )
    except TelegramBadRequest:
        pass

@dp.callback_query(lambda c: c.data == "paytable")
async def show_paytable(callback: types.CallbackQuery):
    paytable_text = """
<b>📊 ТАБЛИЦА ВЫПЛАТ</b>

Выигрыши рассчитываются от ставки за линию:

🍒 Вишня:   2x | 5x | 10x
🍋 Лимон:   2x | 5x | 10x
🍊 Апельсин: 3x | 10x | 15x
🍇 Виноград: 5x | 15x | 25x
🔔 Колокол: 10x | 20x | 50x
⭐ Звезда:  15x | 30x | 75x
7️⃣ Семёрка: 25x | 50x | 100x
💎 Алмаз:   50x | 100x | 250x

<b>Специальные символы:</b>
🐶 Wild - заменяет любые символы (кроме бонуса)
🎁 Scatter - 3+ символа дают 5-15 бесплатных спинов

<b>Джекпот:</b> {JACKPOT}₿ за 5 бриллиантов на любой линии
    """.format(JACKPOT=JACKPOT)
    
    await callback.message.edit_text(
        paytable_text,
        reply_markup=get_paytable_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "bonuses")
async def show_bonuses(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    
    bonuses_text = f"""
🎁 <b>БОНУСНЫЕ ВОЗМОЖНОСТИ</b>

У вас есть:
✨ <b>Бонусные спины:</b> {user['bonuses']}

Бонусные спины позволяют играть бесплатно с текущей ставкой!

<b>Как получить больше бонусов?</b>
- Выпавшие комбинации с 3+ символами 🎁
- Каждые {FREE_SPINS_AFTER} спинов вы получаете +1 спин
- Крупные выигрыши иногда приносят бонусы
- Ежедневный бонус (/bonus)
- Приглашайте друзей (/referral)
- Повышение уровня
    """
    
    await callback.message.edit_text(
        bonuses_text,
        reply_markup=get_paytable_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "leaders")
async def show_leaders(callback: types.CallbackQuery):
    # Собираем топ игроков
    top_players = sorted(
        [(user_id, data["balance"]) for user_id, data in user_data.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    leaders_text = "<b>🏆 ТОП-10 ИГРОКОВ</b>\n\n"
    for i, (user_id, balance) in enumerate(top_players):
        try:
            user = await bot.get_chat(user_id)
            name = user.first_name or user.username
            leaders_text += f"{i+1}. {name} - {balance}₿\n"
        except:
            leaders_text += f"{i+1}. Игрок #{user_id} - {balance}₿\n"
    
    leaders_text += "\n💡 Играйте чаще, чтобы попасть в топ!"
    
    await callback.answer(leaders_text, show_alert=True)

@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    
    win_percentage = user['total_wins'] / user['total_spins'] * 100 if user['total_spins'] > 0 else 0
    
    stats_text = f"""
📊 <b>ВАША СТАТИСТИКА</b>

💰 <b>Баланс:</b> {user['balance']}₿
🎁 <b>Бонусные спины:</b> {user['bonuses']}
🏅 <b>Уровень:</b> {user['level']} (Опыт: {user['experience']}/{LEVEL_EXPERIENCE[user['level']] if user['level'] < len(LEVEL_EXPERIENCE) else 'MAX'})

🎰 <b>Всего спинов:</b> {user['total_spins']}
🏆 <b>Победных спинов:</b> {user['total_wins']}
📈 <b>Процент побед:</b> {win_percentage:.1f}%

<b>Самый большой выигрыш:</b> {user.get('biggest_win', 0)}₿
<b>Текущая ставка:</b> {user['current_bet']}₿
<b>Приглашено друзей:</b> {user['referrals']}
<b>Достижений:</b> {len(user.get('achievements', []))}/{len(ACHIEVEMENTS)}
    """
    
    await callback.answer(stats_text, show_alert=True)

@dp.callback_query(lambda c: c.data == "achievements")
async def show_achievements(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    achievements = user.get("achievements", [])
    
    achievements_text = "<b>🏅 ВАШИ ДОСТИЖЕНИЯ</b>\n\n"
    
    if not achievements:
        achievements_text += "😢 У вас пока нет достижений\nИграйте больше, чтобы получить их!"
    else:
        for achievement in achievements:
            ach_data = ACHIEVEMENTS[achievement]
            achievements_text += f"{ach_data['emoji']} <b>{ach_data['name']}</b>\n"
    
    achievements_text += "\n\n<b>ДОСТУПНЫЕ ДОСТИЖЕНИЯ:</b>\n"
    for key, ach in ACHIEVEMENTS.items():
        if key not in achievements:
            achievements_text += f"🔒 {ach['name']} - {ach['reward']}₿\n"
    
    await callback.message.edit_text(
        achievements_text,
        reply_markup=get_achievements_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def show_help(callback: types.CallbackQuery):
    help_text = f"""
❓ <b>ПОМОЩЬ ПО ИГРЕ</b>

🎰 <b>Как играть?</b>
1. Установите ставку с помощью кнопок ➖/➕
2. Нажмите "🎰 Крутить"
3. Следите за выпавшими комбинациями

💰 <b>Пополнение баланса</b>
- Ежедневный бонус: /bonus
- Приглашайте друзей: /referral
- Уровни и достижения
- Бесплатные спины

⚙️ <b>Техническая поддержка</b>
Если у вас возникли проблемы, обратитесь к администратору.

🎯 <b>Особенности игры</b>
- Джекпот: {JACKPOT}₿
- Максимальная ставка: {MAX_BET}₿
- Бесплатные спины каждые {FREE_SPINS_AFTER} игр
    """
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_help_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сначала начните игру с /start", show_alert=True)
        return
    
    user = user_data[user_id]
    
    main_text = f"""
🎰 <b>DOG HOUSE SLOTS</b> 🐶

💰 <b>Баланс:</b> {user['balance']}₿
🎁 <b>Бонусные спины:</b> {user['bonuses']}
🏅 <b>Уровень:</b> {user['level']}
🎯 <b>Текущая ставка:</b> {user['current_bet']}₿

Выберите действие:
    """
    
    await callback.message.edit_text(
        main_text,
        reply_markup=get_main_keyboard(user_id)
    )
    await callback.answer()

@dp.message(Command("bonus"))
async def daily_bonus(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer("Сначала начните игру с /start")
        return
    
    user = user_data[user_id]
    today = datetime.date.today()
    
    if user.get("last_bonus") == str(today):
        await message.answer("🚫 Вы уже получали бонус сегодня!\nПриходите завтра.")
        return
    
    bonus_amount = DAILY_BONUS * user["level"]
    user["balance"] += bonus_amount
    user["last_bonus"] = str(today)
    
    await message.answer(
        f"🎁 <b>Вы получили ежедневный бонус!</b>\n"
        f"💰 +{bonus_amount}₿ (x{user['level']} за уровень)\n"
        f"💳 Теперь ваш баланс: {user['balance']}₿"
    )

@dp.message(Command("referral"))
async def referral_info(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer("Сначала начните игру с /start")
        return
    
    await message.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка:\n"
        f"<code>https://t.me/{bot.username}?start=ref_{user_id}</code>\n\n"
        f"💸 За каждого приглашённого друга:\n"
        f"- Вы получаете <b>{REFERRAL_BONUS}₿</b>\n"
        f"- Друг получает <b>{REFERRAL_BONUS}₿</b>\n\n"
        f"💰 Уже приглашено: {user_data[user_id]['referrals']} человек",
        reply_markup=get_referral_keyboard(user_id)
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
