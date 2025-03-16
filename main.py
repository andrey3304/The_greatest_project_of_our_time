from flask import Flask, render_template, redirect
from data.classes import Topic
from data.forms import AddTopicForm
from database import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wtforum_secret_key'


@app.route('/')
def index():
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти'  # в зависимости от того, авторизован ли пользователь
           }
    return render_template('index.html', **data)


@app.route('/topics/<topic_name>')
def show_topic():
    pass


@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
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
