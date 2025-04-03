from flask_socketio import SocketIO, emit, join_room
from flask import Flask, render_template, redirect, flash, url_for
from sqlalchemy.testing.suite.test_reflection import users

from data.classes import Topic, Message, LoginForm, RegisterForm, User
from data.forms import AddTopicForm
from database import db_session
from data.functions import slugify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wtforum_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")




@app.route('/')
def index():
    """
       Эта функция обрабатывает главную страницу WTForum. Она подготавливает данные для шаблона index.html и отображает его.

       Параметры:
       Нет

       Возвращает:
       render_template: Отображенный HTML-шаблон с предоставленными данными.
    """
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).all()
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти',  # в зависимости от того, авторизован ли пользователь
        'topics_list': topics
           }
    return render_template('index.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def registration_new_user():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Passwords don't match")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="There is already such a user")
        if db_sess.query(User).filter(User.name == form.name.data):
            print("name")
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="username is busy")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/topics/<topic_slug>')
def show_topic(topic_slug):
    """
        Эта функция обрабатывает отображение определенной страницы темы в WTForum.
        Она подготавливает данные для шаблона show_topic.html и отображает его.

        Параметры:
        topic_name (str): Название темы для отображения. Это получается из URL.

        Возвращает:
        render_template: Отображенный HTML-шаблон с предоставленными данными.
    """
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).all()
    messages = db_sess.query(Message).join(Topic).filter(Topic.slug == str(topic_slug)).all()
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти',
        'topics_list': topics,
        'messages': messages,
        'topic_slug': topic_slug,
    }
    return render_template('show_topic.html', **data)


@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    """
        Эта функция обрабатывает добавление новой темы в WTForum. Она подготавливает данные для шаблона 'add_topic.html'
        и отображает его. Если форма отправлена и проверена, она перенаправляет пользователя на главную страницу.

        Параметры:
        - Нет

        Возвращает:
        - render_template: Отображенный шаблон 'add_topic.html' с предоставленными данными. Если форма отправлена и проверена,
                          возвращается перенаправление на главную страницу ('/').
    """
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).all()
    db_sess.close()
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти',
        'topics_list': topics,
    }
    form = AddTopicForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('add_topic.html', title='WTForum. Добавление темы.', form=form, **data)


@socketio.on('new_message')
def handle_new_message(data):
    print(data)
    topic_slug = data['topic_slug']
    message_text = data['message']

    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).filter(Topic.slug == str(topic_slug)).first()

    if topic:
        message = Message()
        message.content = message_text
        message.topic_id = topic.id
        db_sess.add(message)
        db_sess.commit()

        emit('update_chat', {'topic_slug': topic_slug, 'message': message_text}, room=str(topic_slug))
    db_sess.close()


@socketio.on('join')
def on_join(data):
    topic_slug = data['topic_slug']
    join_room(topic_slug)
    print(f"Client joined room: {topic_slug}")


def main():
    db_session.global_init("database/forum_db.sqlite")
    app.run(debug=True)


if __name__ == '__main__':
    main()
