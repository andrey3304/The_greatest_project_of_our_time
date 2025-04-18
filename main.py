from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_socketio import SocketIO, emit, join_room

from data import users_api
from data.classes import Topic, Message, LoginForm, RegisterForm, User
from data.config import DATABASE_ADRESS
from data.external_apis import WeatherApiClient
from data.forms import AddTopicForm
from data.functions import make_slug
from database import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wtforum_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)
api_client = WeatherApiClient()


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
    topics = db_sess.query(Topic).filter(Topic.status == 'ok')
    is_auth = current_user.is_authenticated

    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти' if not is_auth else current_user.name,
        'url_account_or_login': '/login' if not is_auth else '#',
        'topics_list': topics
    }
    return render_template('index.html', **data)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    equation, answer = generate_equation_for_captcha()
    captcha_error = None

    if form.validate_on_submit():
        # Проверяем капчу только если форма валидна
        try:
            expected_answer = int(request.form.get('expected_answer', 0))
            user_answer = int(request.form.get('user_answer', 0))

            if user_answer != expected_answer:
                equation, answer = generate_equation_for_captcha()
                captcha_error = "Wrong answer, try again."
            else:
                # Капча верна, проверяем логин/пароль
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.name == form.name.data).first()

                if not (user and user.check_password(form.password.data)):
                    raise ValueError
                if user and user.check_password(form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    return redirect("/")
                else:
                    message = "Incorrect username or password"
        except ValueError:
            equation, answer = generate_equation_for_captcha()
            captcha_error = "Please enter a valid number for the captcha"

    return render_template('login.html',
                           title='Authorization',
                           form=form,
                           equation=equation,
                           answer=answer,
                           captcha_error=captcha_error)


@app.route('/register', methods=['GET', 'POST'])
def registration_new_user():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Passwords don't match")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="There is already such a user")
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="username is busy")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.changing_password_to_hash_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Registration', form=form)


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
    topics = db_sess.query(Topic).filter(Topic.status == 'ok')
    messages = db_sess.query(Message).join(Topic).filter(Topic.slug == str(topic_slug)).all()
    is_auth = current_user.is_authenticated
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти' if not is_auth else current_user.name,
        'url_account_or_login': '/login' if not is_auth else '#',
        'topics_list': topics,
        'messages': messages,
        'topic_slug': topic_slug,
    }
    return render_template('show_topic.html', **data)


@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).filter(Topic.status == 'ok')
    db_sess.close()
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти',
        'topics_list': topics,
    }

    form = AddTopicForm()

    if request.method == 'POST' and form.validate_on_submit():
        topic = Topic()
        topic.title = form.name.data
        topic.description = form.about.data
        topic.slug = make_slug(form.name.data)
        topic.status = 'wait'

        db_sess.add(topic)
        db_sess.commit()
        db_sess.close()
        return redirect('/')
    return render_template('add_topic.html', title='WTForum. Добавление темы.', form=form, **data)


@socketio.on('new_message')
def handle_new_message(data):
    topic_slug = data['topic_slug']
    message_text = data['message']
    message_author = data['author']


    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).filter(Topic.slug == str(topic_slug)).first()


    if topic:
        message = Message()
        if message_text.strip().split()[0] == 'Информация':
            city = api_client.get_city_weather_info(message_text.strip().split()[1])
            if city != 'error':
                name = city['city']
                country = city['country']
                localtime = city['localtime']
                temp = city['temp']
                text = city['text']
                wind = city['wind']
                message.content = f'Бот. Город: {name}. Страна: {country}. Местное время: {localtime}. Температура: {temp}℃. Погода: {text}. Ветер: {wind} м.с.'
                message_text = message.content
            else:
                message.content = message_text
        else:
            message.content = message_text
        message.author = message_author
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



@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/admin-panel')
@login_required #
def admin_panel():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.name == str(current_user.name)).first()
    if user.status == 'admin':
        unchecked_topics = db_sess.query(Topic).filter(Topic.status == 'wait')
        return render_template('admin.html', topics=unchecked_topics)
    else:
        return redirect("/admin-error")


@app.route('/admin-error')
def admin_error():
    return render_template('error_admin.html')


@app.route('/admin/themes/<action>', methods=['POST'])
def topic_admin(action):
    themes_id = request.json['theme_ids']
    db_sess = db_session.create_session()
    status = 'reject 'if action == 'reject' else 'ok'
    for i in themes_id:
        topic = db_sess.query(Topic).filter(Topic.id == int(i)).first()
        topic.status = status
        db_sess.commit()
    db_sess.close()
    return {'status': 'ok'}


def main():
    app.register_blueprint(users_api.blueprint)
    db_session.global_init(DATABASE_ADRESS)
    app.run(debug=True)


if __name__ == '__main__':
    main()
