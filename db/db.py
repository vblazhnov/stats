__author__ = 'r1zar'

import psycopg2

def db_connect():
    """
    Производит подключение к базе данных
    """
    try:
            conn = psycopg2.connect("dbname='test' user='postgres' host='localhost' password='test123'")
    except:
        print("I am unable to connect to the database")
    return conn

class DataBase:
    """
    Класс базы данных
    Содержит все методы, необходимые для работы приложения
    """
    __cur = db_connect().cursor()

    @staticmethod
    def is_valid_pass(login, pwd):
        """
        Проверяет валидный ли пассворд передал пользователь
        """
        pass

    @staticmethod
    def add_user(login, pwd):
        """
        Добавляет пользователя
        """
        pass

    @staticmethod
    def get_user_api_key(login):
        """
        Возвращает api key по логину
        """
        pass

    @staticmethod
    def get_user_id_by_api_key(apiKey):
        """
        Возвращает id пользователя по api key
        """
        pass

    @staticmethod
    def add_event(apiKey, eventName, date):
        """
        Добавляет event в БД
        """
        pass

    @staticmethod
    def get_users_events(userId):
        """
        Возвращает последовательность кортежей (имя евента - количество раз) заданного пользователя
        """
        pass

    @staticmethod
    def get_users_event(userId, eventName):
        """
        Возвращает последовательность кортежей (ip отправителя - дата) заданного евента указанного пользователя
        """
        pass