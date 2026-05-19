import razorpay
from flask import Flask, render_template
from flask import request, redirect
from flask import session
from flask_mysqldb import MySQL
from config import Config
import bcrypt
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
client = razorpay.Client(
    auth=(
        "rzp_test_Sr9cwUsrlWGQnX",
        "N3lNte0257LMt7mXrFtM6LEM"
    )
)

# ==========================
# HOME PAGE
# ==========================
@app.route('/')
def home():

    cursor = mysql.connection.cursor()

    search = request.args.get('search')
    sort = request.args.get('sort')
    category = request.args.get('category')

    query = "SELECT * FROM products"
    conditions = []
    values = []

    if search:
        conditions.append(
            "name LIKE %s"
        )
        values.append(
            '%' + search + '%'
        )

    if category:
        conditions.append(
            "category = %s"
        )
        values.append(category)

    if conditions:
        query += " WHERE "
        query += " AND ".join(
            conditions
        )

    if sort == 'low':
        query += """
        ORDER BY price ASC
        """

    elif sort == 'high':
        query += """
        ORDER BY price DESC
        """

    cursor.execute(query, values)

    products = cursor.fetchall()

    cursor.close()

    return render_template(
        'index.html',
        products=products
    )
@app.route('/products')
def products():

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        """
    )

    products = cursor.fetchall()

    cursor.close()

    return render_template(
        'products.html',
        products=products
    )
@app.route('/product/<int:id>')
def product_detail(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=%s
        """,
        (id,)
    )

    product = cursor.fetchone()

    cursor.execute(
        """
        SELECT reviews.rating,
               reviews.comment,
               users.username
        FROM reviews
        JOIN users
        ON reviews.user_id = users.id
        WHERE product_id=%s
        """,
        (id,)
    )

    reviews = cursor.fetchall()

    cursor.close()

    return render_template(
        'product_detail.html',
        product=product,
        reviews=reviews
    )


@app.route(
'/add-review/<int:product_id>',
methods=['POST']
)
def add_review(product_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    rating = request.form['rating']
    comment = request.form['comment']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO reviews
        (user_id, product_id,
        rating, comment)
        VALUES (%s,%s,%s,%s)
        """,
        (
            user_id,
            product_id,
            rating,
            comment
        )
    )

    mysql.connection.commit()

    cursor.close()

    return redirect(
        f'/product/{product_id}'
    )

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=%s
        """,
        (id,)
    )

    product = cursor.fetchone()

    cursor.close()

    return render_template(
        'product_detail.html',
        product=product
    )

# ==========================
# SIGNUP
# ==========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']


        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        cursor = mysql.connection.cursor()

        query = """
        INSERT INTO users
        (username, email, password)
        VALUES (%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                username,
                email,
                hashed_password.decode('utf-8')
            )
        )

        mysql.connection.commit()
        cursor.close()

        return redirect('/login')

    return render_template('signup.html')


# ==========================
# LOGIN
# ==========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()

        if user:

            stored_password = user[3]

            if bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password.encode('utf-8')
            ):

                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]

                return redirect('/')

        return "Invalid Email or Password"

    return render_template('login.html')


# ==========================
# LOGOUT
# ==========================
@app.route('/admin')
def admin_dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return "Access Denied"

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM products"
    )

    products = cursor.fetchall()

    cursor.close()

    return render_template(
        'admin/dashboard.html',
        products=products
    )
@app.route('/admin/orders')
def admin_orders():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return "Access Denied"

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT orders.id,
               users.username,
               orders.total_price,
               orders.address,
               orders.payment_method,
               orders.created_at
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
        """
    )

    orders = cursor.fetchall()

    cursor.close()

    return render_template(
        'admin/orders.html',
        orders=orders
    )
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():

    if request.method == 'POST':

        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']

        image = request.files['image']

        image_name = image.filename

        image.save(
            'static/uploads/' + image_name
        )

        cursor = mysql.connection.cursor()

        query = """
        INSERT INTO products
        (
            name,
            description,
            price,
            category,
            image
        )
        VALUES (%s,%s,%s,%s,%s)
        """

        values = (
            name,
            description,
            price,
            category,
            image_name
        )

        cursor.execute(query, values)

        mysql.connection.commit()

        cursor.close()

        return redirect('/products')

    return render_template(
        'admin/add_product.html'
    )
@app.route('/admin/delete-product/<int:id>')
def delete_product(id):

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return "Access Denied"

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        DELETE FROM products
        WHERE id=%s
        """,
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/admin')

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# ==========================
# ADD TO CART
# ==========================
@app.route('/add-to-wishlist/<int:product_id>')
def add_to_wishlist(product_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO wishlist
        (user_id, product_id)
        VALUES (%s,%s)
        """,
        (user_id, product_id)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/')


@app.route('/wishlist')
def wishlist():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT wishlist.id,
               products.id,
               products.name,
               products.price,
               products.image
        FROM wishlist
        JOIN products
        ON wishlist.product_id = products.id
        WHERE wishlist.user_id=%s
        """,
        (user_id,)
    )

    wishlist_items = cursor.fetchall()

    cursor.close()

    return render_template(
        'wishlist.html',
        wishlist_items=wishlist_items
    )
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT username, email
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE user_id=%s
        """,
        (user_id,)
    )

    total_orders = cursor.fetchone()[0]

    cursor.close()

    return render_template(
        'profile.html',
        user=user,
        total_orders=total_orders
    )

@app.route(
'/remove-wishlist/<int:id>'
)
def remove_wishlist(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        DELETE FROM wishlist
        WHERE id=%s
        """,
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/wishlist')
# ==========================
# CART PAGE
# ==========================
@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM cart
        WHERE user_id=%s
        AND product_id=%s
        """,
        (user_id, product_id)
    )

    existing_item = cursor.fetchone()

    if existing_item:

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE user_id=%s
            AND product_id=%s
            """,
            (user_id, product_id)
        )

    else:

        cursor.execute(
            """
            INSERT INTO cart
            (user_id, product_id, quantity)
            VALUES (%s,%s,%s)
            """,
            (user_id, product_id, 1)
        )

    mysql.connection.commit()

    cursor.close()

    return redirect('/cart')
@app.route('/cart')
def cart():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    query = """
    SELECT cart.id,
           products.name,
           products.price,
           cart.quantity
    FROM cart
    JOIN products
    ON cart.product_id = products.id
    WHERE cart.user_id = %s
    """

    cursor.execute(query, (user_id,))

    cart_items = cursor.fetchall()

    cursor.close()

    total = 0

    for item in cart_items:
        total += item[2] * item[3]

    return render_template(
        'cart.html',
        cart_items=cart_items,
        total=total
    )


# ==========================
# INCREASE QUANTITY
# ==========================
 
@app.route('/increase-quantity/<int:cart_id>')
def increase_quantity(cart_id):
    if 'user_id' not in session:
        return redirect('/login')
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE cart
        SET quantity = quantity + 1
        WHERE id=%s
        """,
        (cart_id,)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect('/cart')


# ==========================
# DECREASE QUANTITY
# ==========================
@app.route('/decrease-quantity/<int:cart_id>')
def decrease_quantity(cart_id):
    if 'user_id' not in session:
     return redirect('/login')
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE id=%s
        """,
        (cart_id,)
    )

    item = cursor.fetchone()

    if item and item[0] > 1:

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity - 1
            WHERE id=%s
            """,
            (cart_id,)
        )

    mysql.connection.commit()
    cursor.close()

    return redirect('/cart')


# ==========================
# REMOVE ITEM
# ==========================
@app.route('/remove-item/<int:cart_id>')
def remove_item(cart_id):
    if 'user_id' not in session:
     return redirect('/login')
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        DELETE FROM cart
        WHERE id=%s
        """,
        (cart_id,)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect('/cart')


# ==========================
# OTHER PAGES
# ==========================
@app.route(
'/checkout',
methods=['GET', 'POST']
)
def checkout():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    query = """
    SELECT cart.id,
           products.name,
           products.price,
           cart.quantity
    FROM cart
    JOIN products
    ON cart.product_id = products.id
    WHERE cart.user_id = %s
    """

    cursor.execute(
        query,
        (user_id,)
    )

    cart_items = cursor.fetchall()

    if not cart_items:

        cursor.close()

        return redirect(
            '/cart'
        )

    total = 0

    for item in cart_items:

        total += (
            item[2] *
            item[3]
        )

    if request.method == 'POST':

        address = request.form[
            'address'
        ]

        payment_method = request.form[
            'payment_method'
        ]

        payment_status = request.form.get(
            'payment_status',
            'Pending'
        )

        cursor.execute(
            """
            INSERT INTO orders
            (
                user_id,
                total_price,
                address,
                payment_method,
                status
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                user_id,
                total,
                address,
                payment_method,
                payment_status
            )
        )

        mysql.connection.commit()

        order_id = cursor.lastrowid

        for item in cart_items:

            cursor.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_name,
                    price,
                    quantity
                )
                VALUES (%s,%s,%s,%s)
                """,
                (
                    order_id,
                    item[1],
                    item[2],
                    item[3]
                )
            )

        cursor.execute(
            """
            DELETE FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        mysql.connection.commit()

        cursor.close()

        return redirect(
            '/orders'
        )

    cursor.close()

    payment = client.order.create({

        "amount":
        int(total * 100),

        "currency":
        "INR",

        "payment_capture":
        1
    })

    return render_template(
        'checkout.html',
        total=total,
        payment=payment,
        razorpay_key=
        "rzp_test_Sr9cwUsrlWGQnX"
    )
@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    orders = cursor.fetchall()

    cursor.close()

    return render_template(
        'orders.html',
        orders=orders
    )



# ==========================
# RUN APP
# ==========================
if __name__ == '__main__':
    app.run(debug=True)