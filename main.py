from flask import Flask, render_template, redirect
from data.classes import Topic, Message
from data.forms import AddTopicForm
from database import db_session
from data.functions import slugify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wtforum_secret_key'


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
    }
    print(messages)
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
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти'  # в зависимости от того, авторизован ли пользователь
    }
    form = AddTopicForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('add_topic.html', title='WTForum. Добавление темы.', form=form, **data)


def main():
    db_session.global_init("The_greatest_project_of_our_time/database/forum_db.sqlite")
    app.run(debug=True)


if __name__ == '__main__':
    main()
