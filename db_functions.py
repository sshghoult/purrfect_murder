import aiomysql
import pymysql
import asyncio
import cfg
import logging
import random


# TODO: nested id-elses to specify error in the data (for every db function)


async def add_user(ids: dict):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=True)
    cur = await conn.cursor()

    logging.debug(msg=f'add_user: id={ids}')
    try:
        await cur.execute(r'INSERT INTO user(internal_id, telegram_id, vk_id, plain_id) VALUE (default, %s, %s, %s)',
                          (ids['telegram_id'], ids['vk_id'], ids['plain_id']))
    except pymysql.MySQLError:
        conn.close()
        raise ValueError('Data error')
    conn.close()


async def add_lobby(lobby_code: str):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=True)
    cur = await conn.cursor()
    logging.debug(msg=f'add_lobby: id={lobby_code}')
    try:
        await cur.execute(r'INSERT INTO lobby(internal_id, external_code, has_started) VALUE (default, %s, %s)', (lobby_code, False))
    except pymysql.MySQLError as e:
        logging.debug(msg=f'add_lobby: Exception={e}')
        conn.close()
        raise ValueError('Data error')
    conn.close()


async def user_joined_lobby(lobby_ext_code, user_ext_id, source_token=None):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=True)
    cur = await conn.cursor()

    try:
        await cur.execute(r'INSERT INTO user_in_lobby(relation_id, internal_lobby_id, internal_user_id_1, internal_victim_id, user_alive)'
                          r' VALUE (DEFAULT, '
                          r'(SELECT internal_id FROM lobby WHERE external_code = %s), '
                          r'(SELECT internal_id FROM user WHERE plain_id = %s), NULL, NULL)', (lobby_ext_code, user_ext_id))

        # TODO: look for appropriate source here
    except pymysql.MySQLError as e:
        logging.debug(msg=f'user_joined_lobby: Exception={e}')
        conn.close()
        raise ValueError('Data error')
    conn.close()


async def lobby_started(lobby_ext_code):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    cur = await conn.cursor()

    try:
        await conn.begin()
        await cur.execute(r'SELECT internal_user_id_1 FROM user_in_lobby '
                          r'WHERE internal_lobby_id = (SELECT internal_id FROM lobby WHERE external_code = %s)',
                          (lobby_ext_code,))
        participants = list(i['internal_user_id_1'] for i in await cur.fetchall())
        # print(participants)
        # exit(1)

        ids = [(participants[i - 1], participants[i]) for i in range(len(participants) - 1, -1, -1)]
        random.shuffle(ids)
        for internal_user_id, victim_internal_id in ids:
            # (SELECT internal_id FROM user WHERE plain_id = %s)
            await cur.execute(r'UPDATE user_in_lobby SET internal_victim_id = %s, user_alive = 1 '
                              r'WHERE internal_lobby_id = (SELECT internal_id FROM lobby WHERE external_code = %s) and '
                              r'internal_user_id_1 = %s',
                              (victim_internal_id, lobby_ext_code, internal_user_id))

        await cur.execute('UPDATE lobby SET has_started = 1 WHERE external_code = %s ', (lobby_ext_code,))

    except pymysql.MySQLError as e:
        await conn.rollback()
        logging.debug(msg=f'lobby_started: Exception={e}')
        conn.close()
        raise ValueError('Data error')
    else:
        await conn.commit()


async def accept_kill(victim_id, source_token=None):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    cur = await conn.cursor()

    try:
        await conn.begin()

        # TODO: look for appropriate source here
        await cur.execute(r'UPDATE user_in_lobby SET internal_victim_id = '
                          r'    (SELECT internal_victim_id FROM (SELECT * FROM user_in_lobby) AS uil  '
                          r'    WHERE internal_user_id_1 = (SELECT internal_id FROM user WHERE plain_id = %s) )'
                          r' WHERE internal_victim_id = '
                          r'(SELECT internal_id FROM user WHERE plain_id = %s)', (victim_id, victim_id))
        await cur.execute(r'UPDATE user_in_lobby SET user_alive = 0, internal_victim_id = NULL WHERE internal_user_id_1 = '
                          r'(SELECT internal_id FROM user WHERE plain_id = %s)', (victim_id,))

        await cur.execute('SELECT internal_user_id_1, internal_lobby_id FROM user_in_lobby WHERE internal_lobby_id = '
                          '(SELECT internal_lobby_id FROM user_in_lobby '
                          'WHERE internal_user_id_1 = (SELECT internal_id FROM user WHERE plain_id = %s)) AND user_alive = 1', (victim_id))
        players = await cur.fetchall()
        if 0 < len(players) <= 2:
            await cur.execute('DELETE FROM lobby WHERE internal_id = %s', (players[0]['internal_lobby_id'],))
    except pymysql.MySQLError as e:
        await conn.rollback()
        logging.debug(msg=f'accept_kill: Exception={e}')
        conn.close()
        raise ValueError('Data error')
    await conn.commit()


async def get_lobby_info(lobby_ext_code):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    cur = await conn.cursor()

    try:
        await cur.execute('''SELECT internal_user_id_1, plain_id, internal_victim_id, user_alive FROM
                            (SELECT internal_user_id_1, internal_victim_id, user_alive FROM user_in_lobby WHERE internal_lobby_id =
                            (SELECT internal_id FROM lobby WHERE external_code = %s)) as uil
                            LEFT JOIN (SELECT plain_id, internal_id FROM user) as usr ON uil.internal_user_id_1 = usr.internal_id;''',
                          (lobby_ext_code,))
        users_data = await cur.fetchall()

        await cur.execute(r'SELECT * FROM lobby WHERE external_code = %s', (lobby_ext_code,))
        lobby_data = await cur.fetchone()
        return [users_data, lobby_data]

    except pymysql.MySQLError as e:
        await conn.rollback()
        logging.debug(msg=f'accept_kill: Exception={e}')
        conn.close()
        raise ValueError('Data error')


# TODO: current db func do not support multiple room joins by the same player
#

#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(accept_kill(123))


async def init_db():
    """
create table lobby
(
	internal_id int unsigned auto_increment
		primary key,
	external_code char(5) null,
	has_started tinyint(1) null,
	constraint external_code
		unique (external_code)
);

create table user
(
	internal_id int unsigned auto_increment
		primary key,
	telegram_id varchar(45) null,
	vk_id varchar(45) null,
	plain_id varchar(45) null,
	constraint plain_id
		unique (plain_id),
	constraint telegram_id
		unique (telegram_id),
	constraint vk_id
		unique (vk_id)
);

create table user_in_lobby
(
	relation_id int unsigned auto_increment
		primary key,
	internal_lobby_id int unsigned not null,
	internal_user_id_1 int unsigned not null,
	internal_victim_id int unsigned null,
	user_alive tinyint(1) null,
	constraint FK_22
		foreign key (internal_user_id_1) references user (internal_id),
	constraint FK_26
		foreign key (internal_victim_id) references user (internal_id),
	constraint user_in_lobby_ibfk_1
		foreign key (internal_lobby_id) references lobby (internal_id)
			on delete cascade
);

create index fkIdx_18
	on user_in_lobby (internal_lobby_id);

create index fkIdx_23
	on user_in_lobby (internal_user_id_1);

create index fkIdx_27
	on user_in_lobby (internal_victim_id);

"""
