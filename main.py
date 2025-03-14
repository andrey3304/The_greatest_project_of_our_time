from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    data = {
        'main_title': 'WTForum. Главная страница',
        'label_account_or_login': 'Войти'  # в зависимости от того, авторизован ли пользователь
           }
    return render_template('index.html', **data)


@app.route('/topics/<slug:topic_name>')
def show_topic():
    pass


if __name__ == '__main__':
    app.run(debug=True)
