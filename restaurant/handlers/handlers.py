
from functools import wraps

from flask import Blueprint, request, Response, jsonify, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os
from dotenv import load_dotenv
from entities.entities import User, Order, Dish
from restaurant.database.connect import get_session
import hashlib
import jwt

app_handlers = Blueprint('handlers', __name__)
load_dotenv()
engine = create_engine(os.getenv('path_to_database'))
Session = sessionmaker(bind=engine)
session = Session()


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Checking user role
        user_id = request.headers.get('User-Id')
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        session.close()

        if user and user.role == 'manager':
            return f(*args, **kwargs)
        else:
            abort(401, 'Unauthorized')

    return decorated


@app_handlers.route('/menu', methods=['GET'])
@manager_required
def get_dishes():
    # Opening session
    session = Session()
    try:
        # Getting all dishes
        dishes = session.query(Dish).all()
        # Forming JSON list
        response = [{'id': dish.id, 'name': dish.name, 'description': dish.description, 'price': dish.price,
                     'quantity': dish.quantity} for dish in dishes]
        return jsonify(response), 200
    except Exception as e:
        # Handling exceptions
        return jsonify({'error': str(e)}), 500
    finally:
        # Closing session
        session.close()


@app_handlers.route('/dish', methods=['GET'])
@manager_required
def get_dish():
    dish_id = request.args.get('dish_id')
    if not dish_id:
        return jsonify({'error': 'dish id was not mentioned'}), 401
    session = Session()
    try:
        # Getting dish by id
        dish = session.query(Dish).get(dish_id)
        if dish:
            # Forming JSON answer
            response = {'id': dish.id, 'name': dish.name, 'description': dish.description, 'price': dish.price,
                        'quantity': dish.quantity}
            return jsonify(response), 200
        else:
            # Handling case with "not found" dish
            return jsonify({'error': 'Dish was not found'}), 404
    except Exception as e:
        # Handling exceptions
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app_handlers.route('/dishes', methods=['POST'])
@manager_required
def create_dish():
    # Opening session
    session = Session()
    try:
        # Getting dish info
        data = request.json
        if not 'name' in data or not 'price' in data or not 'quantity' in data:
            return jsonify({'Ошибка': 'Fullfill all fields'}), 401
        if not 'description' in data:
            data['description'] = ''
        # Making new dish
        dish = Dish(name=data['name'], description=data['description'], price=data['price'], quantity=data['quantity'])
        # Adding dish
        session.add(dish)
        session.commit()
        # JSON answer
        return jsonify({'message': 'Dish added!'}), 201
    except Exception as e:
        # Handling exceptions
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        # Closing session
        session.close()


@app_handlers.route('/update/<int:dish_id>', methods=['PUT'])
@manager_required
def update_dish(dish_id):
    # Opening session
    session = Session()
    try:
        # Getting dish info
        data = request.json
        # Getting dish by id
        dish = session.query(Dish).get(dish_id)
        if dish:
            # Renewing dish data
            dish.name = data['name'] if 'name' in data else dish.name
            dish.description = data['description'] if 'description' in data else dish.description
            dish.price = data['price'] if 'price' in data else dish.price
            dish.quantity = data['quantity'] if 'quantity' in data else dish.quantity
            session.commit()
            # JSON answer
            return jsonify({'message': 'Dish updated!'}), 201
        else:
            # Handling case with "not found" dish
            return jsonify({'Error': 'Dish was not found'}), 404
    except Exception as e:
        # Handling exceptions
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        # Closing session
        session.close()

@app_handlers.route('/new', methods=['POST'])
def create_order():
    data = request.get_json()
    if 'user_id' not in data or 'dishes' not in data:
        return jsonify({'message': 'fulfill all fields'}), 400
    user_id = data.get('user_id')
    status = data.get('status', 'working')
    special_requests = data.get('special_requests')
    dishes = data.get('dishes')
    session = get_session()
    users = session.query(User).all()
    user_exists = any(user.id == user_id for user in users)
    if not user_exists:
        return jsonify({'message': 'user id not found'}), 400
    for dish_id in dishes:
        dish = session.query(Dish).filter_by(id=dish_id).first()
        if not dish:
            return jsonify({'message': f'Dish with id = {dish_id} does not exist'}), 400
        dish.quantity -= 1
        session.commit()
    order = Order(user_id=user_id, status=status, special_requests=special_requests, dishes=dishes)
    session.add(order)
    session.commit()
    return jsonify({'message': 'Order added'}), 201


@app_handlers.route('/list_of_orders', methods=['GET'])
def get_order():
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({'error': 'id was not mentioned'}), 401
    session = get_session()
    try:
        # Getting order by id
        order = session.query(Order).get(order_id)

        if order:
            response = {
                'id': order.id,
                'status': order.status
            }
            return jsonify(response), 200
        else:
            # Handling case with "not found" order
            return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()