import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()  # uncomment initialize the database

# ROUTES
'''
GET /drinks
it should be a public endpoint
it should contain only the drink.short() data representation
returns status code 200 and json {"success": True, "drinks": drinks}
where drinks is the list of drinks
or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    drink_list = []
    for drink in drinks:
        drink_list.append(drink.short())
    return jsonify({
        'success': True,
        'drinks': drink_list
    })


'''
GET /drinks-detail
it should require the 'get:drinks-detail' permission
it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drinks}
where drinks is the list of drinks
or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    drink_list = []
    for drink in drinks:
        drink_list.append(drink.long())
    return jsonify({
        'success': True,
        'drinks': drink_list
    })


'''
POST /drinks
it should create a new row in the drinks table
it should require the 'post:drinks' permission
it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink}
where drink is an array containing only the newly created drink
or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    body = request.get_json()
    new_title = body.get('title')
    # convert dict to str for storage
    new_recipe = json.dumps(body.get('recipe'))

    if new_title == '' or new_recipe == '':
        abort(422)  # invalid input
    if bool(Drink.query.filter_by(title=new_title).first()):
        abort(400)  # drink with same name exists in db

    drink = Drink(title=new_title, recipe=new_recipe)
    drink.insert()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
PATCH /drinks/<id>
where <id> is the existing model id
it should respond with a 404 error if <id> is not found
it should update the corresponding row for <id>
it should require the 'patch:drinks' permission
it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where
drink an array containing only the updated drink
or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    body = request.get_json()
    new_title = body.get('title')
    # convert dict to str for storage
    new_recipe = json.dumps(body.get('recipe'))

    if new_title != '':
        drink.title = new_title
    if new_recipe != '':
        drink.recipe = new_recipe

    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
DELETE /drinks/<id>
where <id> is the existing model id
it should respond with a 404 error if <id> is not found
it should delete the corresponding row for <id>
it should require the 'delete:drinks' permission
returns status code 200 and json {"success": True, "delete": id} where
id is the id of the deleted record
or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    drink.delete()

    return jsonify({
        'success': True,
        'deleted': id
    })


# Error Handling
'''
Error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


'''
Error handler for AuthError
'''


@app.errorhandler(AuthError)
def authorization_errors(error):
    print(error.error['code'])  # for debugging purpose
    return jsonify({
        "success": False,
        "error": 401,
        "message": error.error['description']
    }), 401
