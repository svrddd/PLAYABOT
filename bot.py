import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import reply_keyboard, keyboard

# Ваш токен бота
TOKEN = "7621100705:AAHJ7R4N4ihthLUjV7cvcP95WrAo4GQOvl8"

# ID администратора (замените на свой)
ADMIN_ID = 2105766790

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍽 Меню")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📝 Мои заказы")],
        [KeyboardButton(text="⭐ Оставить отзыв")],
        [KeyboardButton(text="📨 Связаться с администратором")],
        [KeyboardButton(text="📍 Где нас найти")]
    ],
    resize_keyboard=True
)

# Простое меню товаров
menu_items = {
    "Кофе": ["Американо", "Капучино", "Латте"],
    "Напитки": ["Чай", "Морс"],
    "Десерты": ["Пончик", "Торт"]
}

cart = []

# Обработчик главного меню
@dp.message_handler(commands=["start"])
@dp.message_handler(lambda message: message.text in ["🍽 Меню", "🛒 Корзина", "📝 Мои заказы",
                                                          "⭐ Оставить отзыв", "📨 Связаться с администратором",
                                                          "📍 Где нас найти"])
async def handle_main_menu(message: types.Message):
    text = message.text
    if text == "🍽 Меню":
        # Показать категории
        await message.answer("Выберите категорию:", reply_markup=category_keyboard())
    elif text == "🛒 Корзина":
        await show_cart(message)
    elif text == "⭐ Оставить отзыв":
        await message.answer("Напишите ваш отзыв или предложение:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_review")
    elif text == "📨 Связаться с администратором":
        await message.answer("Напишите ваше сообщение админу:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_admin_message")
    elif text == "📍 Где нас найти":
        await message.answer("Наш адрес: г. Москва, ул. Ленина, дом 1.\nНа карте:", reply_markup=location_keyboard())

# Категории
def category_keyboard():
    buttons = [
        [KeyboardButton(text="Кофе")],
        [KeyboardButton(text="Напитки")],
        [KeyboardButton(text="Десерты")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Обработка выбора категории
@dp.message_handler(lambda message: message.text in ["Кофе", "Напитки", "Десерты"])
async def handle_category(message: types.Message):
    category = message.text
    items = menu_items.get(category, [])
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item)] for item in items] + [[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )
    await message.answer(f"{category}:", reply_markup=kb)

# Обработка выбора товара
@dp.message_handler(lambda message: True)
async def handle_product_or_back(message: types.Message):
    text = message.text
    if text == "🔙 Назад":
        await message.answer("Главное меню", reply_markup=main_menu)
        return
    # Добавление в корзину
    cart.append(text)
    await message.answer(f"Добавлено в корзину: {text}")

# Показываем корзину
async def show_cart(message):
    if not cart:
        await message.answer("Ваша корзина пуста.")
        return
    txt = "Ваша корзина:\n" + "\n".join(cart)
    await message.answer(txt, reply_markup=cart_keyboard())

def cart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧹 Очистить корзину"), KeyboardButton(text="✅ Оформить заказ")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

# Обработка кнопок корзины
@dp.message_handler(lambda message: message.text in ["🧹 Очистить корзину", "✅ Оформить заказ", "🔙"])
async def handle_cart_buttons(message: types.Message):
    if message.text == "🧹 Очистить корзину":
        cart.clear()
        await message.answer("Корзина очищена.")
    elif message.text == "✅ Оформить заказ":
        if not cart:
            await message.answer("Корзина пуста.")
            return
        # Отправляем заказ админу
        order_text = "Новый заказ:\n" + "\n".join(cart)
        await bot.send_message(ADMIN_ID, order_text)
        await message.answer("Ваш заказ отправлен админу. Спасибо!")
        cart.clear()
    elif message.text == "🔙":
        await message.answer("Главное меню", reply_markup=main_menu)

# Обработка отзывов
@dp.message_handler(state="waiting_review")
async def handle_review(message: types.Message):
    review = message.text
    # Можно сохранять отзывы куда-то
    await message.answer("Спасибо за отзыв!")
    await dp.current_state(user=message.from_user.id).set_state(None)

# Обработка сообщений для админского канала
@dp.message_handler(state="waiting_admin_message")
async def handle_admin_message(message: types.Message):
    text = message.text
    # Отправляем всем пользователям (здесь нужно хранить список)
    # Для примера отправим админу обратно
    await bot.send_message(ADMIN_ID, f"Сообщение от клиента:\n{text}")
    await message.answer("Сообщение отправлено админу.")
    await dp.current_state(user=message.from_user.id).set_state(None)

# Обработка контактов и местоположения
@dp.message_handler(commands=["location"])
async def send_location(message: types.Message):
    await message.answer("Наш адрес: г. Москва, ул. Ленина, дом 1.", reply_markup=location_keyboard())

def location_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(text="Показать на карте", request_location=True))
    return kb

# Обработка нажатия кнопки "Показать на карте"
@dp.message_handler(lambda message: message.text == "Показать на карте")
async def handle_location_request(message: types.Message):
    await message.answer_location(latitude=55.7558, longitude=37.6173)

# Обработка сообщений для связи с админом
@dp.message_handler(state="waiting_admin_message")
async def handle_admin_msg(message: types.Message):
    text = message.text
    await bot.send_message(ADMIN_ID, f"Сообщение от пользователя {message.from_user.id}:\n{text}")
    await message.answer("Ваше сообщение отправлено админу.")
    await dp.current_state(user=message.from_user.id).set_state(None)

# Обработка команд /help
@dp.message_handler(commands=["help"])
async def handle_help(message: types.Message):
    await message.answer("Это бот кофейни. Используйте меню для заказов, отзывов и связи с админом.")

# Обработка ошибок
@dp.errors_handler()
async def handle_errors(update, exception):
    print(f"Ошибка: {exception}")
    return True

# Запуск
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())

