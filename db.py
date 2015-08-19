# Copyright 2015 vblazhnov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'vblazhnov'

import psycopg2
import hashlib

def db_connect():
    """
    Производит подключение к базе данных
    """
    try:
        conn = psycopg2.connect("dbname='test' user='postgres' host='localhost' password='test123'")
        cur = conn.cursor()
        cur.execute("SELECT EXISTS (SELECT * FROM information_schema.tables WHERE table_name=%s)", ('users',))
        if not cur.fetchone()[0]:
            cur.execute("""
            CREATE TABLE users
            (
              id serial NOT NULL,
              login text NOT NULL,
              pwd_hash text NOT NULL,
              api_key text NOT NULL,
              CONSTRAINT uid PRIMARY KEY (id)
            );
            """)
            conn.commit()

        cur.execute("SELECT EXISTS (SELECT * FROM information_schema.tables WHERE table_name=%s)", ('events',))
        if not cur.fetchone()[0]:
            cur.execute("""
            CREATE TABLE events
            (
              id serial NOT NULL,
              owner_id integer NOT NULL,
              name text NOT NULL,
              date timestamp without time zone NOT NULL,
              ip text NOT NULL,
              CONSTRAINT eid PRIMARY KEY (id),
              CONSTRAINT oid FOREIGN KEY (owner_id)
                  REFERENCES users (id) MATCH SIMPLE
                  ON UPDATE CASCADE ON DELETE CASCADE
            );
            """)
            conn.commit()

    except Exception as E:
        print("I am unable to connect to the database")
        print(E)
    else:
        return conn

class DataBase:
    """
    Класс базы данных.
    Содержит все методы работы с БД, необходимые для приложения.
    Если БД не содержит необходимые таблицы, создает их.
    """

    __conn = db_connect()
    __cur = __conn.cursor()

    __salt = "randomSaLTFromGeneRaT0r".encode('utf-8')

    @staticmethod
    def get_user_info(login):
        """
        Возвращает информацию о заданном пользователе
        :param login: логин пользователя
        :return: кортеж информации о пользователе (id, login, pwd_hash, api_key)
        """

        # в psycopg2 экранирование происходит автоматически в методе execute
        DataBase.__cur.execute("""SELECT id, login, pwd_hash, api_key
        FROM users
        WHERE login = %s""", (login,))
        return DataBase.__cur.fetchone()

    @staticmethod
    def get_user_by_api_key(apiKey):
        """
        Возвращает информацию о пользователе по заданному apiKey
        :param apiKey: ключ пользователя
        :return: кортеж информации о пользователе (id, login, pwd_hash, api_key)
        """

        DataBase.__cur.execute("""SELECT id, login, pwd_hash, api_key
        FROM users
        WHERE api_key = %s
        LIMIT 1""", (apiKey,))
        return DataBase.__cur.fetchone()

    @staticmethod
    def hash_with_salt(str):
        """
        Подсчитывает md5-хэш с солью
        :param str: строка
        :return: строку с хэшем
        """

        md5 = hashlib.md5
        return md5(md5(str.encode('utf-8')).hexdigest().encode('utf-8') + DataBase.__salt).hexdigest()

    @staticmethod
    def is_valid_pass(login, pwd):
        """
        Проверяет валиден ли пароль
        :param login: логин пользователя
        :param pwd: пароль пользователя
        :return: True - если валиден, иначе False
        """

        user = DataBase.get_user_info(login)
        if user is None:
            return False

        return DataBase.hash_with_salt(pwd) == user[2]

    @staticmethod
    def add_user(login, pwd):
        """
        Добавляет нового пользователя в БД
        :param login: логин пользователя
        :param pwd: пароль пользователя
        :return: кортеж информации о пользователе (id, login, pwd_hash, api_key)
        """

        if DataBase.get_user_info(login) is not None:
            return None

        pwd_hash = DataBase.hash_with_salt(pwd)
        # длинный api_key для его уникальности
        api_key = DataBase.hash_with_salt(login) + DataBase.hash_with_salt(login + pwd)
        DataBase.__cur.execute("""INSERT INTO users (login, pwd_hash, api_key)
        VALUES (%s, %s, %s)
        RETURNING id, login, pwd_hash, api_key""", (login, pwd_hash, api_key))
        DataBase.__conn.commit()
        return DataBase.__cur.fetchone()

    @staticmethod
    def add_event(apiKey, eventName, ip):
        """
        Добавляет информацию о новом эвенте в базу данных
        :param apiKey: ключ пользователя
        :param eventName: имя евента
        :param ip: ip, с которого пришел евент
        :return: кортеж информации об евенте (id, owner_id, name, date, ip)
        """

        user = DataBase.get_user_by_api_key(apiKey)
        if user is None:
            return None

        userId = user[0]
        # в postgres now заменяется на время произведения транзакции
        DataBase.__cur.execute("""INSERT INTO events(owner_id, name, date, ip)
        VALUES (%s, %s, %s, %s)
        RETURNING id, owner_id, name, date, ip""", (userId, eventName, "now", ip))
        DataBase.__conn.commit()
        return DataBase.__cur.fetchone()

    @staticmethod
    def get_users_events(userId):
        """
        Возвращает все евенты заданного пользователя и их количество
        :param userId: заданный id пользователя
        :return: список кортежей (eventName, count)
        """

        DataBase.__cur.execute("""SELECT name, COUNT(name)
        FROM events
        WHERE owner_id = %s
        GROUP BY name
        ORDER BY COUNT(name) DESC""", (userId,))
        return DataBase.__cur.fetchall()

    @staticmethod
    def get_users_event(userId, eventName):
        """
        Возвращает все евенты с заданным именем заданного пользователя
        :param userId: заданный id пользователя
        :param eventName: заданное имя евента
        :return: список кортежей (ip - время евента)
        """

        DataBase.__cur.execute("""SELECT ip, date
        FROM events
        WHERE owner_id = %s AND name = %s
        ORDER BY date DESC""", (userId, eventName))
        return DataBase.__cur.fetchall()
