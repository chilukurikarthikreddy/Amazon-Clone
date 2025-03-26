from flask import Flask, request, jsonify, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',
        database='amazon_clone'
    )
    return conn

# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    email = data['email']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "User registered successfully"})

# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user[0]
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# List Products
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    
    product_list = []
    for product in products:
        product_list.append({
            'product_id': product[0],
            'product_name': product[1],
            'description': product[2],
            'price': product[3],
            'stock': product[4]
        })
    
    cursor.close()
    conn.close()
    
    return jsonify(product_list)

# Add to Cart
@app.route('/cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"message": "Please login first"}), 401
    
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id, quantity))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Added to cart"})

# Checkout (Create Order)
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({"message": "Please login first"}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(p.price * c.quantity) FROM cart c JOIN products p ON c.product_id = p.product_id WHERE c.user_id = %s", (user_id,))
    total_amount = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)", (user_id, total_amount))
    order_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) SELECT %s, product_id, quantity FROM cart WHERE user_id = %s", (order_id, user_id))
    
    cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Order placed successfully", "order_id": order_id})

if __name__ == '__main__':
    app.run(debug=True)
