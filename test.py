import unittest
from unittest.mock import MagicMock, patch
from main import *

class TestStartHandler(unittest.TestCase):

    @patch('main.bot')
    async def test_start_new_user(self, fake_bot):
        fake_message = MagicMock()
        fake_message.chat.id = 123456789 

        fake_cursor = MagicMock()
        fake_cursor.check_user_id.return_value = None

        await start(fake_message, cursor=fake_cursor)

        # вызов main
        fake_bot.send_message.assert_called_once()

        # Проверяем аргументы, переданные в функцию send_message
        args, kwargs = fake_bot.send_message.call_args
        chat_id, text, reply_markup = args
        self.assertEqual(chat_id, fake_message.chat.id)
        self.assertIn("Пожалуйста, выберете язык", text)
        self.assertIsNotNone(reply_markup)


    @patch('main.bot')
    async def test_start_existing_user(self, fake_bot):
        fake_message = MagicMock()
        fake_message.chat.id = 123456789  
        
        fake_cursor = MagicMock()
        fake_cursor.check_user_id.return_value = True

        await start(fake_message, cursor=fake_cursor)

        # вызов main
        fake_message.main.assert_called_once()


    @patch('main.bot')
    async def test_language_selection(self, fake_bot):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789 
        fake_message.text = '/start'

        fake_cursor = MagicMock()
        fake_cursor.check_user_id.return_value = None

        await start(fake_message, cursor=fake_cursor)

        fake_bot.send_message.assert_called_once()

        # Проверяем аргументы, переданные в функцию send_message
        args, kwargs = fake_bot.send_message.call_args
        chat_id, text, reply_markup = args
        self.assertEqual(chat_id, fake_message.chat.id)
        self.assertIn("Пожалуйста, выберете язык", text)
        self.assertIsNotNone(reply_markup)

        # Подготавливаем фейковое сообщение от пользователя с выбранным языком
        fake_message.text = 'Английский'

        # Вызываем обработчик второй раз
        await start(fake_message, cursor=fake_cursor)

        # Проверяем, что была вызвана функция send_message второй раз
        self.assertEqual(fake_bot.send_message.call_count, 2)

        args, kwargs = fake_bot.send_message.call_args
        chat_id, text, reply_markup = args
        self.assertEqual(chat_id, fake_message.chat.id)


    @patch('main.bot')
    async def test_multiple_calls(self, fake_bot):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789  
        fake_message.text = '/start'  

        fake_cursor = MagicMock()
        fake_cursor.check_user_id.return_value = None

        # вызов функции start дважды
        await start(fake_message, cursor=fake_cursor)
        await start(fake_message, cursor=fake_cursor)

        fake_message.main.assert_called_once()


class TestLanguageCallbackHandler(unittest.TestCase):

    @patch('db.postgre.cursor')
    @patch('main.bot')
    async def test_existing_user(self, fake_bot, fake_cursor):

        fake_call = MagicMock()
        fake_call.data = 'en'
        fake_call.message.chat.id = 123456789

        fake_cursor.check_user_id.return_value = True
        fake_cursor.update_user.return_value = None

        fake_language_data = {
            "message": {"change_language": "Language changed to ", "selected_language": "Selected language: "},
            "language": {"en": "English"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await language_callback_handler(fake_call)

        fake_cursor.update_user.assert_called_once_with(user_id=123456789, language='en')

        fake_bot.send_message.assert_called_once_with(123456789, text="Language changed to <b>English</b>", parse_mode='HTML')


    @patch('db.postgre.cursor')
    @patch('main.bot')
    async def test_new_user(self, fake_bot, fake_cursor):
        fake_call = MagicMock()
        fake_call.data = 'ru'
        fake_call.message.chat.id = 123456789 

        fake_cursor.check_user_id.return_value = False
        fake_cursor.add_user.return_value = None

        fake_language_data = {
            "message": {"change_language": "Language changed to ", "selected_language": "Selected language: "},
            "language": {"ru": "Russian"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await language_callback_handler(fake_call)

        fake_cursor.add_user.assert_called_once_with(
            user_id=987654321,
            language='ru',
            nickname=None,
            telegram_chat_id=123456789
        )

        fake_bot.send_message.assert_called_once_with(987654321, text="Selected language: <b>Russian</b>", parse_mode='HTML')



class TestMainFunction(unittest.TestCase):
    @patch('db.postgre.cursor')
    @patch('main.bot')
    async def test_existing_user_keyboard(self, fake_bot, fake_cursor):
        fake_message = MagicMock()
        fake_message.chat.id = 123456789  

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "button": {
                "activate_button": "Activate",
                "info_button": "Info",
                "statistics_button": "Statistics",
                "help_button": "Help",
                "language_button": "Language",
                "stop_button": "Stop"
            },
            "message": {
                "start_message": "Welcome!"
            }
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await main(fake_message)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            "Welcome!",
            parse_mode='html',
            reply_markup=MagicMock().add.return_value
        )


class TestGetInfoFunction(unittest.TestCase):
    @patch('your_module.cursor')
    @patch('your_module.bot')
    async def test_existing_user_payment_info(self, fake_bot, fake_cursor):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789 
        fake_message.text = "Info"

        fake_cursor.get_payment_method.return_value = "test"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "message": {"info_message": "Your payment method is"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        # Вызываем функцию get_info
        await get_info(fake_message)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            "Your payment method is - test",
            parse_mode='html'
        )


class TestGetHelpFunction(unittest.TestCase):
    @patch('db.cursor.cursor')
    @patch('main.bot')
    async def test_existing_user_help_message(self, fake_bot, fake_cursor):
  
        fake_message = MagicMock()
        fake_message.chat.id = 123456789 
        fake_message.text = "Help"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "message": {"help_message": "This is a help message."}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await get_help(fake_message)

        # Проверяем, что отправлено правильное сообщение с помощью
        fake_bot.send_message.assert_called_once_with(
            123456789,
            "This is a help message."
        )


class TestGetStatisticFunction(unittest.TestCase):
    @patch('db.cursor.cursor')
    @patch('main.bot')
    async def test_existing_user_statistic_message(self, fake_bot, fake_cursor):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789  
        fake_message.text = "Statistics"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "button_statistic": {
                "all_statistic": "All statistics",
                "region_statistic": "Region statistics",
                "number_of_users": "Number of users"
            }
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        fake_cursor.get_count_records.return_value = 100

        await get_statistic(fake_message)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            f"- All statistics: \n- Region statistics: \n- Number of users: 100",
            parse_mode='HTML'
        )


class TestChangeLanguageFunction(unittest.TestCase):

    @patch('db.cursor.cursor')
    @patch('main.bot')
    async def test_send_language_selection_message(self, fake_bot, fake_cursor):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789  
        fake_message.text = "Language"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "message": {"language_selection_message": "Please select your language"},
            "language_button": {"en": "English", "ru": "Russian", "uk": "Ukrainian"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await change_language(fake_message)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            "Please select your language",
            reply_markup=MagicMock()
        )


class TestGetActivateFunction(unittest.TestCase):
    @patch('db.cursor.cursor')
    @patch('main.bot')
    async def test_send_region_selection_message(self, fake_bot, fake_cursor):

        fake_message = MagicMock()
        fake_message.chat.id = 123456789 
        fake_message.text = "Activate"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "message": {"chose_region_message": "Please select your region"},
            "regions_spain": {"region_id_1": "Region 1", "region_id_2": "Region 2"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await get_activate(fake_message)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            "<b>Please select your region</b>",
            parse_mode='html',
            reply_markup=MagicMock()
        )


class TestHandleRegionCallbackFunction(unittest.TestCase):
    
    @patch('db.cursor.cursor')
    @patch('main.bot')
    async def test_send_price_message(self, fake_bot, fake_cursor):

        fake_call = MagicMock()
        fake_call.from_user.id = 123456789
        fake_call.data = "region_id_1"

        fake_cursor.get_user_language.return_value = 'en'

        fake_language_data = {
            "message": {"price_message": "Here are the prices for the selected region: "},
            "price": {"price_button1": "Price 1", "price_button2": "Price 2"},
            "regions_spain": {"region_id_1": "Region 1"}
        }
        fake_load_language_file = MagicMock(return_value=fake_language_data)

        await handle_region_callback(fake_call)

        fake_bot.send_message.assert_called_once_with(
            123456789,
            "Here are the prices for the selected region: <b>Region 1</b>",
            parse_mode='html',
            reply_markup=MagicMock()
        )


if __name__ == '__main__':
    unittest.main()
