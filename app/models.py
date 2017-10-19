import sys

from flask import current_app, request

from flask_login import UserMixin, AnonymousUserMixin


from . import db, login_manager
import hashlib

import flask_whooshalchemy 
from jieba.analyse import ChineseAnalyzer
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request
from datetime import datetime


  
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_name = db.Column(db.String(64))
    
class Upvote(db.Model):
    __tablename__ = 'upvote'
    id = db.Column(db.Integer, primary_key=True)
    upvoter = db.Column(db.Integer)
    answerid =  db.Column(db.Integer)
    descr =  db.Column(db.Integer)

class FocusTagQues(db.Model):
    __tablename__ = 'focustagques'
    id = db.Column(db.Integer, primary_key=True)
    personid = db.Column(db.Integer, db.ForeignKey('user.id'))
    focusedid = db.Column(db.Integer, db.ForeignKey('items.id'))
 


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

class Comment(db.Model):   
    __tablename__ =  'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    itemid = db.Column(db.Integer, db.ForeignKey('items.id'))
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    deleted = db.Column(db.Integer, default = 0)

class Items(db.Model):
    __tablename__ = 'items'    
    id = db.Column(db.Integer, primary_key=True)    
    title_or_ans = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    types = db.Column(db.Integer)
    ques_id = db.Column(db.Integer, db.ForeignKey('question.id'), default = 0)
    art_id = db.Column(db.Integer, db.ForeignKey('article.id'), default = 0)
    ans_id = db.Column(db.Integer, db.ForeignKey('answer.id'), default = 0)
    items_ = db.relationship('PostTag', backref='items_')
    itemss_ = db.relationship('Comment', backref='items_')
    thankrel = db.relationship('Thank', backref='items')
    focusrel = db.relationship('FocusTagQues', backref='items')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    deleted = db.Column(db.Integer, default = 0)

class Question(db.Model):
    __tablename__ = 'question'    
    id = db.Column(db.Integer, primary_key=True)    
    description = db.Column(db.Text)
    question = db.relationship('Items', backref='question')

class Article(db.Model):
    __tablename__ = 'article'    
    id = db.Column(db.Integer, primary_key=True)    
    content = db.Column(db.Text)
    article = db.relationship('Items', backref='article')


class Answer(db.Model):
    __tablename__ = 'answer'    
    id = db.Column(db.Integer, primary_key=True)    
    belongtoques = db.Column(db.Integer)
    upvote = db.Column(db.Integer, default=0)
    downvote = db.Column(db.Integer, default=0)
    answer = db.relationship('Items', backref='answer')

class PostTag(db.Model):
    __tablename__ = 'posttag'
    id = db.Column(db.Integer, primary_key=True)
    postid = db.Column(db.Integer)
    tagid = db.Column(db.Integer, db.ForeignKey('items.id'))



class Thank(db.Model):   
    __tablename__ =  'thank'
    id = db.Column(db.Integer, primary_key=True)
    personid = db.Column(db.Integer,db.ForeignKey('user.id'))
    postid = db.Column(db.Integer,db.ForeignKey('items.id'))

class User(db.Model, UserMixin):    
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    posts = db.relationship('Items', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    ups = db.Column(db.Integer,default=0)
    avatar_hash = db.Column(db.String(32))
    email = db.Column(db.String(64), unique=True, index=True)
    location = db.Column(db.String(64))
    thanks = db.Column(db.Integer, default = 0)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text())
    user_ = db.relationship('Comment', backref='user_', lazy='dynamic')
    thankrel = db.relationship('Thank', backref='user', lazy='dynamic')
    focusrel = db.relationship('FocusTagQues', backref='user') 
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email == '491903644@qq.com':
            self.role = Role.query.get(1)
        if self.role is None:          
            self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
    
    def is_anony(self):
        return self.confirmed  == False

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def can(self, permissions ):
            return self.role is not None and (self.role.permissions & permissions) == permissions
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True               	
    
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user, followed_name= user.name)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_following_post(self, postid):
        ftq = FocusTagQues.query.filter(FocusTagQues.personid == self.id).filter(FocusTagQues.focusedid == postid).first()
        return ftq is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

class AnonymousUser(AnonymousUserMixin):
    def is_anony(self):
        return True

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Permission:  
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    RAISE_QUESTION = 0x10


class Role(db.Model):  
    __tablename__ =  'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES|
                     Permission.RAISE_QUESTION , True)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()
        

