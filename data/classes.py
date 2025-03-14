import datetime
import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from database.db_session import SqlAlchemyBase


class Topic(SqlAlchemyBase):
    __tablename__ = 'topics'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    messages = orm.relationship("Message", back_populates="topic")
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    def __repr__(self):
        return f"Topic(id={self.id}, title='{self.title}')"


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True ,autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    topic_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('topics.id'), nullable=False)
    topic = orm.relationship("Topic", back_populates="messages")
    # author_id = ... связь с моделью User
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"Message(id={self.id}, content='{self.content[:10]}...')"

