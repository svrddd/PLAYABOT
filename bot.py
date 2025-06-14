import logging
import asyncio
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    KeyboardButton, 
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    FSInputFile
)

# --- Начало файла — параметры заданы вручную ---
BOT_TOKEN = "7621100705:AAHJ7R4N4ihthLUjV7cvcP95WrAo4GQOvl8"  # Вставьте сюда ваш токен
ADMIN_IDS = [2105766790, 523962812]  # Вставьте сюда ID администраторов через запятую
# --- Конец файла — параметры заданы вручную ---

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Пути к файлам
DB_PATH = "coffee_shop.db"
IMAGES_DIR = "images"

# Создаем директорию для изображений, если она не существует
os.makedirs(IMAGES_DIR, exist_ok=True)

# Класс для работы с базой данных
class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        
    def setup(self):
        # Создание необходимых таблиц, если они не существуют
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            image_path TEXT
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_path TEXT,
            available BOOLEAN DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            status TEXT NOT NULL,
            total_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_method TEXT,
            pickup_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT NOT NULL,
            rating INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        # Добавляем базовые категории, если их нет
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            categories = [
                ("Кофе", "Различные виды кофе", "coffee.jpg"),
                ("Напитки", "Разнообразные чайные напитки", "tea.jpg"),
                ("Еда", "Сладости и выпечка", "desserts.jpg"),
            ]
            self.cursor.executemany("INSERT INTO categories (name, description, image_path) VALUES (?, ?, ?)", categories)
            # Добавляем базовые продукты
            products = [
                (1, "Американо 200мл", "Классический черный кофе", 200, "americano.jpg", 1),
                (1, "Капучино 200мл", "Кофе с молочной пенкой", 230, "cappuccino.jpg", 1),
                (1, "Латте 300мл", "Кофе с молоком", 260, "latte.jpg", 1),
                (2, "Милкшейк Шоколад", "Освежающий зеленый чай", 300, "green_tea.jpg", 1),
                (2, "Милкшейк Шоколад", "Крепкий черный чай", 300, "black_tea.jpg", 1),
                (3, "Пончик Шоколад", "Нежный десерт с творожной начинкой", 180, "cheesecake.jpg", 1),
                (3, "Круассан Классический", "Хрустящая выпечка", 180, "croissant.jpg", 1),
                (4, "Сэндвич с курицей", "Сэндвич с куриным филе", 180, "chicken_sandwich.jpg", 1)
            ]
            self.cursor.executemany("INSERT INTO products (category_id, name, description, price, image_path, available) VALUES (?, ?, ?, ?, ?, ?)", products)
        self.conn.commit()
            
    def register_user(self, user_id, username, full_name, phone=None):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name, phone) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, phone)
        )
        self.conn.commit()
        
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()
        
    def get_categories(self):
        self.cursor.execute("SELECT id, name, description, image_path FROM categories")
        return self.cursor.fetchall()
        
    def get_products_by_category(self, category_id):
        self.cursor.execute(
            "SELECT id, name, description, price, image_path FROM products WHERE category_id = ? AND available = 1",
            (category_id,)
        )
        return self.cursor.fetchall()
        
    def get_product_by_id(self, product_id):
        self.cursor.execute(
            "SELECT id, name, description, price, image_path FROM products WHERE id = ?",
            (product_id,)
        )
        return self.cursor.fetchone()
        
    def create_order(self, user_id, cart, payment_method, pickup_time):
        total_price = sum(item['price'] * item['quantity'] for item in cart)
        # Создаем заказ
        self.cursor.execute(
            "INSERT INTO orders (user_id, status, total_price, payment_method, pickup_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, "новый", total_price, payment_method, pickup_time)
        )
        order_id = self.cursor.lastrowid
        # Добавляем позиции заказа
        for item in cart:
            self.cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item['product_id'], item['quantity'], item['price'])
            )
        self.conn.commit()
        return order_id
        
    def get_order_details(self, order_id):
        self.cursor.execute(
            "SELECT id, user_id, status, total_price, created_at, payment_method, pickup_time FROM orders WHERE id = ?",
            (order_id,)
        )
        order = self.cursor.fetchone()
        if not order:
            return None
        self.cursor.execute(
            """
            SELECT oi.product_id, p.name, oi.quantity, oi.price 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = ?
            """,
            (order_id,)
        )
        items = self.cursor.fetchall()
        return {
            "id": order[0],
            "user_id": order[1],
            "status": order[2],
            "total_price": order[3],
            "created_at": order[4],
            "payment_method": order[5],
            "pickup_time": order[6],
            "items": items
        }
        
    def add_review(self, user_id, text, rating):
        self.cursor.execute(
            "INSERT INTO reviews (user_id, text, rating) VALUES (?, ?, ?)",
            (user_id, text, rating)
        )
        self.conn.commit()
        
    def close(self):
        self.conn.close()

# Инициализация базы данных
db = Database(DB_PATH)
db.setup()

# Состояния для FSM
class OrderStates(StatesGroup):
    choosing_category = State()
    choosing_product = State()
    adding_to_cart = State()
    viewing_cart = State()
    checkout = State()
    payment_method = State()
    pickup_time = State()
    confirming_order = State()

class FeedbackStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_rating = State()

class ContactAdminStates(StatesGroup):
    waiting_for_message = State()

class RegistrationStates(StatesGroup):
    waiting_for_phone = State()

# Функции для клавиатур
def get_main_keyboard():
    """Создает основную клавиатуру с главным меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Меню")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📝 Мои заказы")],
            [KeyboardButton(text="⭐ Оставить отзыв"), KeyboardButton(text="📨 Связаться с администратором")],
            [KeyboardButton(text="📍 Где нас найти"), KeyboardButton(text="📣 Наш канал")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_categories_keyboard(categories):
    """Создает клавиатуру со списком категорий"""
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(text=category[1], callback_data=f"category:{category[0]}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_products_keyboard(products, category_id):
    """Создает клавиатуру со списком продуктов в категории"""
    buttons = []
    for product in products:
        buttons.append([InlineKeyboardButton(text=f"{product[1]} - {product[3]} ₽", callback_data=f"product:{product[0]}")])
    buttons.append([InlineKeyboardButton(text="🔙 К категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_keyboard(product_id, in_cart=False):
    """Создает клавиатуру для конкретного продукта"""
    buttons = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease:{product_id}"),
            InlineKeyboardButton(text="1", callback_data="quantity"),
            InlineKeyboardButton(text="➕", callback_data=f"increase:{product_id}")
        ],
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart:{product_id}")]
    ]
    if in_cart:
        buttons.append([InlineKeyboardButton(text="🗑 Удалить из корзины", callback_data=f"remove_from_cart:{product_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cart_keyboard():
    """Создает клавиатуру для корзины"""
    buttons = [
        [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🔙 Вернуться к меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_method_keyboard():
    """Создает клавиатуру для выбора способа оплаты"""
    buttons = [
        [InlineKeyboardButton(text="💵 Наличными при получении", callback_data="payment:cash")],
        [InlineKeyboardButton(text="💳 Картой", callback_data="payment:card")],
        [InlineKeyboardButton(text="📱 СБП", callback_data="payment:sbp")],
        [InlineKeyboardButton(text="🔙 Назад к корзине", callback_data="back_to_cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_pickup_time_keyboard():
    """Создает клавиатуру для выбора времени получения"""
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    # Округляем до ближайших 15 минут
    if current_minute < 10:
        next_minute = 10
    elif current_minute < 30:
        next_minute = 30
    elif current_minute < 40:
        next_minute = 40
    else:
        next_minute = 0
        current_hour = (current_hour + 1) % 24
    times = []
    for i in range(4):  # Предлагаем 4 временных слота
        hour = (current_hour + ((next_minute + i * 10) // 60)) % 24
        minute = (next_minute + i * 10) % 60
        time_str = f"{hour:02d}:{minute:02d}"
        times.append(time_str)
    buttons = []
    for time_str in times:
        buttons.append([InlineKeyboardButton(text=time_str, callback_data=f"time:{time_str}")])
    buttons.append([InlineKeyboardButton(text="🕒 Как можно скорее", callback_data="time:asap")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад к выбору оплаты", callback_data="back_to_payment")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_order_keyboard():
    """Создает клавиатуру для подтверждения заказа"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rating_keyboard():
    """Создает клавиатуру для выставления рейтинга"""
    buttons = []
    for rating in range(1, 6):
        buttons.append(InlineKeyboardButton(text="⭐" * rating, callback_data=f"rating:{rating}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# --- Обработчики и функции дальше идут без изменений, они остаются как есть ---
# Обработчик для всех сообщений
@dp.message_handler()
async def handle_any_message(message: types.Message):
    await message.answer("Я вас не понял. Используйте меню или команды.")

# Обработчик для всех callback-запросов
@dp.callback_query_handler()
async def handle_callback(callback: types.CallbackQuery):
    await callback.answer()
    print(f"Callback data: {callback.data}")

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
