from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import dotenv_values
from db.postgre import cursor
import json
import asyncio

from telebot import types
# variables in .env file
dotenv_variables = {
    **dotenv_values()
}

bot = AsyncTeleBot(dotenv_variables['BOT_TOKEN'])


@bot.message_handler(commands=['start'])
async def start(message):
    await cursor.connect()
    try:
        user_id = await cursor.check_user_id(user_id=message.chat.id)
        if user_id:
            # Вызов меню
            await main(message=message)
        else:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Английский', callback_data='en')
            btn2 = types.InlineKeyboardButton('Русский', callback_data='ru')
            btn3 = types.InlineKeyboardButton('Украинский', callback_data='uk')
            markup.add(btn1, btn2, btn3)
            text = "Пожалуйста, выберете язык"
            await bot.send_message(message.chat.id, text=text, reply_markup=markup)
    finally:
        await cursor.close()


@bot.callback_query_handler(func=lambda call: call.data in ['en', 'ru', 'uk'])
async def language_callback_handler(call):
    # Обработка выбора языка здесь
    selected_language = call.data
    user_id = call.message.chat.id

    # Выбор файла с текстом
    language_data = await load_language_file(selected_language)

    # Сохраняем или обновляем выбранный язык пользователя в базе данных
    await cursor.connect()
    try:
        existing_user = await cursor.check_user_id(user_id)

        if existing_user:
            # Если пользователь уже существует, обновляем его язык
            await cursor.update_user(user_id=user_id, language=selected_language)
            text = language_data["message"]["change_language"] + f"<b>{language_data["language"][selected_language]}</b>"
            await bot.send_message(user_id, text=text, parse_mode='HTML')
        else:
            # Если пользователь новый, добавляем его в базу данных с выбранным языком
            await cursor.add_user(user_id, 
                            language=selected_language, 
                            nickname= call.message.chat.username if call.message.chat.username else None,
                            telegram_chat_id=call.message.chat.id
            )
            text = language_data["message"]["selected_language"] + f"<b>{language_data["language"][selected_language]}</b>"
            await bot.send_message(user_id, text=text, parse_mode='HTML')
    finally:
        await cursor.close()
        # Вызов меню
        await main(message=call)


async def main(message):
    # Проверка на Message или CallbackQuery
    user_id = message.chat.id if isinstance(message, types.Message) else message.from_user.id
    await cursor.connect()
    try:
        # Получаем код языка из бд
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)
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
        await bot.send_message(user_id, text, parse_mode='html', reply_markup=markup)

    finally:
       await cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Info", "Инфо", "Інфо"])
async def get_info(message):

    user_id = message.chat.id 
    await cursor.connect()
    try:
        # Получаем метод оплаты пользователя
        payment_method = await cursor.get_payment_method(user_id=user_id)

        language_code = await cursor.get_user_language(user_id=user_id)
        # Загружаем файл с данными на определенном языке
        language_data = await load_language_file(language_code=language_code)

        # Формируем текст сообщения с информацией о методе оплаты
        text = f"{language_data['message']['info_message']} - {payment_method}"

        # Отправляем сообщение пользователю
        await bot.send_message(message.chat.id, text=text, parse_mode='html')

    except Exception as e:
        # Обработка исключений при работе с базой данных или отправке сообщения
        print(f"An error occurred: {e}")

    finally:
        # В любом случае закрываем соединение с базой данных
        await cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Help", "Помощь", "Допомога"])
async def get_help(message):
    user_id = message.chat.id 
    await cursor.connect()
    try:
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)
        text = language_data["message"]["help_message"]
        await bot.send_message(message.chat.id, text=text)

    finally:
        await cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Statistics", "Статистика", "Статистика"])
async def get_statistic(message):
    user_id = message.chat.id
    await cursor.connect()
    try:
        
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)
        count = await cursor.get_count_records()
        
        all_statistic = language_data["button_statistic"]["all_statistic"]
        region_statistic = language_data["button_statistic"]["region_statistic"]
        number_of_users = language_data["button_statistic"]["number_of_users"]

        text = f"""- {all_statistic}: \n- {region_statistic}: \n- {number_of_users}: {count}"""
        await bot.send_message(message.chat.id, text=text, parse_mode='HTML')

    finally:
        await cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Language", "Язык", "Мова"])
async def change_language(message):
    
    user_id = message.chat.id
    await cursor.connect()
    try:
        # Получаем код языка из бд
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(language_data["language_button"]["en"], callback_data='en')
        btn2 = types.InlineKeyboardButton(language_data["language_button"]["ru"], callback_data='ru')
        btn3 = types.InlineKeyboardButton(language_data["language_button"]["uk"], callback_data='uk')
        markup.add(btn1, btn2, btn3)

        text = language_data["message"]["language_selection_message"]
        await bot.send_message(message.chat.id, text=text, reply_markup=markup)

    finally:
        await cursor.close()


@bot.message_handler(func=lambda message: message.text in ["Activate", "Активировать", "Активувати"])
async def get_activate(message):
    user_id = message.chat.id
    await cursor.connect()
    try:
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)
        text = f"<b>{language_data['message']['chose_region_message']}</b>"
    
        # Создание инлайн-кнопок для каждого региона
        markup = types.InlineKeyboardMarkup(row_width=2)  # Определение ширины строки
        regions = language_data['regions_spain']
        for region_id, region_name in regions.items():
            button = types.InlineKeyboardButton(region_name, callback_data=region_id)
            markup.add(button)
        await bot.send_message(user_id, text, parse_mode='html', reply_markup=markup)

    finally:
        await cursor.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith('region'))
async def handle_region_callback(call):
    user_id = call.from_user.id
    await cursor.connect()
    try:
        language_code = await cursor.get_user_language(user_id=user_id)
        language_data = await load_language_file(language_code=language_code)
    
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(language_data["price"]["price_button1"], callback_data='en')
        btn2 = types.InlineKeyboardButton(language_data["price"]["price_button1"], callback_data='en')
        markup.add(btn1, btn2)

        text = language_data["message"]["price_message"] + f"<b>{language_data['regions_spain'][call.data]}</b>"
        await bot.send_message(user_id, text=text, reply_markup=markup, parse_mode='html')
    finally:
        await cursor.close()


async def load_language_file(language_code):
    file_path = f"language/{language_code}.json"
    with open(file_path, 'r', encoding='utf-8') as file:
        language_data = json.load(file)
    return language_data


if __name__ == '__main__':
    asyncio.run(bot.polling())