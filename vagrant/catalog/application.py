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

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add user info to templates
@app.context_processor
def inject_user():
    return dict(user=login_session)

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

# Google sign up / sign in

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        #return response
        return redirect(url_for('showCategories'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print data
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Save new user into database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s(%s)" % (login_session['username'],
                                                   login_session['email']), 'success')
    print "done!"
    return output

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Show app homepage
@app.route('/')
@app.route('/home/')
def showCategories():
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.id))
    latestItems = session.query(Item).order_by(Item.id.desc()).limit(10)
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories,
                               latestItems=latestItems)
    else:
        return render_template('categories.html', categories=categories,
                           latestItems=latestItems)

# Show items from given category
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def showItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.name))
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitems.html', items=items, currentCategory=category,
                               categories=categories, creator=creator)
    else:
        return render_template('items.html', items=items, currentCategory=category,
                           categories=categories, creator=creator)

# Create new category
@app.route('/category/new/', methods=['GET', 'POST'])
def addCategory():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.name))
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name, 'success')
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('addcategory.html', categories=categories)

# Edit category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(
        Category).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name, 'info')
            return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', category=editedCategory)


# Delete category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name, 'danger')
        session.commit()
        return redirect(url_for('showCategories', category_id=category_id))
    else:
        return render_template('deletecategory.html', category=categoryToDelete)

# Create a new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def addItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category.id, Category.name, func.count(Item.id).label('count')).\
        filter(getattr(Category, 'user_id').__eq__(login_session['user_id'])).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.name))

    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this category. Please create your own category in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form['description'].strip(),
                           price=request.form['price'], category_id=request.form['category'],
                           user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.name), 'success')
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('additem.html', category_id=category_id, categories=categories)

# Edit item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category.id, Category.name, func.count(Item.id).label('count')).\
        filter(getattr(Category, 'user_id').__eq__(login_session['user_id'])).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.name))
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items to this category. Please create your own category in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description'].strip()
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited', 'info')
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
                               item_id=item_id, item=editedItem, categories=categories)

# Delete item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category.id, Category.name,
                               func.count(Item.id).label('count')).\
        outerjoin(Item).group_by(Category.id).order_by(asc(Category.name))
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete items to this category. Please create your own category in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted', 'danger')
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete,
                               categories=categories, currentCategory=category_id)

# JSON API endpoints
@app.route('/categories/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
