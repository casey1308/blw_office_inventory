from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# === MySQL Config ===
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Uzumymw1308",  # Change this for security
    database="inventory_db"
)
cursor = db.cursor()

# === Auto-create tables ===
cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item VARCHAR(255),
        department VARCHAR(100),
        office VARCHAR(100),
        quantity INT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(255)
    )
""")
db.commit()

# === Static dropdown values ===
items = ["Monitor", "Laptop", "Keyboard", "Mouse", "Chair", "Desk",
         "Printer", "Router", "Stationery", "Projector"]
departments = ["HR", "Finance", "Tech", "Admin", "Operations", "Legal", "Marketing"]
offices = ["Varanasi"]

# === ROUTES ===

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM inventory")
    data = cursor.fetchall()

    cursor.execute("SELECT SUM(quantity) FROM inventory")
    total_quantity = cursor.fetchone()[0] or 0

    return render_template("dashboard.html", data=data, total_quantity=total_quantity)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session["username"] = username
            session["user_type"] = "manager" if username.lower() == "manager" else "staff"
            return redirect(url_for("home"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db.commit()
            return redirect(url_for("login"))
        except mysql.connector.errors.IntegrityError:
            error = "Username already exists. Choose another."
    return render_template("signup.html", error=error)

@app.route('/add', methods=["GET", "POST"])
def add():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        item = request.form['item']
        department = request.form['department']
        office = request.form['office']
        quantity = request.form['quantity']

        cursor.execute(
            "INSERT INTO inventory (item, department, office, quantity) VALUES (%s, %s, %s, %s)",
            (item, department, office, quantity)
        )
        db.commit()
        return redirect(url_for('home'))

    return render_template("add.html", items=items, departments=departments, offices=offices)

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    db.commit()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === MANAGER ANALYTICS ===

@app.route('/analytics')
def analytics():
    if 'user_type' not in session or session['user_type'] != 'manager':
        return redirect(url_for('home'))

    cursor.execute("SELECT DISTINCT office FROM inventory")
    offices = [row[0] for row in cursor.fetchall()]
    return render_template("analytics.html", offices=offices)

@app.route('/get_departments/<office>')
def get_departments(office):
    cursor.execute("SELECT DISTINCT department FROM inventory WHERE office = %s", (office,))
    departments = [row[0] for row in cursor.fetchall()]
    return jsonify(departments)

@app.route('/get_items/<office>/<department>')
def get_items(office, department):
    cursor.execute("""
        SELECT item, SUM(quantity) 
        FROM inventory 
        WHERE office = %s AND department = %s 
        GROUP BY item
    """, (office, department))
    items = cursor.fetchall()
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True)
