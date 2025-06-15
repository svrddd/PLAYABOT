import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Введите сюда ваш токен
TOKEN = "7621100705:AAHJ7R4N4ihthLUjV7cvcP95WrAo4GQOvl8"
# Введите сюда ваш Telegram ID (числом)
ADMIN_ID = 2105766790

logging.basicConfig(level=logging.INFO)

# Создаем экземпляр бота
bot = Bot(token=TOKEN)

# Создаем диспетчер с привязкой к боту
dp = Dispatcher()

# Главное меню
main_menu = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🍽 Меню")],
        [types.KeyboardButton(text="🛒 Корзина"), types.KeyboardButton(text="📝 Мои заказы")],
        [types.KeyboardButton(text="⭐ Оставить отзыв")],
        [types.KeyboardButton(text="📨 Связаться с администратором")],
        [types.KeyboardButton(text="📍 Где нас найти")],
    ],
    resize_keyboard=True
)

# Категории и товары
menu_items = {
    "Кофе": ["Американо", "Капучино", "Латте"],
    "Напитки": ["Чай", "Морс"],
    "Десерты": ["Пончик", "Торт"]
}
cart = []

# Обработчик /start
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=main_menu)

# Обработка всех сообщений
@dp.message()
async def handle_message(message: types.Message):
    text = message.text

    if text == "🍽 Меню":
        await message.answer("Выберите категорию:", reply_markup=category_keyboard())
    elif text == "🛒 Корзина":
        await show_cart(message)
    elif text == "⭐ Оставить отзыв":
        await message.answer("Напишите ваш отзыв или предложение:")
    elif text == "📨 Связаться с администратором":
        await message.answer("Напишите ваше сообщение админу:")
        await bot.send_message(ADMIN_ID, f"Сообщение от пользователя {message.from_user.id}:\n{message.text}")
    elif text == "📍 Где нас найти":
        await message.answer("Наш адрес: г. Москва, ул. Ленина, дом 1.\nНа карте:", reply_markup=location_keyboard())
    elif text == "🔙 Назад" or text == "🔙":
        await message.answer("Главное меню", reply_markup=main_menu)
    elif text in ["🧹 Очистить корзину", "✅ Оформить заказ"]:
        await handle_cart_buttons(message)
    elif text == "Показать на карте":
        await message.answer_location(latitude=55.7558, longitude=37.6173)
    elif text in sum(menu_items.values(), []):  # товар
        cart.append(text)
        await message.answer(f"Добавлено в корзину: {text}")
    else:
        await message.answer("Я вас не понял. Используйте меню.")

def category_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=cat)] for cat in menu_items.keys()] + [[types.KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

async def show_cart(message: types.Message):
    if not cart:
        await message.answer("Ваша корзина пуста.")
        return
    txt = "Ваша корзина:\n" + "\n".join(cart)
    await message.answer(txt, reply_markup=cart_keyboard())

def cart_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧹 Очистить корзину"), types.KeyboardButton(text="✅ Оформить заказ")],
            [types.KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

async def handle_cart_buttons(message: types.Message):
    txt = message.text
    if txt == "🧹 Очистить корзину":
        cart.clear()
        await message.answer("Корзина очищена.")
    elif txt == "✅ Оформить заказ":
        if not cart:
            await message.answer("Корзина пуста.")
            return
        order_text = "Новый заказ:\n" + "\n".join(cart)
        await bot.send_message(ADMIN_ID, order_text)
        await message.answer("Ваш заказ отправлен админу. Спасибо!")
        cart.clear()

def location_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Показать на карте", request_location=True)]],
        resize_keyboard=True
    )

# Запуск бота
async def main():
    # Запускаем бота и диспетчер
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

