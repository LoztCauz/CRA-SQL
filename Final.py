from flask import Flask, request, redirect, url_for, session, render_template_string, flash, jsonify
import MySQLdb
import hashlib
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL configurations
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "merchant"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQLdb.connect(host=app.config["MYSQL_HOST"], user=app.config["MYSQL_USER"],
                        password=app.config["MYSQL_PASSWORD"], database=app.config["MYSQL_DB"])

# Create tables if not exists
with mysql.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            merchant_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            hire_date DATE,
            age INT,
            gender ENUM('Male', 'Female', 'Other'),
            first_name VARCHAR(255),
            middle_initial CHAR(1),
            last_name VARCHAR(255)
        ) ENGINE=InnoDB
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            date_of_arrival DATE,
            location VARCHAR(255),
            other_field VARCHAR(255)
        ) ENGINE=InnoDB
    """)
    mysql.commit()

# Login route
@app.route("/", methods=["GET", "POST"])
def login():
    msg = ''
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password'] 
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM merchants WHERE username = %s AND password = %s', (username, hashed_password))
        account = cursor.fetchone()
        cursor.close()

        if account:
            session['loggedin'] = True
            session['id'] = account['merchant_id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username / password!'
    
    login_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #800000, #808080);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .textbox {
            margin-bottom: 20px;
        }
        .textbox input {
            width: calc(100% - 22px);
            padding: 12px 10px;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        .textbox input:focus {
            border-color: #6A85B6;
        }
        .btn {
            background-color: #6A85B6;
            color: #fff;
            padding: 14px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #4E6FA7;
        }
        .error-msg {
            color: #ff4d4d;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
        a {
            color: #2980b9;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #FFFFFF;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Login</h1>
        {% if msg %}
        <p class="error-msg">{{ msg }}</p>
        {% endif %}
        <form method="post">
            <div class="textbox">
                <input type="text" placeholder="Your Username" name="username">
            </div>
            <div class="textbox">
                <input type="password" placeholder="Your Password" name="password">
            </div>
            <input type="submit" class="btn" value="Login">
        </form>
        <p>Don't have an account? <a href="{{ url_for('register') }}">Register</a></p>
    </div>
</body>
</html>


    """
    return render_template_string(login_template, msg=msg)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        first_name = request.form['first_name']
        middle_initial = request.form['middle_initial']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM merchants WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            msg = 'Username already exists!'
        else:
            cursor.execute('INSERT INTO merchants (username, password, first_name, middle_initial, last_name, age, gender) VALUES (%s, %s, %s, %s, %s, %s, %s)', 
                           (username, hashed_password, first_name, middle_initial, last_name, age, gender))
            mysql.commit()
            cursor.close()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    register_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #800000, #808080);
            font-family: 'Roboto', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .textbox {
            position: relative;
            margin-bottom: 20px;
        }
        .textbox input, .textbox select {
            width: calc(100% - 30px);
            padding: 12px 10px;
            border-radius: 5px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        .textbox input:focus, .textbox select:focus {
            border-color: #ff7e5f;
        }
        .textbox i {
            position: absolute;
            top: 50%;
            left: 10px;
            transform: translateY(-50%);
            color: #ccc;
        }
        .btn {
            background-color: #feb47b;
            color: #fff;
            padding: 14px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #ff7e5f;
        }
        .error-msg {
            color: #ff4d4d;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
        a {
            color: #feb47b;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #ff7e5f;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Register</h1>
        {% if msg %}
        <p class="error-msg">{{ msg }}</p>
        {% endif %}
        <form method="post">
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Username" name="username">
            </div>
            <div class="textbox">
                <i class="fas fa-lock"></i>
                <input type="password" placeholder="Password" name="password">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="First Name" name="first_name">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Middle Initial" name="middle_initial">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Last Name" name="last_name">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="number" placeholder="Age" name="age">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <select name="gender" id="gender">
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <input type="submit" class="btn" value="Register">
        </form>
        <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
    </div>
</body>
</html>

    """
    return render_template_string(register_template, msg=msg)

# Home route
@app.route('/home', methods=['GET'])
def home():
    if 'loggedin' in session:
        home_template = """
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #800000, #808080);
            font-family: 'Poppins', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: #F0F0F0;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        a {
            color: #4B77BE;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #00FF00;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Welcome, {{ username }}!</h1>
        <a href="{{ url_for('create') }}">Add Item</a><br>
        <a href="{{ url_for('read') }}">View Items</a><br>
        <a href="{{ url_for('delete') }}">Delete Items</a><br>
        <a href="{{ url_for('logout') }}">Logout</a><br>
    </div>
</body>
</html>

        """
        return render_template_string(home_template, username=session['username'])
    return redirect(url_for('login'))

# Create route
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        date_of_arrival = request.form['date_of_arrival']
        location = request.form['location']
        other_field = request.form['other_field']
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO items (name, price, date_of_arrival, location, other_field) VALUES (%s, %s, %s, %s, %s)', (name, price, date_of_arrival, location, other_field))
        mysql.commit()
        cursor.close()
        flash('Item created', 'success')
    create_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Item</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #008000, #808000);
            font-family: 'Roboto', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .textbox {
            position: relative;
            margin-bottom: 20px;
        }
        .textbox input, .textbox select {
            width: calc(100% - 30px);
            padding: 12px 10px;
            border-radius: 5px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        .textbox input:focus, .textbox select:focus {
            border-color: #FF9A9E;
        }
        .textbox i {
            position: absolute;
            top: 50%;
            left: 10px;
            transform: translateY(-50%);
            color: #ccc;
        }
        .btn {
            background-color: #FAD0C4;
            color: #fff;
            padding: 14px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #FF9A9E;
        }
        a {
            color: #FF9A9E;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #F94144;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Create Item</h1>
        <form method="post">
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Name" name="name">
            </div>
            <div class="textbox">
                <i class="fas fa-lock"></i>
                <input type="text" placeholder="Price" name="price">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="date" placeholder="Date of Arrival" name="date_of_arrival">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Location" name="location">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Other Field" name="other_field">
            </div>
            <input type="submit" class="btn" value="Create">
        </form>
        <a href="{{ url_for('home') }}">Back to Home</a><br>
    </div>
</body>
</html>

    """
    return render_template_string(create_template)

# Read route
@app.route('/read')
def read():
    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM items')
    items = cursor.fetchall()
    cursor.close()
    read_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Items</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #008000, #808000);
            font-family: 'Montserrat', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 800px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ccc;
        }
        th {
            background-color: #FFA500;
            color: #fff;
        }
        tr:nth-child(even) {
            background-color: #fff;
        }
        tr:nth-child(odd) {
            background-color: #f2f2f2;
        }
        a {
            color: #FF6347;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #DC143C;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Items</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Price</th>
                <th>Date of Arrival</th>
                <th>Location</th>
                <th>Other Field</th>
                <th>Edit</th>
            </tr>
            {% for item in items %}
            <tr>
                <td>{{ item['item_id'] }}</td>
                <td>{{ item['name'] }}</td>
                <td>{{ item['price'] }}</td>
                <td>{{ item['date_of_arrival'] }}</td>
                <td>{{ item['location'] }}</td>
                <td>{{ item['other_field'] }}</td>
                <td><a href="{{ url_for('edit', item_id=item['item_id']) }}">Edit</a></td>
            </tr>
            {% endfor %}
        </table>
        <a href="{{ url_for('download', format='json') }}">Download as JSON</a><br>
        <a href="{{ url_for('download', format='xml') }}">Download as XML</a><br>
        <a href="{{ url_for('home') }}">Back to Home</a><br>
    </div>
</body>
</html>

    """
    return render_template_string(read_template, items=items)

# Delete route
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        items_to_delete = request.form.getlist('delete_item')
        if items_to_delete:
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            for item_id in items_to_delete:
                cursor.execute('DELETE FROM items WHERE item_id = %s', (item_id,))
            mysql.commit()
            cursor.close()
            flash('Items deleted successfully!', 'success')
        else:
            flash('No items selected for deletion!', 'danger')

    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM items')
    items = cursor.fetchall()
    cursor.close()
    delete_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Delete Items</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right,#008000, #808000);
            font-family: 'Roboto', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 800px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ccc;
        }
        th {
            background-color: #b24592;
            color: #fff;
        }
        tr:nth-child(even) {
            background-color: #fff;
        }
        tr:nth-child(odd) {
            background-color: #f2f2f2;
        }
        input[type="checkbox"] {
            transform: scale(1.5);
        }
        .btn {
            background-color: #f15f79;
            color: #fff;
            padding: 14px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #b24592;
        }
        a {
            color: #f15f79;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #d7385e;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Delete Items</h1>
        <form method="post">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Price</th>
                    <th>Date of Arrival</th>
                    <th>Location</th>
                    <th>Other Field</th>
                    <th>Select for Deletion</th>
                </tr>
                {% for item in items %}
                <tr>
                    <td>{{ item['item_id'] }}</td>
                    <td>{{ item['name'] }}</td>
                    <td>{{ item['price'] }}</td>
                    <td>{{ item['date_of_arrival'] }}</td>
                    <td>{{ item['location'] }}</td>
                    <td>{{ item['other_field'] }}</td>
                    <td><input type="checkbox" name="delete_item" value="{{ item['item_id'] }}"></td>
                </tr>
                {% endfor %}
            </table>
            <input type="submit" class="btn" value="Delete">
        </form>
        <a href="{{ url_for('home') }}">Back to Home</a><br>
    </div>
</body>
</html>

    """
    return render_template_string(delete_template, items=items)

# Edit route
# Update route
# Edit route
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        date_of_arrival = request.form['date_of_arrival']
        location = request.form['location']
        other_field = request.form['other_field']
        
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE items SET name=%s, price=%s, date_of_arrival=%s, location=%s, other_field=%s WHERE item_id=%s',
                       (name, price, date_of_arrival, location, other_field, item_id))
        mysql.commit()
        cursor.close()
        flash('Item updated', 'success')
        return redirect(url_for('read'))

    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM items WHERE item_id = %s', (item_id,))
    item = cursor.fetchone()
    cursor.close()
    
    edit_template = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Item</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        body {
            background-image: linear-gradient(to right, #008000, #808000);
            font-family: 'Open Sans', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .login-box h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .textbox {
            position: relative;
            margin-bottom: 20px;
        }
        .textbox input, .textbox select {
            width: calc(100% - 30px);
            padding: 12px 10px;
            border-radius: 5px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        .textbox input:focus, .textbox select:focus {
            border-color: #6A85B6;
        }
        .textbox i {
            position: absolute;
            top: 50%;
            left: 10px;
            transform: translateY(-50%);
            color: #ccc;
        }
        .btn {
            background-color: #6A85B6;
            color: #fff;
            padding: 14px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #4E6FA7;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Edit Item</h1>
        <form method="post">
            <input type="hidden" name="item_id" value="{{ item['item_id'] }}">
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Name" name="name" value="{{ item['name'] }}">
            </div>
            <div class="textbox">
                <i class="fas fa-lock"></i>
                <input type="text" placeholder="Price" name="price" value="{{ item['price'] }}">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="date" placeholder="Date of Arrival" name="date_of_arrival" value="{{ item['date_of_arrival'] }}">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Location" name="location" value="{{ item['location'] }}">
            </div>
            <div class="textbox">
                <i class="fas fa-user"></i>
                <input type="text" placeholder="Other Field" name="other_field" value="{{ item['other_field'] }}">
            </div>
            <input type="submit" class="btn" value="Update">
        </form>
    </div>
</body>
</html>

    """
    return render_template_string(edit_template, item=item)




# Download route
@app.route('/download/<format>')
def download(format):
    if format == 'json':
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        cursor.close()
        json_data = jsonify(items)
        response = app.response_class(
            response=json_data,
            status=200,
            mimetype='application/json'
        )
        response.headers['Content-Disposition'] = 'attachment; filename=items.json'
        return response
    elif format == 'xml':
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        cursor.close()
        root = ET.Element("items")
        for item in items:
            item_element = ET.SubElement(root, "item")
            for key, value in item.items():
                sub_element = ET.SubElement(item_element, key)
                sub_element.text = str(value)
        xml_data = ET.tostring(root)
        response = app.response_class(
            response=xml_data,
            status=200,
            mimetype='application/xml'
        )
        response.headers['Content-Disposition'] = 'attachment; filename=items.xml'
        return response
    else:
        flash('Invalid format specified for download!', 'danger')
        return redirect(url_for('home'))

# Logout route
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)