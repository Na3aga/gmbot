import asyncpg
import logging


class DataBase():
    @classmethod
    async def connect(cls, DATABASE_URL):
        """
        Create class instance with established connection
        also create db if not exists
        """
        self = DataBase()
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_db()
        return self

    def conn(func):
        """
        Add every connection to a connection pool
        """
        async def decor(self, *args, **kwargs):
            async with self.pool.acquire() as conn:
                # TODO: make working transaction wrapper (? in separate func)
                return await func(self, conn=conn, *args, **kwargs)
        return decor

    @conn
    async def create_db(self, conn):
        """
        Create DB from specified file
        """
        logging.info('Creating DB ...')
        with open("DB/create.sql", "r") as file:
            create_db_command = file.read()
        await conn.execute(create_db_command)

    @conn
    async def add_chat(self, conn, chat_id, chat_type):
        """
        Add chat to DB
        Parameters:
        chat_id (int): chat id can be up to 52 bits
        chat_type (str of enum): can be 'private', 'group', 'supergroup', 'channel'
        """
        logging.debug(f"Adding chat {chat_id}")
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
        """
        Calling stored procedure in DB that adds email and its data and link
        FK with each other
        Parameters:
        email (str): gmail address up to 128 bytes
        refresh_token (str): refresh token for offline access up to 512 bytes
        access_token (str): access user token  up to 2048 bytes
        expires_at (str): time of token expiration to 32 bytes
        chat_id (int): gmail address up to 128 bytes
        """
        logging.debug(f"Gmail {email} is adding...")
        await conn.execute(
            "call add_gmail($1,$2,$3,$4,$5)",
            email,
            refresh_token,
            access_token,
            expires_at,
            chat_id)

    @conn
    async def get_gmail_creds(self, conn, email):
        """
        Get user credentials with that email
        Parameters:
        email (str): gmail address up to 128 bytes
        Returns:
        (asyncpg.Record): row with user credentials
        """
        logging.debug(f"Getting credentials from {email}")
        return await conn.fetchrow(
            """select access_token, refresh_token, expires_at
            from gmail
            where email = $1""",
            email)
