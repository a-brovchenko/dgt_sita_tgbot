from dotenv import dotenv_values
import os
import telebot
from telebot import types
from db.postgre import cursor
import json

# variables in .env file
dotenv_variables = {
    **dotenv_values()
}


bot = telebot.TeleBot(dotenv_variables['BOT_TOKEN'])


@bot.message_handler(commands=['start'])
def start(message):

    cursor.connect()
    user_id = cursor.check_user_id(user_id=message.chat.id)
    cursor.close()
    if user_id:
        # Вызов меню
        main(message=message)
    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Английский', callback_data='en')
        btn2 = types.InlineKeyboardButton('Русский', callback_data='ru')
        btn3 = types.InlineKeyboardButton('Украинский', callback_data='uk')
        markup.add(btn1, btn2, btn3)
        text = "Пожалуйста, выберете язык"
        bot.send_message(message.chat.id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['en', 'ru', 'uk'])
def language_callback_handler(call):
    # Обработка выбора языка здесь
    selected_language = call.data
    user_id = call.message.chat.id

    # Выбор файла с текстом
    language_data = load_language_file(selected_language)

    # Сохраняем или обновляем выбранный язык пользователя в базе данных
    cursor.connect()
    existing_user = cursor.check_user_id(user_id)

    if existing_user:
        # Если пользователь уже существует, обновляем его язык
        cursor.update_user(user_id=user_id, language=selected_language)
        bot.send_message(user_id, f"{language_data["message"]["change_language"]}: {selected_language}")
    else:
        # Если пользователь новый, добавляем его в базу данных с выбранным языком
        cursor.add_user(user_id, 
                        language=selected_language, 
                        nickname= call.message.chat.username if call.message.chat.username else None,
                        telegram_chat_id=call.message.chat.id
        )
        text = language_data["message"]["selected_language"]
        bot.send_message(user_id, f"{text}: {selected_language}")
    cursor.close()
    # Вызов меню
    main(message=call)


def main(message):
    # Проверка на Message или CallbackQuery
    user_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
    cursor.connect()
    # Получаем код языка из бд
    language_code = cursor.get_user_language(user_id=user_id)
    cursor.close()
    # Получаем файл с определенным языком
    language_data = load_language_file(language_code=language_code)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton(language_data["button"]["activate_button"])
    btn2 = types.KeyboardButton(language_data["button"]["info_button"])
    btn3 = types.KeyboardButton(language_data["button"]["statistics_button"])

    btn4 = types.KeyboardButton(language_data["button"]["help_button"])
    btn5 = types.KeyboardButton(language_data["button"]["language_button"])
    btn6 = types.KeyboardButton(language_data["button"]["stop_button"])

    markup.add(btn1, btn2, btn3)
    markup.add(btn4, btn5, btn6)
    text = language_data["message"]["start_message"]
    bot.send_message(user_id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["Info", "Инфо", "Інфо"])
def get_info(message):

    user_id = message.chat.id 
    cursor.connect()
    try:
        # Получаем метод оплаты пользователя
        payment_method = cursor.get_payment_method(user_id=user_id)

        language_code = cursor.get_user_language(user_id=user_id)
        # Загружаем файл с данными на определенном языке
        language_data = load_language_file(language_code=language_code)

        # Формируем текст сообщения с информацией о методе оплаты
        text = f"{language_data['message']['info_message']} - {payment_method}"

        # Отправляем сообщение пользователю
        bot.send_message(message.chat.id, text=text, parse_mode='html')

    except Exception as e:
        # Обработка исключений при работе с базой данных или отправке сообщения
        print(f"An error occurred: {e}")

    finally:
        # В любом случае закрываем соединение с базой данных
        cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Help", "Помощь", "Допомога"])
def get_help(message):
    user_id = message.chat.id 
    cursor.connect()
    language_code = cursor.get_user_language(user_id=user_id)
    language_data = load_language_file(language_code=language_code)
    cursor.close()

    text = language_data["message"]["help_message"]
    bot.send_message(message.chat.id, text=text)


def load_language_file(language_code):
    file_path = f"language/{language_code}.json"
    with open(file_path, 'r', encoding='utf-8') as file:
        language_data = json.load(file)
        return language_data

if __name__ == "__main__":
    bot.polling(none_stop=True)