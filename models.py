'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Column, ForeignKey, Table, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict
from datetime import datetime

# data models
class Base(DeclarativeBase):
    pass

pending_requests_table = Table(
    'pending_requests',
    Base.metadata,
    Column('requester_username', String, ForeignKey('user.username'), primary_key=True),
    Column('requestee_username', String, ForeignKey('user.username'), primary_key=True)
)

user_friend_table = Table(
    'username',
    Base.metadata,
    Column('user_username', String, ForeignKey('user.username'), primary_key=True),
    Column('friend_username', String, ForeignKey('user.username'), primary_key=True)
)

class FriendRequest(Base):
    __tablename__ = 'friend_request'
    from_username = Column(String, ForeignKey('user.username'), primary_key=True)
    to_username = Column(String, ForeignKey('user.username'), primary_key=True)
    status = Column(String, default='pending') 
    from_user = relationship("User", foreign_keys=[from_username])
    to_user = relationship("User", foreign_keys=[to_username])

    def __repr__(self):
        return f"<FriendRequest(from={self.from_username}, to={self.to_username})>"

# model to store user information
class User(Base):
    __tablename__ = "user"
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    friends = relationship(
        'User',
        secondary=user_friend_table,
        primaryjoin=username == user_friend_table.c.user_username,
        secondaryjoin=username == user_friend_table.c.friend_username,
        back_populates='friends'
    )
    pending_requests_sent = relationship(
        "FriendRequest",
        foreign_keys="FriendRequest.from_username",
        back_populates="from_user"
    )   
    pending_requests_received = relationship(
        "FriendRequest",
        foreign_keys="FriendRequest.to_username",
        back_populates="to_user"
    )
    
    def __repr__(self):
        return f"<User(username={self.username})>"
    
class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    sender = Column(String, ForeignKey('user.username'), nullable=False)
    receiver = Column(String, ForeignKey('user.username'), nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    sender_user = relationship('User', foreign_keys=[sender])
    receiver_user = relationship('User', foreign_keys=[receiver])

    def __repr__(self):
        return f"<Message(sender={self.sender}, receiver={self.receiver}, message={self.message}, timestamp={self.timestamp})>"

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    def get_receiver_in_room(self, sender, room_id):
        for user, room in self.dict.items():
            if room == room_id and user != sender:
                return user
        return None
class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(50), nullable=False)
    comments = relationship("Comment", back_populates="article")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author = Column(String(50), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'))
    article = relationship("Article", back_populates="comments")