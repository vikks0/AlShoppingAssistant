import os
import traceback
import telebot
from telebot import types
from dotenv import load_dotenv

from services.parser import get_reviews
from services.ai import analyze_reviews
from services.formatter import count_sentiments, format_result
from services.database import Database

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

db = Database()

WELCOME_TEXT = (
    "Привет! Я — *Анализатор отзывов*\n\n"
    "Помогаю принять решение о покупке,\n"
    "анализируя отзывы на товары с Wildberries\n\n"
    "Выберите действие:"
)


def create_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Оценить товар", callback_data="menu_analyze"),
        types.InlineKeyboardButton("Сравнить товары", callback_data="menu_compare"),
    )
    markup.add(types.InlineKeyboardButton("Моя история", callback_data="menu_history"))
    return markup


def create_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Назад", callback_data="menu_back"))
    return markup


@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_username"
    db.add_user(user_id, message.from_user.first_name, username)

    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=create_main_menu())


def show_section(call, title, body):
    text = title + "\n" + "━" * 24 + "\n\n" + body
    bot.edit_message_text(text, call.message.chat.id,
                         call.message.message_id, parse_mode="Markdown",
                         reply_markup=create_back_button())


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    chat_id = call.message.chat.id

    if data == "menu_analyze":
        show_section(call, "Оценка товара",
            "Отправьте мне ссылку на товар Wildberries,\n"
            "и я загружу отзывы и проанализирую их.\n\n"
            "Как это работает:\n"
            "1. Я загружу все доступные отзывы\n"
            "2. Посчитаю положительные и отрицательные\n"
            "3. ИИ выделит главные плюсы и минусы\n"
            "4. Дам рекомендацию\n\n"
            "Пример ссылки:\n"
            "`wildberries.ru/catalog/243744988/detail.aspx`\n\n"
            "Отправьте ссылку следующим сообщением:")

    elif data == "menu_compare":
        show_section(call, "Сравнение товаров",
            "Отправьте мне несколько ссылок на товары\n"
            "Wildberries одним сообщением (каждая ссылка\n"
            "с новой строки).\n\n"
            "Что я сделаю:\n"
            "1. Проанализирую каждый товар\n"
            "2. Сравню результаты\n"
            "3. Покажу плюсы и минусы каждого\n"
            "4. Сделаю итоговый вывод\n\n"
            "Пример:\n"
            "`wildberries.ru/catalog/111111/detail.aspx`\n"
            "`wildberries.ru/catalog/222222/detail.aspx`\n\n"
            "Отправьте ссылки следующим сообщением:")

    elif data == "menu_history":
        bot.answer_callback_query(call.id)

    elif data == "menu_back":
        bot.edit_message_text(WELCOME_TEXT, chat_id,
                             call.message.message_id, parse_mode="Markdown",
                             reply_markup=create_main_menu())

    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    if text.startswith('http') or text.startswith('www.'):
        lines = text.split('\n')
        wb_links = []
        for line in lines:
            line = line.strip()
            if line and is_wb_url(line):
                wb_links.append(line)

        if not wb_links:
            bot.send_message(chat_id,
                "Не найдено ссылок на Wildberries.\n\n"
                "Отправьте ссылку в формате:\n"
                "`wildberries.ru/catalog/12345678/detail.aspx`",
                parse_mode="Markdown", reply_markup=create_main_menu())
            return

        if len(wb_links) == 1:
            analyze_single(message, wb_links[0])
        else:
            bot.send_message(chat_id,
                "Слишком много ссылок.\n\n"
                "Можно сравнить максимум 5 товаров.\n"
                "Отправьте не более 5 ссылок.",
                reply_markup=create_main_menu())
    else:
        bot.send_message(chat_id,
            "Я не понял сообщение.\n\n"
            "Отправьте ссылку на товар Wildberries\n"
            "или нажмите кнопку ниже:",
            reply_markup=create_main_menu())


def analyze_single(message, url):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Загружаю отзывы с Wildberries...")

    try:
        reviews = get_reviews(url)

        if not reviews:
            bot.send_message(chat_id,
                "Не удалось загрузить отзывы.\n\n"
                "Возможно:\n"
                "- У товара ещё нет отзывов\n"
                "- Ссылка недействительна\n"
                "- Wildberries временно недоступен\n\n"
                "Попробуйте другой товар.",
                reply_markup=create_main_menu())
            return

        all_reviews = "\n\n".join(reviews)
        positive, negative = count_sentiments(reviews)

        bot.send_message(chat_id,
            "Загружено " + str(len(reviews)) + " отзывов.\nАнализирую с помощью ИИ...")

        gpt_result = analyze_reviews(all_reviews)
        final_result = format_result(gpt_result, len(reviews), positive, negative)

        bot.send_message(chat_id, final_result, reply_markup=create_main_menu())
        db.add_history(chat_id, "analyze", url)

    except Exception as e:
        traceback.print_exc()
        bot.send_message(chat_id,
            "Произошла ошибка: " + type(e).__name__ + "\n\n"
            "Попробуйте позже или отправьте другой товар.",
            reply_markup=create_main_menu())


def is_wb_url(url):
    return "wildberries.ru" in url


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
