from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, func
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Basic app credentials
app = Flask(__name__)

#CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Show app homepage
@app.route('/')
@app.route('/category/')
def showCategories():
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        join(Item).group_by(Item.id).order_by(asc(Category.name))
    latestItems = session.query(Item).order_by(asc(Item.id)).limit(10)
    print(categories)
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories,
                               latestItems=latestItems)
    else:
        return render_template('categories.html', categories=categories)

# Show items from given category
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def showItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        join(Item).group_by(Item.id).order_by(asc(Category.name))
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitems.html', items=items, currentCategory=category,
                               categories=categories, creator=creator)
    else:
        return render_template('items.html', items=items, category=category,
                               creator=creator)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)