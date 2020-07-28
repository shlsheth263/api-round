from flask import Flask, render_template, request, session
import mysql.connector
from cryptography.fernet import Fernet
import datetime


app = Flask(__name__)
key = b'pRmgMa8T0INjEAfksaq2aafzoZXEuwKI7wDe4c1F8AY='
cipher_suite = Fernet(key)


def connect_to_mysql():
    conn = mysql.connector.connect(
        host="us-cdbr-east-02.cleardb.com",
        user="bd263bb3993eab",
        passwd="67cd7db9",
        database='heroku_53e25e16cd304df'
    )
    return conn


def get_notes(user_id):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute("select note, created_at from notes where user_id = " + str(user_id))
    results = list(cursor.fetchall())
    notes = []
    for result in results:
        note = (result[0]).encode('utf-8')
        dec_note = cipher_suite.decrypt(note).decode('utf-8')
        p = list(result)
        p[0] = dec_note
        notes.append(p)
    return notes


def get_user_details(info):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    if "name" in info.keys():
        query = "select * from users where name = '" + info["name"] + "'"
    else:
        query = "select * from users where id = " + str(info["sess_id"])
    cursor.execute(query)
    results = cursor.fetchall()
    if len(results) > 0:
        results = results[0]
    return results


@app.route('/')
def home():
    session.clear()
    return render_template("login.html", text=None)


@app.route('/<sess_id>/new_note', methods=["GET", "POST"])
def new_note(sess_id):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    if request.method == 'GET':
        if str(session.get("id")) == str(sess_id):
            user = get_user_details({"sess_id": sess_id})
            return render_template("add.html", session=sess_id, name=user[1])
        else:
            return '<script>alert("Please Login");</script>'
    else:
        note = str(request.form['note']).encode('utf-8')
        encrypted_note = cipher_suite.encrypt(note)
        now = datetime.datetime.now()
        created_at = now.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO notes (user_id, note, created_at) VALUES (%s,%s,%s)",
                       (sess_id, encrypted_note, created_at))
        conn.commit()
        notes = get_notes(sess_id)
        user = get_user_details({"sess_id": sess_id})
        return render_template('home.html', text=notes, session=sess_id, name=user[1])


@app.route('/register', methods=["GET", "POST"])
def register():
    conn = connect_to_mysql()
    cursor = conn.cursor()
    if request.method == 'GET':
        return render_template("register.html")
    else:
        name = request.form['name']
        password = request.form['password'].encode('utf-8')
        encrypted_password = cipher_suite.encrypt(password)
        now = datetime.datetime.now()
        created_at = now.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO users (name, password, created_at) VALUES (%s,%s,%s)",
                       (name, encrypted_password, created_at))
        conn.commit()
        user = get_user_details({"name": name})
        session['id'] = user[0]
        notes = get_notes(user[0])
        return render_template("home.html", text=notes, session=user[0], name=name)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = list(get_user_details({"name": name}))
        if len(user) > 0:
            password_stored = (user[2]).encode('utf-8')
            if cipher_suite.decrypt(password_stored).decode('utf-8') == password:
                session['id'] = user[0]
                passwords = get_notes(user[0])
                return render_template("home.html", text=passwords, session=user[0], name=user[1])
            else:
                return '<script>alert("Invalid Credentials");</script>'
        else:
            return '<script>alert("USER NOT FOUND");</script>'
    else:
        return render_template("login.html")


if __name__ == '__main__':
    app.secret_key = "abc123"
    app.run(debug=True, port=5011)
