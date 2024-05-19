'''
db
database file, containing all the logic to interface with the sql database
'''
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path
import sqlite3

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

def check_user_exists(username):
    # Implement logic to check if the user exists in the database
    # Return True if the user exists, False otherwise
    user = get_user(username)
    return user is not None

def add_friend_request(from_username: str, to_username: str):
    with Session(engine) as session:
        # Check if both users exist
        user = session.query(User).filter_by(username=from_username).first()
        friend = session.query(User).filter_by(username=to_username).first()
        
        if not user or not friend:
            return False, "One or both users do not exist"
        
        # Check if a friend request already exists
        existing_request = session.query(FriendRequest).filter(
            FriendRequest.from_username == from_username,
            FriendRequest.to_username == to_username,
            FriendRequest.status == 'pending'
        ).first()
        
        if existing_request:
            return False, "Friend request already sent"
        
        # Create a new friend request
        new_request = FriendRequest(from_username=from_username, to_username=to_username)
        session.add(new_request)
        session.commit()
        return True, None

def get_pending_friend_requests(username: str):
    with Session(engine) as session:
        pending_requests = session.query(FriendRequest).filter(
            FriendRequest.to_username == username,
            FriendRequest.status == 'pending'
        ).all()
        return [(request.from_username, request.to_username) for request in pending_requests]

def send_friend_request(from_username, to_username):
    with Session(engine) as session:
        request = FriendRequest(from_username=from_username, to_username=to_username)
        session.add(request)
        session.commit()

def accept_friend_request(from_username: str, to_username: str):
    with Session(engine) as session:
        # Find the request
        request = session.query(FriendRequest).filter(
            FriendRequest.from_username == from_username,
            FriendRequest.to_username == to_username,
            FriendRequest.status == 'pending'
        ).first()
        
        if request:
            # Accept the request
            request.status = 'accepted'
            session.commit()
            
            # Add the friendship
            user = session.query(User).filter(User.username == from_username).first()
            friend = session.query(User).filter(User.username == to_username).first()
            if user and friend:
                user.friends.append(friend)
                friend.friends.append(user)
                session.commit()
            return True
        else:
            return False, "Request not found"

def decline_friend_request(from_username: str, to_username: str):
    with Session(engine) as session:
        # Find the request
        request = session.query(FriendRequest).filter(
            FriendRequest.from_username == from_username,
            FriendRequest.to_username == to_username,
            FriendRequest.status == 'pending'
        ).first()
        
        if request:
            # Decline the request
            session.delete(request)
            session.commit()
            return True
        else:
            return False, "Request not found"

def get_confirmed_friends(username: str):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if user:
            return [(user.username, friend.username) for friend in user.friends]
        return []

def remove_friend(username: str, friend_username: str):
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()
        friend = session.query(User).filter_by(username=friend_username).first()
            
        if not user or not friend:
            return False, "User does not exist"
     
        if friend not in user.friends:
            return False, "User is not in the friend list"
            
        # Remove friend relationship
        user.friends.remove(friend)
        friend.friends.remove(user)
        session.commit()
        return True, None

def check_friends(user1_username, user2_username):
    with Session(engine) as session:
        user1 = session.query(User).filter_by(username=user1_username).first()
        user2 = session.query(User).filter_by(username=user2_username).first()
        if user1 is None or user2 is None:
            return False
        return user1 in user2.friends
    
# 插入消息到数据库
def insert_message(sender: str, receiver: str, message: str):
    with Session(engine) as session:
        new_message = Message(sender=sender, receiver=receiver, message=message)
        session.add(new_message)
        session.commit()

# 获取某个用户的所有消息
def get_messages(username: str):
    with Session(engine) as session:
        messages = session.query(Message).filter(
            Message.receiver == username
        ).order_by(Message.timestamp.asc()).all()
        return [(msg.sender, msg.message, msg.timestamp) for msg in messages]