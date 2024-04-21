'''
socket_routes
file containing all the routes related to socket.io
'''

# from Crypto.PublicKey import DH
# from Crypto.Random import get_random_bytes
from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler
@socketio.on("send")
def send(username, message, room_id):
    emit("incoming", (f"{username}: {message}"), to=room_id)
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"
    
    # Check if sender and receiver are friends
    are_friends = db.check_friends(sender_name, receiver_name)
    if not are_friends:
        return "You are not friends with this user. Please send a friend"

    room_id = room.get_room_id(receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        # emit to everyone in the room except the sender
        emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # emit only to the sender
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)
    return room_id

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)


# def generate_dh_keys():
#     # 生成密钥参数
#     params = DH.generate_parameters(generator=2, key_size=2048)
#     # 生成密钥对
#     private_key = params.generate_private_key()
#     public_key = private_key.public_key().export_key()
#     return private_key, public_key

# @socketio.on('join_room')
# def handle_join_room(data):
#     # 每个用户生成自己的DH密钥对
#     private_key, public_key = generate_dh_keys()
#     room = data['room']
#     join_room(room)
#     # 发送公钥给房间内的其他用户
#     emit('exchange_keys', {'public_key': public_key.decode('utf-8')}, room=room)

# @socketio.on('receive_key')
# def handle_key_exchange(data):
#     other_public_key_data = data['public_key']
#     other_public_key = DH.import_key(other_public_key_data.encode('utf-8'))
#     # 计算共享密钥
#     shared_key = private_key.exchange(other_public_key)
#     # 可以使用这个共享密钥来加密后续的通信