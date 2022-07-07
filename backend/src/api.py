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

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def show_drinks():
    drinks = Drink.query.all()
    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(payload):
    drinks = Drink.query.all()
    return {
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    }


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def make_drink(payload):
    data = request.get_json(force=True)
    drink = Drink(title=data.get('title'), recipe=json.dumps(data.get('recipe')))
    drink.insert()
    return {
        "success": True,
        "drinks": [drink.long()]
    }


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drinks(payload, id):
    data = request.get_json(force=True)
    drink = Drink.query.get(int(id))
    if data.get('title'):
        drink.title = data['title']
    if data.get('recipe'):
        drink.recipe = json.dumps(data['recipe'])
    drink.update()
    return {
        "success": True,
        "drinks": [drink.long()]
    }


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.get(int(id))
    drink.delete()
    return {
        "success": True,
        "delete": int(id)
    }


# Error Handling
'''
Example error handling for unprocessable entity
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
        "message": "requested resource was not found"
    })


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(401)
def authentication_error(exception):
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": "Unauthorized"
    }), 401
