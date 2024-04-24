import psycopg2
from dotenv import dotenv_values
import os


# variables in .env file
dotenv_variables = {
    **dotenv_values()
}


class BotDatabase:
    """
    class for creating a connection to a db
    """

    def __init__(self, database, host, user, password, port):
        self.database = database
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        self.cursor = None


    def connect(self):
        try:
            self.connection = psycopg2.connect(
                database=self.database,
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.connection.cursor()
        except Exception as e:
            print("Error executing query:", e)


    def check_user_id(self, user_id):
        query = "SELECT user_id, language FROM users WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()


    def add_user(self, user_id, telegram_chat_id, nickname, language, payment_method=None):
        query = """
                INSERT INTO users (user_id, telegram_chat_id, nickname, language, payment_method)
                VALUES (%s, %s, %s, %s, %s)
            """
        self.cursor.execute(query, (user_id, telegram_chat_id, nickname, language, payment_method))
        self.connection.commit()
        

    def update_user(self, user_id, telegram_chat_id=None, nickname=None, language=None, payment_method=None):
        update_params = []

        # Проверяем на наличие параметра
        if telegram_chat_id is not None:
            update_params.append(f"telegram_chat_id = '{telegram_chat_id}'")
        if nickname is not None:
            update_params.append(f"nickname = '{nickname}'")
        if language is not None:
            update_params.append(f"language = '{language}'")
        if payment_method is not None:
            update_params.append(f"payment_method = '{payment_method}'")
            
        if update_params:
                set_clause = ", ".join(update_params)
                query = f"UPDATE users SET {set_clause} WHERE user_id = %s"
                self.cursor.execute(query, (user_id,))
                self.connection.commit()
                return True

        self.cursor.execute(query, (language, user_id))
        self.conn.commit()


    def get_user_language(self, user_id):
        query = "SELECT language, language FROM users WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()[1]


    def delete_user(self, user_id):
        query = "DELETE FROM users WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        self.connection.commit()  

    
    def get_payment_method(self, user_id):
        query = "SELECT payment_method FROM users WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()[0]
    
    
    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()



# db connect
cursor = BotDatabase(database = dotenv_variables['POSTGRES_DB'],
                        host = dotenv_variables['DB_HOST'],
                        user = dotenv_variables['POSTGRES_USER'],
                        password = dotenv_variables['POSTGRES_PASSWORD'],
                        port = dotenv_variables['DB_PORT'])

