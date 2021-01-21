DO
$$
    BEGIN
        IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'chat_type') THEN
            CREATE TYPE chat_type AS ENUM ('private', 'group', 'supergroup', 'channel');
        END IF;
    END
$$;

CREATE TABLE IF NOT EXISTS chat
(
    id   BIGINT PRIMARY KEY NOT NULL,
    type chat_type          NOT NULL
);

CREATE TABLE IF NOT EXISTS gmail
(
    email         VARCHAR(128) PRIMARY KEY NOT NULL,
    refresh_token VARCHAR(512),
    access_token  VARCHAR(2048)            NOT NULL,
    expires_at    VARCHAR(32)              NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_gmail
(
    chat_id BIGINT REFERENCES chat (id) ON DELETE CASCADE,
    email   VARCHAR(128) REFERENCES gmail (email) ON DELETE CASCADE,
    CONSTRAINT chat_id_email PRIMARY KEY (chat_id, email)
);

CREATE OR REPLACE PROCEDURE ADD_GMAIL(_email VARCHAR(128)
                                     , _refresh_token VARCHAR(512)
                                     , _access_token VARCHAR(2048)
                                     , _expires_at VARCHAR(32)
                                     , _chat_id BIGINT)
    LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO gmail (email, access_token, expires_at)
    VALUES (_email, _access_token, _expires_at)
    ON CONFLICT (email) DO UPDATE SET access_token = excluded.access_token,
                                      expires_at   = excluded.expires_at;
    IF _refresh_token IS NOT NULL THEN
        UPDATE gmail
        SET refresh_token = _refresh_token
        WHERE email = _email;
    END IF;
    commit;

    INSERT INTO chat_gmail (chat_id, email)
    VALUES (_chat_id, _email)
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE TABLE IF NOT EXISTS watched_emails
(
    email      VARCHAR(128) NOT NULL,
    last_watch timestamptz  NOT NULL,
    CONSTRAINT fk_email FOREIGN KEY (email) REFERENCES gmail (email) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS watched_chat_emails
(
    chat_id BIGINT NOT NULL,
    email   VARCHAR(128) NOT NULL,
    CONSTRAINT watched_chat_id_email FOREIGN KEY (chat_id, email) REFERENCES chat_gmail (chat_id, email) ON DELETE CASCADE
);

