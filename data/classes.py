import datetime
import sqlalchemy
from sqlalchemy import orm
import hashlib
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from database.db_session import SqlAlchemyBase


class Topic(SqlAlchemyBase):
    __tablename__ = 'topics'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    messages = orm.relationship("Message", back_populates="topic")
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    slug = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)

    def __repr__(self):
        return f"Topic(id={self.id}, title='{self.title}')"


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True ,autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    topic_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('topics.id'), nullable=False)
    topic = orm.relationship("Topic", back_populates="messages")
    author = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('users.name'), nullable=False)
    author_id = orm.relationship("User", backref="messages")
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"Message(id={self.id}, content='{self.content[:10]}...')"


class LoginForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat the password', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Register')


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=False, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String, default='user')
    ava_photo = sqlalchemy.Column(sqlalchemy.String(120))

    def get_id(self):  # Flask-Login требует метод get_id()
        return str(self.id)  # Преобразуем в строку (стандарт для сессий)

    def changing_password_to_hash_password(self, password):
        self.hashed_password = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest() == self.hashed_password

    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}')"

