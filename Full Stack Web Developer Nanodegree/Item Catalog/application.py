#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, jsonify, url_for, flash
from datetime import datetime
from werkzeug import secure_filename

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, BannedUser, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
from flask import make_response, request
import requests

from util import create_user, slugify, valid_item, subtree, get_node_to_root
from functools import wraps
import sys  # for args.
# import codecs # for py3  "the JSON object must be str, not 'bytes' "

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # let justify return unicode

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['json', 'txt', '']


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.context_processor
def get_root():
    def find_root(db_object):
        name = db_object.name
        lookfor = db_object
        if lookfor.parent:
            if lookfor.parent.id == 1:
                return '(Main Category)'
            while lookfor.parent and lookfor.parent.id != 1:
                lookfor = lookfor.parent
            name = lookfor.name
            return name
        else:
            return '(Main Category)'
    return dict(find_root=find_root)


def login_required(func):
    '''
    Define a @login_required decorator.
    Usage:
        add @login_required after @app.route()
    Example:
        @app.route('/post')
        @login_required
        def post():
            pass
    '''
    @wraps(func)
    def wrapper(*args, **kargs):
        try:
            # read login_session
            user_email = login_session['email']
            userinfo = session.query(
                                     User).filter_by(
                                     email=login_session['email']).first()
            if not userinfo:
                return func(**kargs)
        except:
            # if no login_session:
            return redirect(url_for('showLogin', next=request.url))
        # verify login session width existing user:
        if user_email == userinfo.email:
            # return func if user found
            return func(**kargs)
        else:
            # or redirect to login page
            return redirect(url_for('showLogin', next=request.url))
    return wrapper


# index()
@app.route('/')
@app.route('/catalog/')
def homepage():
    catalog = session.query(Catalog).filter_by(parent_id=1).all()
    newest_catalog = session.query(
                                   Catalog).filter(
                                   Catalog.id != 1).order_by(
                                   Catalog.create_time.desc()).limit(10)
    if not session.query(Catalog).all():
        # if empty catalog
        Catalogitem1 = Catalog(name="ROOT", id=1, lvl=0,
                               description="Real Root(does not display)",
                               slug="/")
        session.add(Catalogitem1)
        session.commit()
        return 'Empty database, start <a href="%s">setup</a>.'\
               % url_for('manage', setup='1')
    return render_template('homepage.html',
                           catalog=catalog,
                           newest=newest_catalog)


# manage catalog page (including setup + load catalog from file)
@app.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    catalog = session.query(Catalog)
    try:
        ifsetup = request.args.get('setup')
    except (ValueError, TypeError):
        ifsetup = None

    if request.method == 'POST':
        # try:
        file_json = request.form['jsontext']
        file = None
        if not file_json:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_json = file.read().decode("utf-8")
        # get json in string from file or textarea
        jsontext = json.loads(file_json)

        largest_id = session.query(Catalog).order_by(
                        Catalog.id.desc()).limit(1).first()
        existing_parent = int(request.form['moveto'])

        existing_level = session.query(
                                    Catalog).filter_by(
                                    id=existing_parent).first().lvl
        jcatalog = jsontext['Catalog']
        json_min_id = min(jcatalog,
                          key=lambda i: i['id'])
        # min parentid in json
        json_min_parent = min(jcatalog,
                              key=lambda i: i['parent_id'])

        id_plus = int(largest_id.id) - int(json_min_id['id']) + 1

        # sort import list so that parents added first
        newlist = sorted(jcatalog, key=lambda k: k['parent_id'])
        new_list_min_lvl = min(jcatalog,
                               key=lambda i: i['parent_id'])
        # g=list(item for item in newlist  if item["parent_id"] == 1)

        level_plus = existing_level + 1 - int(json_min_parent['level'])

        num = 0

        createdby = session.query(
                                User).filter_by(
                                email=login_session['email']).first()

        for i in newlist:

            # massage uploaded json

            if i['parent_id'] == new_list_min_lvl['parent_id']:
                new_parent = existing_parent
            else:
                new_parent = i['parent_id'] + id_plus

            # safe slug for upload
            safe_slug_prefix = 'upload-' + \
                               datetime.now()\
                               .strftime("%Y-%m-%d-%H-%M-%S")
            i['slug'] = safe_slug_prefix + '-' + i['slug']

            check_item = Catalog(id=int(i['id'])+int(id_plus),
                                 name=i['name'],
                                 description=i['description'],
                                 parent_id=new_parent,
                                 slug=i['slug'],
                                 lvl=int(i['level'])+level_plus,
                                 user_id=createdby.id
                                 )

            session.add(check_item)
            session.commit()
            num = num + 1

        flash('Succefully uploaded %s Catalog.' % num)
        return redirect(url_for('homepage'))

#   except:
        return "Error Uploading, please try again."
    else:
        return render_template('manage.html', catalog=catalog, parentid=1)


@app.route('/catalog/<catalog_path>/')
def catalogItem(catalog_path):

    catalog = session.query(Catalog)
    item = catalog.filter_by(slug=catalog_path).first()

    if item:
        node_to_root = get_node_to_root(item)
        createdby = session.query(User).filter_by(
                id=item.user_id).first()
        return render_template('catalogItem.html',
                               items=item,
                               User=createdby,
                               node_to_root=node_to_root)
    else:
        return 'Category 404 - Not Found', 404


@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
@login_required  # forgot to require log in with preview submit
def deleteItem(catalog_id):
    itemToDelete = session.query(Catalog).filter_by(id=catalog_id).first()
    createdby = session.query(User).filter_by(
                email=login_session['email']).first()
    if not itemToDelete:
        return "Category 404 - Nothing to Delete", 404
    if itemToDelete.user_id != createdby.id:  # checking for User Authorization
        return "Category 403 - Don't touch things that don't belong to you.", 403
    if request.method == 'POST':
        if itemToDelete.children:
            return "Remove children before delete!"
        else:
            if itemToDelete.parent.id == 1:
                redirect_to = redirect('/')
            else:
                redirect_to = redirect(url_for('catalogItem',
                                       catalog_path=itemToDelete.parent.slug))
            session.delete(itemToDelete)
            flash('%s Successfully Deleted' % itemToDelete.name)
            session.commit()
            return redirect_to
    else:
        return render_template('deleteItem.html', catalog=itemToDelete)


@app.route('/new/', methods=['GET', 'POST'])
@app.route('/add/', methods=['GET', 'POST'])
@login_required
def newCatalogItem():
    catalog = session.query(Catalog).filter_by(parent_id=1).all()
    catalog_all = session.query(Catalog)
    newest_catalog = session.query(Catalog).filter(
                        Catalog.id != 1).order_by(
                        Catalog.id.desc()).limit(1).first()

    try:
        parentid = int(request.args.get('parentid'))
    except (ValueError, TypeError):
        parentid = 1
    # print u'new_catalog_item: ', login_session
    if request.method == 'POST':
        if not session.query(Catalog).all():
            Catalogitem1 = Catalog(name="(ROOT)", id=1, lvl=0,
                                   description="Real Root(does not display)",
                                   slug="/")
            session.add(Catalogitem1)
            try:
                session.commit()
            except:  # (IntegrityError,InvalidRequestError):
                session.rollback()
        if request.form['name']:
            newname = request.form['name']
        else:
            newname = 'No Name #' + str(newest_catalog.id+1)
        if request.form['slug']:
            newslug = slugify(request.form['slug'])
        else:
            newslug = str(newest_catalog.id)

        new_item_slug = slugify(newslug)
        parent_node = catalog_all.filter_by(
                      id=int(request.form['moveto'])).first()

        createdby = session.query(User).filter_by(
                email=login_session['email']).first()

        newItem = Catalog(name=newname,
                          description=request.form['description'],
                          parent_id=parent_node.id,
                          slug=new_item_slug,
                          lvl=parent_node.lvl + 1,
                          user_id=createdby.id)

        if valid_item(newItem, session, catalog_all.all()):
            session.add(newItem)
            session.commit()
        else:
            response = make_response(json.dumps(
                        '422 Unprocessable Entity: Duplicated Slug?'), 422)
            response.headers['Content-Type'] = 'application/json'
            return response

        return redirect(url_for('catalogItem', catalog_path=newItem.slug))
    else:
        return render_template('newCatalogItem.html',
                               catalog=catalog, parentid=parentid)


@app.route('/catalog/<catalog_path>/edit/', methods=['GET', 'POST'])
@login_required
def editCatalog(catalog_path):
    edited = session.query(
        Catalog).filter_by(slug=catalog_path).first()
    catalog = session.query(Catalog).filter_by(parent_id=1).all()
    catalog_all = session.query(Catalog)

    createdby = session.query(User).filter_by(
                email=login_session['email']).first()
    if edited.user_id != createdby.id:  # checking for User Authorization
        return "Category 403 - Don't touch things that don't belong to you.", 403
    if edited:
        if request.method == 'POST':
            if request.form:
                if request.form['name']:
                    newname = request.form['name']
                else:
                    newname = 'No Name #'+request.form['id']
                if request.form['slug']:
                    newslug = slugify(request.form['slug'])
                else:
                    newslug = request.form['id']
                parent_node = catalog_all.filter_by(
                            id=int(request.form['moveto'])).first()
                # define a new item to check,
                # avoiding flush() which may cause constraint conflict
                check_item = Catalog(id=int(request.form['id']),
                                     name=newname,
                                     description=request.form['description'],
                                     parent_id=request.form['moveto'],
                                     slug=newslug
                                     )

                if valid_item(check_item, session, catalog_all.all()):
                    edited.name = newname
                    edited.description = request.form['description']
                    edited.parent_id = request.form['moveto']
                    edited.slug = newslug
                    edited.lvl = parent_node.lvl + 1
                    session.merge(edited)
                    session.commit()
                    flash('Catalog Successfully Edited %s' % edited.name)
                    return redirect(url_for('catalogItem',
                                            catalog_path=edited.slug))
                else:
                    response = make_response(json.dumps(
                            '422 Unprocessable Entity: duplicated slug?'), 422)
                    return response
        else:
            return render_template('editCatalog.html',
                                   edited=edited, catalog=catalog)
    else:
        return 'Category 404 - Not Found', 404


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    try:
        state_random = xrange(32)  # for python2
    except NameError:
        state_random = range(32)  # for python3
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in state_random)
    login_session['state'] = state
    return render_template('login.html', STATE=state)


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
    # h = httplib2.Http()
    # result = json.loads(h.request(url, 'GET')[1])
    r = requests.get(url=url)
    result = r.json()
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        login_session['access_token'] = credentials.access_token
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    create_user(login_session, session)
#   print(u"Existing User %s Logged in" % user.name )

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += (' " style = "width: 300px; height: 300px;' +
               'border-radius: 150px;-webkit-border-radius: 150px;' +
               '-moz-border-radius: 150px;"> ')
    flash("you are now logged in as %s" % login_session['username'])
    print("Logged in!")
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    print(request.referrer)
    access_token = login_session.get('access_token')
    response = """
            <html>
            <meta http-equiv="refresh" content="2;url=/" />
            <title>Catalog - User Logout </title>
            <body>%s Redirecting...</body>
            """
    if access_token is None:
        print('Access Token is None')
        return response % 'Current user not connected.'
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
#   h = httplib2.Http()
#   result = h.request(url, 'GET')[0]

    r = requests.get(url=url)  # to support python3

#   delete sessions anyway
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']

    if r.status_code == 200:
        return response % 'Successfully disconnected.'
    else:
        return response % 'Failed to revoke token for given user.'


# JSON APIs
@app.route('/catalog/<slug>.json')
def singleItemjson(slug):
    catalog = session.query(Catalog)
    item = catalog.filter_by(slug=slug).first()
    if item:
        return jsonify(Catalog=item.serialize)
    else:
        return "Category 404 - Not Found", 404


@app.route('/catalog.json')
def wholecatalogjson():
    catalog = session.query(Catalog).filter(Catalog.id != 1).all()
    return jsonify(Catalog=[i.serialize for i in catalog])


# subtree of a category
@app.route('/catalog/subtree/<slug>.json')
def subtreejson(slug):
    catalog = session.query(Catalog)
    item = catalog.filter_by(slug=slug).first()
    if item:
        sub = subtree(item, catalog, max_depth=10)
        for i in sub:
            print(i.serialize)
        return jsonify(Catalog=[i.serialize for i in sub])
    else:
        return "Category 404 - Not Found", 404


if __name__ == '__main__':
    port_num = 8000
    try:
        port_num = int(sys.argv[1])
    except (ValueError, TypeError, IndexError):
        port_num = 8000  # default
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=port_num)
