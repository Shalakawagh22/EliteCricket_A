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
schedules_collection = db["schedules"]




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
    schedules = list(db.schedules.find().sort("date", 1))
    all_perf_users = list(users.find({"email": {"$nin": ADMIN_EMAILS}}, {"name": 1, "email": 1}))
    all_performance = list(performance_collection.find().sort("session_date", -1))
    all_orders = list(orders_collection.find().sort("created_at", -1))
    orders_count = orders_collection.count_documents({})
    store_products = list(products_collection.find())

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
        reviews_count=reviews_count,
        schedules=schedules,
        all_perf_users=all_perf_users,
        all_performance=all_performance,
        all_orders=all_orders,
        orders_count=orders_count,
        store_products=store_products
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
    cart_count = cart_collection.count_documents({"user": session.get("user", "")})
    return render_template("store.html", products=products, cart_count=cart_count)
# ===== ADD TO CART =====
from bson.objectid import ObjectId
from flask import request, redirect, url_for, flash

@app.route("/add_to_cart/<product_id>", methods=["POST"])
def add_to_cart(product_id):
    if 'user' not in session:
        return redirect('/login')

    quantity = int(request.form.get("quantity", 1))
    product = products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("store"))

    product_id_str = str(product["_id"])
    user_email = session["user"]

    existing = cart_collection.find_one({"product_id": product_id_str, "user": user_email})

    if existing:
        cart_collection.update_one(
            {"product_id": product_id_str, "user": user_email},
            {"$inc": {"quantity": quantity}}
        )
    else:
        cart_collection.insert_one({
            "product_id": product_id_str,
            "user": user_email,
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
    user_email = session.get("user", "")
    cart = list(cart_collection.find({"user": user_email}))
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
        {"product_id": product_id, "user": session.get("user")},
        {"$set": {"quantity": quantity}}
    )
    return redirect(url_for("cart_page"))

@app.route("/remove_from_cart/<product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart_collection.delete_one({"product_id": product_id, "user": session.get("user")})
    return redirect(url_for("cart_page"))

# ===== CHECKOUT =====
import random
from bson.objectid import ObjectId

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if 'user' not in session:
        return redirect('/login')

    cart = list(cart_collection.find({"user": session["user"]}))
    total = sum(int(i["price"]) * int(i["quantity"]) for i in cart)

    if request.method == "POST":
        payment_method = request.form.get("payment_method")
        if not payment_method:
            flash("Please select a payment method.")
            return redirect("/checkout")

        order_id = str(random.randint(100000, 999999))

        serialized = [
            {"name": i["name"], "price": int(i["price"]), "quantity": int(i["quantity"])}
            for i in cart
        ]

        # Store in DB instead of session to avoid cookie size limit
        orders_collection.insert_one({
            "order_id": order_id,
            "user": session.get("user"),
            "items": serialized,
            "total": total,
            "payment_method": payment_method,
            "created_at": datetime.now()
        })

        # Keep only order_id in session
        session["last_order_id"] = order_id
        session.modified = True

        cart_collection.delete_many({"user": session["user"]})

        if payment_method == "COD":
            return redirect(f"/order_success?oid={order_id}")
        return redirect(f"/payment?oid={order_id}")

    return render_template("checkout.html", cart=cart, total=total)

# ===== HOME =====
# (handled by home() route above)

#---------------payment---------------
@app.route("/payment", methods=["GET", "POST"])
def payment():
    order_id = (request.form.get("oid") or
                request.args.get("oid") or
                session.get("last_order_id"))
    if not order_id:
        return redirect("/checkout")
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        return redirect("/checkout")
    if request.method == "POST":
        orders_collection.update_one({"order_id": order_id}, {"$set": {"payment_method": "ONLINE"}})
        return redirect(f"/order_success?oid={order_id}")
    return render_template("payment.html", total=order["total"], oid=order_id)

#----------order success-----------
@app.route("/order_success")
def order_success():
    order_id = request.args.get("oid") or session.get("last_order_id")

    if order_id:
        order = orders_collection.find_one({"order_id": order_id})
    else:
        order = None

    # Final fallback — most recent order for this user
    if not order and session.get("user"):
        order = orders_collection.find_one(
            {"user": session["user"]},
            sort=[("_id", DESCENDING)]
        )

    if not order:
        return redirect("/store")

    return render_template(
        "order_success.html",
        order_id=order["order_id"],
        order_items=order.get("items", []),
        total=order["total"],
        payment_method=order.get("payment_method", "COD"),
        tracking_status=order.get("tracking_status", "Order Placed")
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

model = genai.GenerativeModel("gemini-1.5-flash")


# ------------------ AI CHATBOT ------------------

# -------- AI CHATBOT --------
import requests

OPENROUTER_API_KEY = "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"   # 🔑 PUT YOUR REAL KEY HERE

@app.route("/chatbot")
def chatbot():
    if 'user' not in session:
        return redirect('/login')
    return render_template("chatbot.html")


@app.route("/clear_chat")
def clear_chat():
    return jsonify({"status": "cleared"})


@app.route("/get_response", methods=["POST"])
def get_response():
    user_msg = request.json.get("message", "").strip().lower()
    if not user_msg:
        return jsonify({"response": "Please type a message."})

    # ---- Try Gemini first ----
    try:
        prompt = f"You are a professional cricket coach AI for Elite Cricket Academy. Give short, helpful, friendly answers in 2-4 sentences.\n\nUser: {user_msg}\nCoach:"
        response = model.generate_content(prompt)
        reply = response.text.strip()
        return jsonify({"response": reply})
    except Exception as e:
        print("Gemini error:", e)

    # ---- Fallback: rule-based cricket Q&A ----
    qa = [
        (["batting", "bat", "improve batting", "batting tips"], "🏏 To improve batting: 1) Keep your eye on the ball at all times. 2) Practice your footwork daily. 3) Work on both front-foot and back-foot play. 4) Shadow bat in front of a mirror to check your technique."),
        (["bowling", "bowl", "bowling tips", "bowling technique"], "🎳 Key bowling tips: 1) Focus on a consistent run-up. 2) Keep your wrist behind the ball at release. 3) Vary your pace and length to deceive batsmen. 4) Practice yorkers and bouncers regularly."),
        (["fielding", "field", "catching", "fielding tips"], "🏃 Fielding tips: 1) Always stay on your toes and be ready to move. 2) Practice catching with both hands. 3) Work on your throwing accuracy. 4) Anticipate the ball's direction based on the batsman's stance."),
        (["fitness", "fit", "exercise", "training", "workout"], "💪 Cricket fitness: 1) Focus on agility drills and sprints. 2) Build core strength with planks and squats. 3) Do shoulder strengthening exercises to prevent injury. 4) Maintain flexibility with daily stretching."),
        (["wicket", "wicket keeping", "keeper"], "🧤 Wicket-keeping tips: 1) Stay low and balanced behind the stumps. 2) Keep your eyes level with the ball. 3) Practice taking catches on both sides. 4) Work on your footwork for wide deliveries."),
        (["spin", "spin bowling", "spinner"], "🌀 Spin bowling tips: 1) Grip the ball with your fingers, not your palm. 2) Use your wrist to generate turn. 3) Vary your flight and pace. 4) Practice the googly and doosra to deceive batsmen."),
        (["fast", "fast bowling", "pace", "pacer"], "⚡ Fast bowling tips: 1) Build a smooth, rhythmic run-up. 2) Jump high at the crease for extra bounce. 3) Keep your front arm high for control. 4) Strengthen your core and legs for power."),
        (["diet", "food", "nutrition", "eat"], "🥗 Cricket nutrition: 1) Eat complex carbs before matches for energy. 2) Stay hydrated — drink water every 20 minutes. 3) Have protein after training for muscle recovery. 4) Avoid heavy meals before playing."),
        (["mental", "pressure", "confidence", "nervous", "focus"], "🧠 Mental game tips: 1) Focus on one ball at a time. 2) Use deep breathing to stay calm under pressure. 3) Visualize success before you bat or bowl. 4) Learn from mistakes without dwelling on them."),
        (["enroll", "join", "register", "academy", "program"], "🎓 To join Elite Cricket Academy, visit our Enroll page! We offer Beginner, Intermediate, and Advanced programs with professional coaches. Click 'Enroll' in the navigation to get started."),
        (["hello", "hi", "hey", "good morning", "good evening"], "👋 Hello! I'm your AI Cricket Coach. Ask me about batting, bowling, fielding, fitness, or anything cricket-related!"),
        (["thank", "thanks", "thank you"], "😊 You're welcome! Keep practicing and you'll reach the top. Any other cricket questions?"),
        (["bye", "goodbye", "see you"], "👋 Goodbye! Keep training hard and stay passionate about cricket. See you on the field!"),
    ]

    for keywords, answer in qa:
        if any(kw in user_msg for kw in keywords):
            return jsonify({"response": answer})

    return jsonify({"response": "🏏 Great question! I can help with batting, bowling, fielding, fitness, wicket-keeping, spin/pace bowling, nutrition, and mental game tips. What would you like to know?"})

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


# ---------------- PERFORMANCE ANALYTICS ----------------
performance_collection = db["performance"]

@app.route('/performance/add', methods=['POST'])
def admin_add_performance():
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')
    user_email = request.form['user_email']
    performance_collection.insert_one({
        "user_email": user_email,
        "session_date": request.form['session_date'],
        "batting_score": int(request.form.get('batting_score', 0)),
        "bowling_wickets": int(request.form.get('bowling_wickets', 0)),
        "fielding_score": int(request.form.get('fielding_score', 0)),
        "fitness_score": int(request.form.get('fitness_score', 0)),
        "notes": request.form.get('notes', ''),
        "created_at": datetime.now()
    })
    flash("Performance record added!")
    return redirect('/dashboard_admin#performance')

@app.route('/performance/delete/<id>', methods=['POST'])
def admin_delete_performance(id):
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')
    performance_collection.delete_one({"_id": ObjectId(id)})
    return redirect('/dashboard_admin#performance')

@app.route('/my_performance')
def my_performance():
    if 'user' not in session:
        return redirect('/login')
    records = list(performance_collection.find(
        {"user_email": session['user']}
    ).sort("session_date", 1))
    user = users.find_one({"email": session['user']})
    return render_template('performance.html', records=records, user=user)

# ---------------- TRAINING SCHEDULE ----------------
@app.route('/admin/schedule/add', methods=['POST'])
def admin_add_schedule():
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')
    schedules_collection.insert_one({
        "title":    request.form['title'],
        "date":     request.form['date'],
        "time":     request.form['time'],
        "duration": request.form.get('duration', ''),
        "coach":    request.form.get('coach', ''),
        "batch":    request.form.get('batch', 'All'),
        "notes":    request.form.get('notes', ''),
        "created_at": datetime.now()
    })
    flash("Session added successfully!")
    return redirect('/dashboard_admin#schedule')

@app.route('/admin/schedule/delete/<id>', methods=['POST'])
def admin_delete_schedule(id):
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')
    schedules_collection.delete_one({"_id": ObjectId(id)})
    flash("Session deleted.")
    return redirect('/dashboard_admin#schedule')

@app.route('/training_schedule')
def training_schedule():
    if 'user' not in session:
        return redirect('/login')
    schedules = list(schedules_collection.find().sort("date", 1))
    return render_template('training_schedule.html', schedules=schedules)


# ------------------ ML PLAYER PREDICTION ------------------
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans

def predict_best_players():
    """
    Aggregates performance data per user, normalises it,
    computes a weighted composite score, clusters players
    into tiers, and returns a ranked list with ML insights.
    """
    pipeline = list(performance_collection.aggregate([
        {"$group": {
            "_id": "$user_email",
            "avg_batting":  {"$avg": "$batting_score"},
            "avg_bowling":  {"$avg": "$bowling_wickets"},
            "avg_fielding": {"$avg": "$fielding_score"},
            "avg_fitness":  {"$avg": "$fitness_score"},
            "sessions":     {"$sum": 1},
            "last_date":    {"$max": "$session_date"}
        }}
    ]))

    if len(pipeline) < 2:
        return [], []   # not enough data for clustering

    # Build feature matrix
    emails   = [p["_id"] for p in pipeline]
    features = np.array([
        [p["avg_batting"],
         p["avg_bowling"] * 10,   # scale wickets to ~0-100
         p["avg_fielding"],
         p["avg_fitness"],
         min(p["sessions"] * 5, 100)]  # consistency bonus, capped at 100
        for p in pipeline
    ], dtype=float)

    # Normalise 0-1
    scaler = MinMaxScaler()
    norm   = scaler.fit_transform(features)

    # Weighted composite score (batting 30%, bowling 25%, fielding 20%, fitness 20%, consistency 5%)
    weights = np.array([0.30, 0.25, 0.20, 0.20, 0.05])
    scores  = (norm * weights).sum(axis=1) * 100   # 0-100

    # KMeans clustering into 3 tiers
    n_clusters = min(3, len(pipeline))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(norm)

    # Map cluster label → tier name by cluster centre score
    centre_scores = {i: (km.cluster_centers_[i] * weights).sum() for i in range(n_clusters)}
    sorted_centres = sorted(centre_scores, key=centre_scores.get, reverse=True)
    tier_names = {sorted_centres[0]: "Elite", sorted_centres[1]: "Developing"}
    if n_clusters == 3:
        tier_names[sorted_centres[2]] = "Beginner"

    # Enrich pipeline records
    for i, p in enumerate(pipeline):
        user = users.find_one({"email": p["_id"]}, {"name": 1})
        p["name"]          = user["name"] if user else p["_id"]
        p["score"]         = round(float(scores[i]), 1)
        p["tier"]          = tier_names.get(int(labels[i]), "Beginner")
        p["avg_batting"]   = round(p["avg_batting"],  1)
        p["avg_bowling"]   = round(p["avg_bowling"],  1)
        p["avg_fielding"]  = round(p["avg_fielding"], 1)
        p["avg_fitness"]   = round(p["avg_fitness"],  1)

    pipeline.sort(key=lambda x: x["score"], reverse=True)

    # Feature importance (just the weights, labelled)
    feature_importance = [
        {"feature": "Batting",     "weight": 30},
        {"feature": "Bowling",     "weight": 25},
        {"feature": "Fielding",    "weight": 20},
        {"feature": "Fitness",     "weight": 20},
        {"feature": "Consistency", "weight": 5},
    ]

    return pipeline, feature_importance


@app.route("/ml_predictions")
def ml_predictions():
    if session.get("user") not in ADMIN_EMAILS:
        return redirect("/login")
    players, feature_importance = predict_best_players()
    return render_template("ml_predictions.html",
                           players=players,
                           feature_importance=feature_importance)



# ------------------ ORDER MANAGEMENT ------------------
TRACKING_STEPS = ["Order Placed", "Processing", "Packed", "Out for Delivery", "Delivered"]

@app.route('/admin/order/update_tracking/<order_id>', methods=['POST'])
def admin_update_tracking(order_id):
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')

    status = request.form.get('tracking_status')

    if status in TRACKING_STEPS:
        orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"tracking_status": status}}
        )
        flash(f"Tracking updated to '{status}'")

    return redirect('/dashboard_admin#orders')

@app.route('/admin/order/delete/<order_id>', methods=['POST'])
def admin_delete_order(order_id):
    if session.get('user') not in ADMIN_EMAILS:
        return redirect('/login')
    orders_collection.delete_one({"order_id": order_id})
    flash("Order deleted.")
    return redirect('/dashboard_admin#orders')

# ------------------ ABOUT & PROGRAMS ------------------
def about():
    return render_template("about.html")

@app.route("/programs")
def programs():
    return render_template("programs.html")

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)


