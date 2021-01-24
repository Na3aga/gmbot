from typing import List, Callable, Awaitable

import asyncpg
import logging
import ssl


def conn(func):
    """
    Add every connection to a connection pool
    """

    async def decor(self, *args, **kwargs):
        async with self.pool.acquire() as conn:
            # TODO: make working transaction wrapper (? in separate func)
            # try `return await func(self, conn, *args, **kwargs)` to be able to use *args
            return await func(self, conn=conn, *args, **kwargs)

    return decor


class DataBase:
    @classmethod
    async def connect(cls, DATABASE_URL):
        """
        Create class instance with established connection
        also create db if not exists
        """
        self = DataBase()
        ctx = ssl.create_default_context(cafile='concatenated.pem')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.pool = await asyncpg.create_pool(DATABASE_URL, ssl=ctx)
        await self.create_db()
        return self

    @conn
    async def create_db(self, conn):
        """
        Create DB from specified file

        Args:
            conn (asyncpg.pool.PoolAcquireContext): use decorator's connection pool
        """
        logging.info('Creating DB ...')
        with open("DB/create.sql", "r") as file:
            create_db_command = file.read()
        await conn.execute(create_db_command)

    @conn
    async def add_chat(self, conn, chat_id, chat_type):
        """
        Add a chat to DB
        Args:
            conn (asyncpg.pool.PoolAcquireContext): same as in create_db
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
    async def add_gmail(self, conn, email, refresh_token, access_token,
                        expires_at, chat_id):
        """
        Calling stored procedure in DB that adds email and its data and link
        FK with each other
        Args:
            email (str): gmail address up to 128 bytes
            refresh_token (str): refresh token for offline access up to 512 bytes
            access_token (str): access user token  up to 2048 bytes
            expires_at (str): time of token expiration to 32 bytes
            chat_id (int): chat id can be up to 52 bits
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
    async def get_gmail_creds(self, conn, email: str) -> asyncpg.Record:
        """
        Get user credentials with that email
        Args:
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

    @conn
    async def email_in_chat(self, conn, email: str, chat_id: int) -> asyncpg.Record:
        """
        Get email, chat if they are linked in 'chat_gmail' table
        Args:
            conn: (asyncpg.pool.PoolAcquireContext): same as in create_db
            email (str): gmail address up to 128 bytes
            chat_id (int): chat id can be up to 52 bits

        Returns:
            (asyncpg.Record): row with email and chat ID if they are exists in the table
        """
        logging.debug(f"Checking if chat '{chat_id}' has email '{email}'")
        return await conn.fetchrow(
            """select email, chat_id
            from chat_gmail
            where email = $1 and chat_id=$2""",
            email, chat_id)

    @conn
    async def add_watched_chat_emails(self, conn, email: str, chat_id: int):
        """
        Adding already linked chat and email from 'chat_gmail' table to watched_chat_emails
        Args:
            same as in email_in_chat()
        """
        logging.debug(f"Add existing chat_email to watched {email}, {chat_id}")
        await conn.execute(
            """insert into watched_chat_emails (email, chat_id)
            select email, chat_id
            from chat_gmail
            where email = $1 and chat_id = $2
            on conflict do nothing""",
            email, chat_id)

    @conn
    async def remove_watched_chat_emails(self, conn, email: str, chat_id: int):
        """
        Remove chat and email from watched_chat_emails
        Args:
            same as in email_in_chat()
        """
        await conn.execute(
            """delete
            from watched_chat_emails
            where email = $1
              and chat_id = $2""",
            email, chat_id)

    @conn
    async def email_watched(self, conn, email: str) -> asyncpg.Record:
        """
        Get email if it 'watched_emails' table
        Args:
            conn, email: same as in email_in_chat()

        Returns:
            same as in email_in_chat()
        """
        logging.debug(f"Checking if email '{email}' is watched")
        return await conn.fetchrow(
            """select email
            from watched_emails
            where email = $1""",
            email
        )

    @conn
    async def watch_email(self, conn, email: str):
        """
        Adding already existing email from 'gmail' table to 'watched_emails' with timestamp
        Args:
            same as in email_watched()
        """
        logging.debug(f"Start watching email '{email}'")
        await conn.execute(
            """insert into watched_emails (email, last_watch)
            values ((select email from gmail where gmail.email = $1), now())
            on conflict do nothing
            """,
            email
        )

    @conn
    async def remove_watch_email(self, conn, email: str):
        """
        Remove email from 'watched_emails'
        Args:
            same as in email_watched()
        """
        await conn.execute(
            """delete
            from watched_emails
            where email = $1""",
            email
        )

    @conn
    async def get_watched_chats(self, conn, email: str) -> List[asyncpg.Record]:
        """
        Get list of all watched chats with given email
        Args:
           same as in email_watched()
        Returns:
            (List[asyncpg.Record]): List of all watched chats
        """
        logging.debug(f"Getting all the watched chats wit email '{email}'")
        return await conn.fetch(
            """select chat_id
            from watched_chat_emails
            where email = $1""",
            email)

    @conn
    async def get_old_watched_emails(self, conn, hours) -> List[asyncpg.Record]:
        """
        Get all the emails which last watch is greater than 'hours' hours ago
        Args:
            conn (asyncpg.pool.PoolAcquireContext): use decorator's connection pool
            hours (int): hours difference
        Returns:
            (List[asyncpg.Record]): list of all the records with old updates
        """
        return await conn.fetch(
            """select email
            from watched_emails
            where DATE_PART('day', now() - last_watch) * 24
            + DATE_PART('hour', now() - last_watch) >= $1""",
            hours
        )

    @conn
    async def update_email_last_watch(self, conn, email):
        # alter table and inserting last update time
        pass