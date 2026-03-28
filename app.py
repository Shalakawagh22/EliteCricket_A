from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
from pymongo import MongoClient, DESCENDING
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import random, json
from datetime import datetime


app = Flask(__name__)
app.secret_key = "secretkey123"

# -------- ADMIN EMAILS --------
ADMIN_EMAILS = ["shalakawagh22@gmail.com", "waghshalaka6@gmail.com"]

# -------- MAIL CONFIG --------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shalakawagh22@gmail.com'
app.config['MAIL_PASSWORD'] = 'momk ufsq onty hpcz'
app.config['MAIL_DEFAULT_SENDER'] = 'shalakawagh22@gmail.com'
mail = Mail(app)

# -------- MONGODB --------
client = MongoClient("mongodb://localhost:27017/")
db = client["cricket_academy_db"]
users = db["users"]
enrollments = db["enrollments"]
contact_collection = db["contact"]
store_collection = db["cricketStoreDB"]
payments_collection = db["payments"]
products_collection = db["products"]
cart_collection = db["cart"]
orders_collection = db["orders"]
payments_collection = db["payments"]
players_collection = db["players"]
reviews_collection = db["reviews"]




# -------- UTILITY FUNCTIONS --------
def get_cart():
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]

# ------------------ HOME ------------------
@app.route("/")
def home():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/dashboard_user')

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if email in ADMIN_EMAILS:
            flash("Admin accounts cannot be registered.")
            return redirect("/register")

        if users.find_one({"email": email}):
            flash("Email already registered.")
            return redirect("/register")

        otp = str(random.randint(100000, 999999))
        session.update({"otp": otp, "name": name, "email": email, "password": password})

        msg = Message("Cricket Academy OTP Verification", recipients=[email])
        msg.body = f"Your OTP for registration is: {otp}"
        mail.send(msg)

        flash("OTP sent to your email.")
        return redirect("/verify_email")
    return render_template("register.html")

# ------------------ VERIFY OTP ------------------
@app.route("/verify_email", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form["otp"]
        if user_otp == session.get("otp"):
            users.insert_one({
                "name": session["name"],
                "email": session["email"],
                "password": session["password"]
            })
            session.pop("otp", None)
            flash("Registration successful! Please login.")
            return redirect("/login")
        else:
            flash("Invalid OTP")
    return render_template("verify_email.html")

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = users.find_one({"email": email})
        if user and user["password"] == password:
            session["user"] = email
            if email in ADMIN_EMAILS:
                return redirect("/dashboard_admin")
            else:
                return redirect("/dashboard_user")
        else:
            flash("Invalid email or password")
    return render_template("login.html")

# ------------------ DASHBOARDS ------------------
@app.route('/dashboard_user')
def dashboard_user():
    if 'user' not in session:
        return redirect('/login')
    player = db.players.find_one({"user_email": session['user']})
    user = users.find_one({"email": session['user']})
    recent_reviews = list(reviews_collection.find().sort("created_at", DESCENDING).limit(5))
    return render_template("dashboard_user.html", player=player, user=user, recent_reviews=recent_reviews)

@app.route("/dashboard_admin")
def dashboard_admin():
    if "user" not in session:
        return redirect("/login")
    if session["user"] not in ADMIN_EMAILS:
        return redirect("/dashboard_user")

    all_users = list(users.find({"email": {"$nin": ADMIN_EMAILS}}, {"name": 1, "email": 1}))
    all_reviews = list(reviews_collection.find().sort("created_at", DESCENDING))
    reviews_count = reviews_collection.count_documents({})

    return render_template(
        "dashboard_admin.html",
        users_count=users.count_documents({}),
        enroll_count=enrollments.count_documents({}),
        contact_count=contact_collection.count_documents({}),
        users_data=list(users.find()),
        enroll_data=list(enrollments.find()),
        contact_data=list(contact_collection.find()),
        all_users=all_users,
        all_reviews=all_reviews,
        reviews_count=reviews_count
    )

# ------------------ USER MANAGEMENT ------------------
@app.route("/view_user")
def view_user():
    if session.get("user") not in ADMIN_EMAILS:
        return redirect("/login")
    return render_template("view_user.html", users=users.find())

@app.route("/delete_user/<email>", methods=["GET","POST"])
def delete_user(email):
    if session.get("user") not in ADMIN_EMAILS:
        return redirect("/login")
    user = users.find_one({"email": email})
    if request.method == "POST":
        users.delete_one({"email": email})
        flash("User deleted successfully")
        return redirect("/view_user")
    return render_template("delete_user.html", user=user)

@app.route("/update_user/<email>", methods=["GET","POST"])
def update_user(email):
    if session.get("user") not in ADMIN_EMAILS:
        return redirect("/login")
    user = users.find_one({"email": email})
    if request.method == "POST":
        users.update_one({"email": email}, {"$set": {
            "name": request.form["name"],
            "password": request.form["password"]
        }})
        return redirect("/view_user")
    return render_template("update_user.html", user=user)

# ------------------ ENROLLMENT ------------------
@app.route("/enroll", methods=["GET","POST"])
def enroll():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        enrollments.insert_one({
            "name": request.form["name"],
            "email": request.form["email"],
            "age": request.form["age"],
            "phone": request.form["phone"],
            "training": request.form["training"],
            "batch": request.form["batch"],
            "message": request.form["message"],
            "created_at": datetime.now()
        })
        flash("Enrollment Successful!")
        return redirect("/enroll")
    return render_template("enroll.html")

# ------------------ CONTACT ------------------
@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        contact_collection.insert_one({
            "name": request.form["name"],
            "email": request.form["email"],
            "subject": request.form["subject"],
            "message": request.form["message"],
            "created_at": datetime.now()
        })
        flash("Message sent successfully!")
        return redirect("/contact")
    return render_template("contact.html")

@app.route("/view_contacts")
def view_contacts():
    if session.get("user") not in ADMIN_EMAILS:
        return redirect("/login")
    return render_template("view_contacts.html", contacts=contact_collection.find())



# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------ STORE ------------------

if products_collection.count_documents({}) == 0:
    products_collection.insert_many([
        {"product_id": "1", "name": "Cricket Bat", "price": 2500},
        {"product_id": "2", "name": "Cricket Ball", "price": 500},
        {"product_id": "3", "name": "Cricket Jersey", "price": 1200},
        {"product_id": "4", "name": "Cricket Kit", "price": 5000}
    ])

# ===== STORE PAGE =====
@app.route("/store")
def store():
    products = list(products_collection.find())

    cart_count = cart_collection.count_documents({})

    return render_template(
        "store.html",
        products=products,
        cart_count=cart_count
    )
# ===== ADD TO CART =====
from bson.objectid import ObjectId
from flask import request, redirect, url_for, flash

@app.route("/add_to_cart/<product_id>", methods=["POST"])
def add_to_cart(product_id):

    quantity = int(request.form.get("quantity", 1))

    # FIX: use ObjectId
    product = products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("store"))

    product_id_str = str(product["_id"])

    existing = cart_collection.find_one({"product_id": product_id_str})

    if existing:
        cart_collection.update_one(
            {"product_id": product_id_str},
            {"$inc": {"quantity": quantity}}
        )
    else:
        cart_collection.insert_one({
            "product_id": product_id_str,
            "name": product["name"],
            "price": int(product["price"]),
            "quantity": int(quantity)
        })

    return redirect(url_for("store"))

#----clean cart--------
@app.route("/clean_cart")
def clean_cart():
    cart_collection.delete_many({})
    return "Cart cleared"
# ===== CART PAGE =====
@app.route("/cart")
def cart_page():
    cart = list(cart_collection.find())

    total = 0

    for item in cart:
        price = int(item.get("price", 0))
        quantity = int(item.get("quantity", 1))

        item["price"] = price
        item["quantity"] = quantity

        total += price * quantity

    return render_template("cart.html", cart=cart, total=total)

# ===== UPDATE CART =====
@app.route("/update_cart/<product_id>", methods=["POST"])
def update_cart(product_id):
    quantity = int(request.form.get("quantity", 1))

    cart_collection.update_one(
        {"product_id": product_id},
        {"$set": {"quantity": quantity}}
    )

    return redirect(url_for("cart_page"))

# ===== REMOVE ITEM =====
@app.route("/remove_from_cart/<product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart_collection.delete_one({"product_id": product_id})
    return redirect(url_for("cart_page"))

# ===== CHECKOUT =====
import random
from bson.objectid import ObjectId

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = list(cart_collection.find())

    total = sum(int(i["price"]) * int(i["quantity"]) for i in cart)

    if request.method == "POST":
        payment_method = request.form.get("payment_method")

        order_id = str(random.randint(100000, 999999))

        # IMPORTANT: SAVE ORDER BEFORE REDIRECT
        session["order"] = {
            "order_id": order_id,
            "items": cart,
            "total": total,
            "payment_method": payment_method
        }

        # clear cart AFTER saving order
        cart_collection.delete_many({})

        if payment_method == "COD":
            return redirect(url_for("order_success"))

        return redirect(url_for("payment"))

    return render_template("checkout.html", cart=cart, total=total)
# ===== HOME =====
# (handled by home() route above)

#---------------payment---------------
@app.route("/payment", methods=["GET", "POST"])
def payment():
    order = session.get("order")

    if not order:
        return redirect("/store")

    if request.method == "POST":
        # simulate payment success
        return redirect("/order_success")

    return render_template("payment.html", total=order["total"])

#-----------payment sucess---------
@app.route("/payment_success/<order_id>")
def payment_success(order_id):

    order = orders_collection.find_one({"order_id": order_id})

    if not order:
        return "Order not found", 404

    return redirect(url_for(
        "order_success",
        order_id=order_id,
        payment_method="ONLINE"
    ))

#----------order sucesss-----------
from bson.objectid import ObjectId

@app.route("/order_success")
def order_success():
    order = session.get("order")

    if not order:
        return redirect(url_for("store"))

    return render_template(
        "order_success.html",
        order_id=order["order_id"],
        order_items=order["items"],
        total=order["total"],
        payment_method=order["payment_method"]
    )
# ------------------ GAMES ------------------
@app.route("/gamezone")
def gamezone():
    return render_template("gamezone.html")

@app.route("/cricket_game_real")
def cricket_game_real():
    return render_template("cricket_game_real.html")

@app.route("/car_game")
def car_game():
    return render_template("car_game.html")

@app.route("/fruit_game")
def fruit_game():
    return render_template("fruit_game.html")


# ----------- GEMINI AI SETUP -----------
import google.generativeai as genai

genai.configure(api_key="AIzaSyCkBHhIjk2Bz95XCQaUhodErcIMKvUQN-g")

model = genai.GenerativeModel("gemini-pro")


# ------------------ AI CHATBOT ------------------

# -------- AI CHATBOT --------
import requests

OPENROUTER_API_KEY = "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"   # 🔑 PUT YOUR REAL KEY HERE

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@app.route("/get_response", methods=["POST"])
def get_response():
    user_msg = request.json.get("message")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer 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",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional cricket coach AI. Give short, helpful answers."
                    },
                    {
                        "role": "user",
                        "content": user_msg
                    }
                ]
            }
        )

        data = response.json()

        # 🔍 DEBUG (optional)
        print("AI RESPONSE:", data)

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
        elif "error" in data:
            reply = "⚠️ " + str(data["error"])
        else:
            reply = "⚠️ AI not responding properly"

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": "⚠️ Error: " + str(e)})
    
#-------------------store admin-----------

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/store_admin")
def store_admin():
    products = list(db.products.find())
    return render_template("store_admin.html", products=products)


# =========================
# ADD PRODUCT
# =========================
@app.route("/add_product", methods=["POST"])
def add_product():
    name = request.form["name"]
    price = request.form["price"]

    file = request.files["image"]
    filename = secure_filename(file.filename)

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    db.products.insert_one({
        "name": name,
        "price": price,
        "image": f"uploads/{filename}"   # IMPORTANT
    })

    return redirect("/store_admin")


# =========================
# DELETE PRODUCT
# =========================
@app.route("/delete_product/<id>")
def delete_product(id):
    product = db.products.find_one({"_id": ObjectId(id)})

    # remove image file
    if product:
        try:
            os.remove(os.path.join("static", product["image"]))
        except:
            pass

    db.products.delete_one({"_id": ObjectId(id)})

    return redirect("/store_admin")


# =========================
# EDIT PRODUCT PAGE
# =========================
@app.route("/edit_product/<id>", methods=["GET", "POST"])
def edit_product(id):
    product = db.products.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        db.products.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"name": name, "price": price}}
        )

        return redirect("/store_admin")

    return f"""
    <h2>Edit Product</h2>
    <form method="POST">
        <input name="name" value="{product['name']}" />
        <input name="price" value="{product['price']}" />
        <button type="submit">Update</button>
    </form>
    """


#-----------update product------------
@app.route("/update_product/<id>", methods=["POST"])
def update_product(id):
    from bson.objectid import ObjectId

    products_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "name": request.form["name"],
            "price": int(request.form["price"]),
            "image": request.form["image"]
        }}
    )

    return redirect(url_for("store_admin"))


#-----------uploads-------------

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- ADD PLAYER DATA ----------------
@app.route('/admin_add_player', methods=['GET', 'POST'])
def add_player():
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')

    if request.method == 'POST':
        user_email = request.form['user_id']
        player_data = {
            "user_email": user_email,
            "height": request.form['height'],
            "weight": request.form['weight'],
            "matches": int(request.form['matches']),
            "runs": int(request.form['runs']),
            "wickets": int(request.form.get('wickets', 0)),
            "batting_avg": request.form.get('batting_avg', ''),
            "bowling_style": request.form.get('bowling_style', ''),
            "role": request.form['role'],
            "experience": request.form['experience'],
            "fitness": request.form['fitness']
        }
        db.players.update_one(
            {"user_email": user_email},
            {"$set": player_data},
            upsert=True
        )
        flash("Player data saved successfully!")
        return redirect('/dashboard_admin#player')

    all_users = list(users.find({"email": {"$nin": ADMIN_EMAILS}}, {"name": 1, "email": 1}))
    return render_template('admin_add_player.html', users=all_users)


# ---------------- USER PROFILE ----------------
@app.route('/my_profile')
def my_profile():
    if 'user' not in session:
        return redirect('/login')

    player = db.players.find_one({"user_email": session['user']})
    user = db.users.find_one({"email": session['user']})

    return render_template('user_profile.html', player=player, user=user)


# ---------------- REVIEWS ----------------
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user' not in session:
        return redirect('/login')

    user = users.find_one({"email": session['user']})
    rating = int(request.form.get('rating', 5))
    review_text = request.form.get('review', '').strip()

    if review_text:
        reviews_collection.insert_one({
            "name": user['name'] if user else session['user'],
            "email": session['user'],
            "rating": rating,
            "review": review_text,
            "created_at": datetime.now()
        })
        flash("Thank you for your review!")

    return redirect('/dashboard_user#review')


# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)


