import telebot
import psycopg2
from telebot import types

# Подключение к базе данных PostgreSQL
db_connection = psycopg2.connect(
    database="bd_bot",
    user="postgres",
    password="password",
    host="localhost",
    port="5433"
)
db_cursor = db_connection.cursor()

# Токен вашего бота
TOKEN = '7660126710:AAGS9Dd2C4PWT0Rio08jXxdWDktwXGCmTaI'
bot = telebot.TeleBot(TOKEN)

# Структура данных для вопросов и их сохранения
user_preferences = {}

questions = [
    {"key": "category", "text": "Какая категория заведения вас интересует?",
     "options": ["Быстрое питание", "Кафе", "Кофейня", "Пиццерия", "Ресторан"]},
    {"key": "order_method", "text": "Как вы предпочитаете получить заказ?",
     "options": ["Самовывоз в любое время", "Требуется курьер", "Требуется онлайн запись"]},
    {"key": "payment_method", "text": "Как вы предпочитаете оплачивать заказ?",
     "options": ["Наличными", "Картой", "СБП", "SberPay"]},
    {"key": "cuisine", "text": "Какую кухню вы предпочитаете?",
     "options": ["Европейская", "Домашняя", "Русская", "Смешанная", "Итальянская", "Кавказская"]},
    {"key": "price", "text": "На какие цены блюд вы рассчитываете?",
     "options": ["Низкие", "Средние", "Выше среднего", "Высокие"]},
    {"key": "schedule", "text": "Какой график работы заведения вас устроит?",
     "options": ["Открыто сейчас", "Открыто в указанное время"]},
    {"key": "outdoor", "text": "Вы предпочитаете расположиться на улице?",
     "options": ["Да", "Нет"]},
    {"key": "rating", "text": "Какой рейтинг заведения вас интересует?",
     "options": ["Низкие", "Средние", "Высокие"]},
    {"key": "accessibility", "text": "Интересует ли вас доступность для инвалидов?",
     "options": ["Да", "Нет"]},
    {"key": "parking", "text": "Требуется ли парковка?",
     "options": ["Да", "Нет"]},
    {"key": "wifi", "text": "Нужен ли вам Wi-Fi?",
     "options": ["Да", "Нет"]}
]


# Начало диалога
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "👋 Добро пожаловать в *FoodFinderBot*! 🍴\n\n"
        "Я помогу вам найти идеальное место для обеда или ужина.\n"
        "Ответьте на несколько вопросов, и я предложу заведение, которое вам понравится.\n"
        "Чтобы начать, нажмите *'Далее'* или просто ответьте на первый вопрос. 😊"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

    user_preferences[message.chat.id] = {}
    ask_question(message, 0)


# Задать вопрос
def ask_question(message, question_index):
    if question_index < len(questions):
        question = questions[question_index]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for option in question['options']:
            markup.add(option)
        bot.send_message(message.chat.id, question['text'], reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: save_answer(msg, question_index))
    else:
        find_restaurant(message)


# Сохранить ответ
def save_answer(message, question_index):
    question_key = questions[question_index]["key"]
    user_preferences[message.chat.id][question_key] = message.text
    ask_question(message, question_index + 1)


# Поиск подходящего заведения
def find_restaurant(message):
    preferences = user_preferences.get(message.chat.id, {})
    query = """
        SELECT r.name, r.address
        FROM restaurants r
        JOIN categories c ON r.category_id = c.id
        JOIN cuisines cu ON r.cuisine_id = cu.id
        JOIN price_levels p ON r.price_level_id = p.id
        JOIN work_schedules w ON r.work_schedule_id = w.id
        WHERE c.name = %(category)s
        AND cu.name = %(cuisine)s
        AND p.name = %(price)s
        AND w.name = %(schedule)s
        AND r.parking = %(parking)s
        AND r.wifi = %(wifi)s
        AND r.rating = %(rating)s
        AND r.accessibility = %(accessibility)s
        LIMIT 1
    """
    params = {
        "category": preferences.get("category"),
        "cuisine": preferences.get("cuisine"),
        "price": preferences.get("price"),
        "schedule": preferences.get("schedule"),
        "parking": preferences.get("parking") == "Да",
        "wifi": preferences.get("wifi") == "Да",
        "rating": preferences.get("rating"),
        "accessibility": preferences.get("accessibility") == "Да"
    }

    db_cursor.execute(query, params)
    result = db_cursor.fetchone()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Попробовать снова")

    if result:
        bot.send_message(message.chat.id,
                         f"Мы нашли для вас заведение: {result[0]}, адрес: {result[1]}.",
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         "К сожалению, подходящих заведений не найдено.",
                         reply_markup=markup)

    bot.register_next_step_handler(message, restart)


# Начать поиск заново
def restart(message):
    if message.text == "Попробовать снова":
        user_preferences[message.chat.id] = {}
        ask_question(message, 0)
    else:
        bot.send_message(message.chat.id, "Введите 'Попробовать снова', чтобы начать поиск заново.")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)