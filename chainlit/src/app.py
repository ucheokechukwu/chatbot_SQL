import os
import psycopg2
from flask import Flask, render_template, request

app = Flask(__name__)

# Default PostgreSQL server credentials
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = '5432'
DEFAULT_USERNAME = 'student'
DEFAULT_PASSWORD = 'student'
DEFAULT_DATABASE = 'northwind'


def save_postgres_log_params(host, port, username, password, database):
    ### save the new postgres login settings###

    postgres_log_params = [host, port, username,
                           password, database]
    f = open('../data/postgres_login', 'w')
    for param in postgres_log_params:
        f.write(param+'\n')
    f.close()
    os.system("chainlit run chainlit_app.py -w")
    return f"Connected to PostgreSQL server {host}, database {database} as {username}"


def save_chat_gpt(chat_gpt_select):
    ### saves the chatGPT login settings ###
    f = open('../data/chat_gpt_', 'w')
    f.write(chat_gpt_select)
    f.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chat_gpt_select = request.form.get('option')
        save_chat_gpt(chat_gpt_select)

        host = request.form.get('host')
        port = request.form.get('port')
        username = request.form.get('username')
        password = request.form.get('password')
        database = request.form.get('database')

        result = save_postgres_log_params(
            host, port, username, password, database)
        print(result)
        return render_template('result.html', result=result)
    return render_template('index.html',
                           host=DEFAULT_HOST,
                           port=DEFAULT_PORT,
                           username=DEFAULT_USERNAME,
                           password=DEFAULT_PASSWORD,
                           database=DEFAULT_DATABASE)


if __name__ == '__main__':
    app.run(debug=True)
