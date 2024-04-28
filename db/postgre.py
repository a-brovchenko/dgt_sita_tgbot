"""
Module for asynchronous work with Postgresql
"""

from dotenv import dotenv_values
import asyncpg



# variables in .env file
dotenv_variables = {
    **dotenv_values()
}


class BotDatabase:

    def __init__(self, database, host, user, password, port):
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        except Exception as e:
            print("Error connecting to database:", e)

    async def close(self):
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def execute(self, query, *args):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await connection.fetchrow(query, *args)


    async def check_user_id(self, user_id):
        """
        checking for user presence
        """
        query = "SELECT user_id, language FROM users WHERE user_id = $1"
        row = await self.fetchrow(query, user_id)
        return row[0] if row else row  #user_id or None
    

    async def add_user(self, user_id, telegram_chat_id, nickname, language, region=None, payment_method=None) -> None:
        query = """
                INSERT INTO users (user_id, telegram_chat_id, nickname, region, language, payment_method)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
        await self.execute(query, user_id, telegram_chat_id, nickname, region, language, payment_method)


    async def update_user(self, user_id, **update_fields):
        set_values = []
        values = [user_id]

        for field, value in update_fields.items():
            set_values.append(f"{field} = ${len(values) + 1}")
            values.append(value)

        set_clause = ", ".join(set_values)
        query = f"""
                UPDATE users
                SET {set_clause}
                WHERE user_id = $1
                """

        await self.execute(query, *values)


    async def delete_user(self, user_id):
        query = "DELETE FROM users WHERE user_id = $1"
        await self.execute_query(query, user_id)


    async def get_payment_method(self, user_id):
        query = "SELECT payment_method FROM users WHERE user_id = $1"
        result = await self.fetchrow(query, user_id)
        if result:
            return result[0]
        else:
            return None


    async def get_count_records(self):
        query = "SELECT COUNT(*) FROM users"
        result = await self.fetchrow(query)
        return result[0] if result else 0
    

    async def get_user_language(self, user_id):
        query = "SELECT language FROM users WHERE user_id = $1"
        result = await self.fetchrow(query, user_id)
        return result[0]
    

# Создаем экземпляр класса BotDatabase для подключения к базе данных
cursor = BotDatabase(
    database=dotenv_variables['POSTGRES_DB'],
    host=dotenv_variables['DB_HOST'],
    user=dotenv_variables['POSTGRES_USER'],
    password=dotenv_variables['POSTGRES_PASSWORD'],
    port=dotenv_variables['DB_PORT']
)


