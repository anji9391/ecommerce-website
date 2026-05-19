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