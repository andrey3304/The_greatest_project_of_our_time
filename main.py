from flask import Flask, render_template
from database import db_session

app = Flask(__name__)


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


if __name__ == '__main__':
    db_session.global_init("database/forumdb.sqlite")
    app.run(debug=True)
