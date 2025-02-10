from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Временное хранилище для тем и сообщений форума
threads = ['Общее', 'Другое']
messages = [
    {'id': '#1',
     'text': 'Привет! Как дела? У меня достаточно хорошо.'
     },
    {'id': '#2',
     'text': ' У меня плохо!'
     },
{'id': '#1',
     'text': 'Привет! Как дела? У меня достаточно хорошо.'
     },
    {'id': '#2',
     'text': ' У меня плохо!'
     },
{'id': '#1',
     'text': 'Привет! Как дела? У меня достаточно хорошо.'
     },
    {'id': '#2',
     'text': ' У меня плохо!'
     },
{'id': '#1',
     'text': 'Привет! Как дела? У меня достаточно хорошо.'
     },
    {'id': '#2',
     'text': ' У меня плохо!'
     },
]


@app.route('/')
def index():
    return render_template('index.html', topics=threads, messages=messages)


@app.route('/thread/<int:thread_id>')
def thread(thread_id):
    if thread_id < len(threads):
        thread_data = threads[thread_id]
        return render_template('thread.html', thread=thread_data)
    return "Тема не найдена", 404


@app.route('/create_thread', methods=['GET', 'POST'])
def create_thread():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        threads.append({'title': title, 'content': content})
        return redirect(url_for('index'))
    return render_template('create_thread.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
