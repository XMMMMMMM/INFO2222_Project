'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
import db
import secrets
import bcrypt
from flask_bcrypt import Bcrypt

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)
bcrypt = Bcrypt(app)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    # verify the password.
    if not bcrypt.check_password_hash(user.password, password):
        return "Error: Password does not match!"

    return url_for('home', username=username)

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")

    # Encrypt passwords using a hash function.
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    if db.get_user(username) is None:
        db.insert_user(username, pw_hash)
        return url_for('home', username=username)
    return "Error: User already exists!"

@app.route('/add_friend', methods=['POST'])
def add_friend():
    data = request.json
    if not data:
        abort(400, description="No data provided")
        
    username = data.get("username")
    friend_username = data.get("friendUsername")
    
    # Check if username and friend_username are provided
    if not username or not friend_username:
        abort(400, description="Missing username or friend username")

    # Check if the friend exists in the database
    if not db.check_user_exists(friend_username):
        return jsonify({"success": False, "error": "User does not exist"})

    # Add friend to the database
    success = db.add_friend_request(username, friend_username)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to add friend"})

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)
    return render_template("home.jinja", username=request.args.get("username"))

@app.route("/home?username=<username>", methods=['GET'])
def get_friends():
    username = request.args.get('username')
    if not username:
        abort(400, description="username not provided")
    friend_list = db.get_friend_list(username)
    if friend_list is None:
        friend_list = []
    return jsonify({"success": True, "friends": friend_list})

@app.route('/pending_requests')
def pending_requests():
    username = request.args.get('username')
    if not username:
        abort(400, description="username not provided")
    
    # Fetch pending friend requests from the database
    requests = db.get_pending_friend_requests(username)
    
    if requests is not None:
        return jsonify({"success": True, "requests": requests})
    else:
        return jsonify({"success": False, "error": "Failed to fetch pending friend requests"})

@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request():
    data = request.json
    from_username = data.get('from_username')
    to_username = data.get('to_username')
    db.accept_friend_request(from_username, to_username)
    return jsonify(success=True)

@app.route('/decline_friend_request', methods=['POST'])
def decline_friend_request():
    data = request.json
    from_username = data.get('from_username')
    to_username = data.get('to_username')
    db.decline_friend_request(from_username, to_username)
    return jsonify(success=True)

@app.route('/confirmed_friends')
def confirmed_friends():
    username = request.args.get('username')
    if not username:
        abort(400, description="username not provided")
    
    # Fetch confirmed friends from the database
    friends = db.get_confirmed_friends(username)
    
    if friends is not None:
        return jsonify({"success": True, "friends": friends})
    else:
        return jsonify({"success": False, "error": "Failed to fetch confirmed friends"})

@app.route('/chat_request', methods=['POST'])
def chat_request():
    # Get data from request
    data = request.json
    sender = data.get('sender')
    receiver = data.get('receiver')
    # Check if the receiver exists in the database
    user_exists = db.check_user_exists(receiver)
    if not user_exists:
        # If Receiver doesn't exist
        return jsonify({"success": False, "error": "User does not exist"})
    # Check if the sender and receiver are already friends
    are_friends = db.check_friends(sender, receiver)
    if are_friends:
        # If already friends, allow chat
        return jsonify({"success": True, "status": "friends"})
    else:
        return jsonify({"success": False, "error": "You are not friends with this user"})

if __name__ == '__main__':
    socketio.run(app, ssl_context=('./certs/localhost.crt', './certs/localhost.key'))