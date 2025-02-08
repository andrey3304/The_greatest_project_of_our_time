from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Временное хранилище для тем форума
threads = []

@app.route('/')
def index():
    return render_template('index.html', threads=threads)

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

if __name__ == '__main__':
    app.run(debug=True)
