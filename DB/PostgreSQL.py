import asyncpg
import logging
from config import DATABASE_URL


class DataBase():
    @classmethod
    async def connect(cls):
        self = DataBase()
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_db()
        return self

    def conn(func):
        async def decor(self, *args, **kwargs):
            async with self.pool.acquire() as conn:
                return await func(self, conn=conn, *args, **kwargs)
        return decor

    @conn
    async def create_db(self, conn):
        logging.info('Creating DB ...')
        with open("DB/create.sql", "r") as file:
            create_db_command = file.read()
        await conn.execute(create_db_command)

    @conn
    async def add_chat(self, conn, chat_id, chat_type):
        await conn.execute(
            """INSERT INTO chat (id, type)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING""",
            chat_id,
            chat_type)

    @conn
    async def add_gmail(self,
                        conn,
                        email,
                        refresh_token,
                        access_token,
                        expires_at,
                        chat_id):
        await conn.execute(
            "call add_gmail($1,$2,$3,$4,$5)",
            email,
            refresh_token,
            access_token,
            expires_at,
            chat_id)


    @conn
    async def get_gmail_creds(self, conn, email):
        return await conn.fetchrow(
            """select refresh_token, access_token, expires_at
            from gmail
            where email = $1""",
            email)
