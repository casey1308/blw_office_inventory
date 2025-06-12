from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecret'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username TEXT UNIQUE, 
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    department TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    action TEXT,
                    item TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Username already exists")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                  (request.form['username'], request.form['password']))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = request.form['username']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    department_filter = request.args.get('department')
    message = request.args.get('message')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if department_filter and department_filter != "All":
        c.execute("SELECT * FROM inventory WHERE department=?", (department_filter,))
    else:
        c.execute("SELECT * FROM inventory")
    items = c.fetchall()

    c.execute("SELECT DISTINCT department FROM inventory")
    departments = [d[0] for d in c.fetchall()]
    conn.close()

    return render_template('dashboard.html',
                           items=items,
                           username=session['username'],
                           departments=departments,
                           selected=department_filter or "All",
                           message=message)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        dept = request.form['department']
        username = session['username']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO inventory (name, department) VALUES (?, ?)", (name, dept))
        c.execute("INSERT INTO logs (username, action, item) VALUES (?, ?, ?)", 
                  (username, 'Added', f"{name} ({dept})"))
        conn.commit()
        conn.close()
        return redirect('/dashboard?message=Item+added+successfully')
    return render_template('add_item.html')

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    if 'username' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name, department FROM inventory WHERE id=?", (item_id,))
    item = c.fetchone()
    if item:
        c.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        c.execute("INSERT INTO logs (username, action, item) VALUES (?, ?, ?)", 
                  (session['username'], 'Deleted', f"{item[0]} ({item[1]})"))
    conn.commit()
    conn.close()
    return redirect('/dashboard?message=Item+deleted+successfully')

@app.route('/logs')
def view_logs():
    if 'username' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT username, action, item, timestamp FROM logs ORDER BY timestamp DESC")
    logs = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
