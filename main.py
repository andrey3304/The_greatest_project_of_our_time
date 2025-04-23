from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.routing import Rule
from loguru import logger
import os

from data import users_api
from data.classes import Topic, Message, LoginForm, RegisterForm, User
from data.config import DATABASE_ADRESS
from data.external_apis import WeatherApiClient
from data.forms import AddTopicForm
from data.functions import make_slug, generate_equation_for_captcha, generate_name_for_avatar_photo, allowed_file
from database import db_session


# Настройка Flask и socketio
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wtforum_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Куда перенаправлять неавторизованных пользователей

# Натсройка API
api_client = WeatherApiClient()


# Настройка логгера
logger.add('database/logging/debug.json', format='{time} {level} {message}',
           level='DEBUG', rotation='10:00', compression='zip',
           serialize=True)


@app.route('/')
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
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



@app.route('/profile_page', methods=['GET', 'POST'])
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
def profile_page():
    """
    Обрабатывает запросы к странице профиля пользователя.
    При GET-запросе отображает шаблон profile.html.
    При POST-запросе может обрабатывать данные формы изменения профиля.
    Возвращает:
        render_template: Отрендеренный шаблон страницы профиля
    """
    return render_template('profile.html', user=current_user,
                         title=f"Профиль {current_user.name}")


@app.route('/upload_avatar', methods=['POST'])
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('profile_page'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('profile_page'))

    if file and allowed_file(file.filename):
        if file.content_length > 2 * 1024 * 1024:  # 2MB
            flash('Файл слишком большой (макс. 2MB)', 'error')
            return redirect(url_for('profile_page'))

        # Генерируем уникальное имя
        unique_filename = generate_name_for_avatar_photo(user_id=current_user.id, filename=file.filename)

        # Сохраняем файл
        upload_folder = os.path.join(
            current_app.root_path,
            'static',
            'uploads',
            'avatars'
        )
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, unique_filename))

        # Обновляем БД
        db_sess = db_session.create_session()
        try:
            # Получаем пользователя из текущей сессии
            user = db_sess.get(User, current_user.id)
            if user:
                user.ava_photo = f"uploads/avatars/{unique_filename}"  # Используем unique_filename!
                db_sess.commit()
                flash('Аватар успешно обновлён!', 'success')
            else:
                flash('Пользователь не найден', 'error')
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка: {str(e)}', 'error')
        finally:
            db_sess.close()
        return redirect(url_for('profile_page'))
    flash('Недопустимый формат файла', 'error')
    return redirect(url_for('profile_page'))


# Загрузчик пользователя (для Flask-Login)
@login_manager.user_loader
@logger.catch()
def load_user(user_id):
    # Здесь должна быть загрузка из БД
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    db_sess.close()
    return user  # Возвращает объект User или None


@app.route('/logout')
@login_required
@logger.catch()
def logout():
    logout_user()  # Удаляет данные пользователя из сессии
    flash("Вы вышли из системы.", "info")
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@logger.catch()
def login():
    """
    Обрабатывает логин пользователя с защитой капчей.
    При GET-запросе отображает форму входа.
    При POST-запросе:
        1. Проверяет корректность капчи
        2. Проверяет логин и пароль
        3. При успешной аутентификации перенаправляет на главную страницу
    В случае ошибок отображает соответствующие сообщения.
    Возвращает:
        render_template: Отрендеренный шаблон login.html или redirect на главную страницу
    """
    form = LoginForm()
    equation, answer = generate_equation_for_captcha()
    captcha_error = None
    message_error = None

    # Если пользователь уже авторизован, перенаправляем его на главную страницу
    if current_user.is_authenticated:
        return redirect(url_for('/'))

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
                    message_error = "Incorrect username or password"
                if user and user.check_password(form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    return redirect("/")
                else:
                    message_error = "Incorrect username or password"
        except ValueError:
            equation, answer = generate_equation_for_captcha()
            captcha_error = "Please enter a valid number for the captcha"

    return render_template('login.html',
                           title='Authorization',
                           form=form,
                           equation=equation,
                           answer=answer,
                           captcha_error=captcha_error,
                           message_error=message_error)


@app.route('/register', methods=['GET', 'POST'])
@logger.catch()
def registration_new_user():
    """
    Обрабатывает регистрацию новых пользователей.
    При GET-запросе отображает форму регистрации.
    При POST-запросе:
        1. Проверяет совпадение паролей
        2. Проверяет уникальность email и имени пользователя
        3. Создает нового пользователя и хэширует его пароль
        4. Перенаправляет на страницу входа после успешной регистрации
    В случае ошибок отображает соответствующие сообщения.
    Возвращает:
        render_template: Отрендеренный шаблон register.html или redirect на страницу входа
    """
    equation, answer = generate_equation_for_captcha()
    captcha_error = None
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            equation, answer = generate_equation_for_captcha()
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Passwords don't match",
                                       captcha_error=captcha_error,
                                       equation=equation,
                                       answer=answer)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            equation, answer = generate_equation_for_captcha()
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="There is already such a user",
                                       captcha_error=captcha_error,
                                       equation=equation,
                                       answer=answer)
        if db_sess.query(User).filter(User.name == form.name.data).first():
            equation, answer = generate_equation_for_captcha()
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="username is busy",
                                       captcha_error=captcha_error,
                                       equation=equation,
                                       answer=answer)

        # Проверяем капчу только если форма валидна
        try:
            expected_answer = int(request.form.get('expected_answer', 0))
            user_answer = int(request.form.get('user_answer', 0))

            if user_answer != expected_answer:
                equation, answer = generate_equation_for_captcha()
                captcha_error = "Wrong answer, try again."
                return render_template('register.html',
                                       title='Registration',
                                       form=form,
                                       captcha_error=captcha_error,
                                       equation=equation,
                                       answer=answer)
        except ValueError:
            equation, answer = generate_equation_for_captcha()
            captcha_error = "Please enter a valid number for the captcha"
            return render_template('register.html',
                                   title='Registration',
                                   form=form,
                                   captcha_error=captcha_error,
                                   equation=equation,
                                   answer=answer)

        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.changing_password_to_hash_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html',
                           title='Registration', form=form,
                           captcha_error=captcha_error,
                           equation=equation,
                           answer=answer)


@app.route('/topics/<topic_slug>')
@logger.catch()
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
@logger.catch()
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
@logger.catch()
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
@logger.catch()
def on_join(data):
    topic_slug = data['topic_slug']
    join_room(topic_slug)
    print(f"Client joined room: {topic_slug}")



@app.route('/about')
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
def logout():
    logout_user()
    return redirect("/")


@app.route('/admin-panel')
@login_required  # защита роута от намереннового избежания авторизации
@logger.catch()
def admin_panel():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.name == str(current_user.name)).first()
    if user.status == 'admin':
        unchecked_topics = db_sess.query(Topic).filter(Topic.status == 'wait')
        return render_template('admin.html', topics=unchecked_topics)
    else:
        return redirect("/admin-error")


@app.route('/admin-error')
@logger.catch()
def admin_error():
    return render_template('error_admin.html')


@app.route('/admin/themes/<action>', methods=['POST'])
@logger.catch()
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


@logger.catch()
def main():
    app.register_blueprint(users_api.blueprint)
    db_session.global_init(DATABASE_ADRESS)
    app.url_map.add(Rule('/', endpoint='login', redirect_to='/login'))  # автоматически перенаправляет на /login
    app.run(debug=True)


if __name__ == '__main__':
    main()
