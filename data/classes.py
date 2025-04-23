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
    """Класс, представляющий тему/раздел на форуме.
    
    Attributes:
        id (int): Уникальный идентификатор темы (первичный ключ);
        title (str): Название темы (максимум 255 символов);
        messages (relationship): Связь с сообщениями в этой теме;
        description (str): Описание темы;
        slug (str): транслитерация для отображения темы в ссылке;
        status (str): Статус темы ('active', 'closed');
    """
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
    """Класс, представляющий сообщение в теме форума.
    
    Attributes:
        id (int): Уникальный идентификатор сообщения (первичный ключ);
        content (str): Текст сообщения;
        topic_id (int): Идентификатор темы, к которой относится сообщение (внешний ключ);
        topic (relationship): Связь с темой сообщения;
        author (str): Имя автора сообщения (внешний ключ к таблице users);
        author_id (relationship): Связь с пользователем;
        created_at (datetime): Дата и время создания сообщения (текущее время);
    """
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
    """Форма для входа пользователя в WTForum.
    
    Fields:
        name (StringField): Поле для ввода имени пользователя (обязательное);
        password (PasswordField): Поле для ввода пароля (обязательное);
        remember_me (BooleanField): Чекбокс "Запомнить меня";
        submit (SubmitField): Кнопка для отправки формы;
    """
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Форма для регистрации нового пользователя.
    
    Fields:
        name (StringField): Поле для ввода имени пользователя (обязательное);
        password (PasswordField): Поле для ввода пароля (обязательное);
        password_again (PasswordField): Поле для повторного ввода пароля (обязательное);
        email (EmailField): Поле для ввода email (обязательное);
        submit (SubmitField): Кнопка для отправки формы;
    """
    name = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat the password', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Register')


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    """Класс, представляющий пользователя системы.
    
    Наследуется от UserMixin (для Flask-Login) и SerializerMixin (для сериализации).
    
    Attributes:
        id (int): Уникальный идентификатор пользователя (первичный ключ);
        name (str): Имя пользователя;
        hashed_password (str): Хэшированный пароль пользователя;
        email (str): Email пользователя (уникальный);
        date (datetime): Дата регистрации пользователя (текущее время);
        status (str): Статус пользователя ('user');
        ava_photo (str): Путь к файлу аватара пользователя (максимум 120 символов);
    """
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=False, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String, default='user')
    ava_photo = sqlalchemy.Column(sqlalchemy.String(120))

    def get_id(self):
        """Метод, требуемый Flask-Login для получения идентификатора пользователя."""
        return str(self.id)  # Преобразуем в строку (стандарт для сессий)

    def changing_password_to_hash_password(self, password):
        """Хэширует переданный пароль и сохраняет его в поле hashed_password.
        
        Args:
            password (str): Пароль для хэширования;
        """
        self.hashed_password = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        """Проверяет, соответствует ли переданный пароль хэшированному паролю пользователя.
        
        Args:
            password (str): Пароль для проверки;
            
        Returns:
            bool: True если пароль верный, иначе False;
        """
        return hashlib.sha256(password.encode()).hexdigest() == self.hashed_password

    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}')"

