#!flask/bin/python
__author__ = 'vblazhnov'

from db import DataBase
from functools import wraps
from flask import Flask, jsonify, abort, make_response, request

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def incorrect_data(error):
    return make_response(jsonify({'error': 'Your data is incorrect'}), 400)

@app.errorhandler(409)
def conflict_data(error):
    return make_response(jsonify({'error': 'Your data is conflict. Try another.'}), 409)

@app.errorhandler(403)
def conflict_data(error):
    return unauthorized()

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return unauthorized()
        kwargs['authUserName'] = auth.username
        return f(*args, **kwargs)
    return decorated

def check_auth(login, password):
    return DataBase.is_valid_pass(login, password)

def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

@app.route('/stats/api/register', methods=['POST'])
def sign_up():
    """
    Регистрация нового пользователя
    """

    if not request.json or not 'login' in request.json or not 'password' in request.json:
        abort(400)

    user = DataBase.add_user(request.json['login'], request.json['password'])

    if user is None:
        abort(409)

    return jsonify({'login': user[1], 'apiKey': user[3]}), 201

@app.route('/stats/api/me', methods=['GET'])
@requires_auth
def get_user_info(**args):
    """
    Получение информации о пользователе
    """

    user = DataBase.get_user_info(args['authUserName'])

    if user is None:
        abort(403)

    return jsonify({'login': user[1], 'apiKey': user[3]})

@app.route('/stats/api/events', methods=['POST'])
def add_event():
    """
    Добавление евента
    """

    if not request.json or not 'apiKey' in request.json or not 'event' in request.json:
        abort(400)

    result = DataBase.add_event(request.json['apiKey'], request.json['event'], request.remote_addr)

    if result is None:
        abort(400)

    return jsonify({'event': result[2], 'date': result[3], 'ip': result[4]}), 201

@app.route('/stats/api/events', methods=['GET'])
@requires_auth
def get_events(**args):
    """
    Получение своих евентов
    """

    user = DataBase.get_user_info(args['authUserName'])

    if user is None:
        abort(403)

    result = DataBase.get_users_events(user[0])

    return jsonify({'events': result})

@app.route('/stats/api/events/<string:name>', methods=['GET'])
@requires_auth
def get_event(name, **args):
    """
    Получение подробной информации об евенте
    """

    user = DataBase.get_user_info(args['authUserName'])

    if user is None:
        abort(403)

    result = DataBase.get_users_event(user[0], name)
    return jsonify({'event': name, 'events': result})

if __name__ == '__main__':
    app.run(debug=True)


