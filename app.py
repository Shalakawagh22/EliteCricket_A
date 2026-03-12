from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from pymongo import MongoClient
from flask_mail import Mail, Message
import bcrypt
import random
from config import *
from ai_agent.cricket_agent import ask_cricket_ai

app = Flask(__name__)
app.secret_key = "secretkey123"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["cricket_academy_db"]
users = db["users"]
enrollments = db["enrollments"]

# Mail setup
app.config.from_object('config')
mail = Mail(app)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("dashboard_user.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if users.find_one({"email":email}):
            return "Email already registered"

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        otp = str(random.randint(100000,999999))

        users.insert_one({
            "name":name,
            "email":email,
            "password":hashed,
            "role":role,
            "verified":False,
            "otp":otp
        })

        msg = Message("Verify Email", recipients=[email])
        msg.body = f"Your verification code is {otp}"

        mail.send(msg)

        session["email"] = email

        return redirect("/verify")

    return render_template("register.html")


# ---------------- VERIFY EMAIL ----------------
@app.route("/verify", methods=["GET","POST"])
def verify():

    if request.method == "POST":

        otp = request.form["otp"]
        email = session["email"]

        user = users.find_one({"email":email})

        if user["otp"] == otp:

            users.update_one(
                {"email":email},
                {"$set":{"verified":True}}
            )

            return redirect("/login")

        else:
            return "Invalid OTP"

    return render_template("verify_email.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = users.find_one({"email": email})

        if user is None:
            flash("User not found")
            return redirect(url_for("login"))

        if not user.get("verified", False):
            flash("Please verify your email first")
            return redirect(url_for("login"))

        stored_password = user.get("password")

        if bcrypt.checkpw(password.encode("utf-8"), stored_password):

            session["user"] = email
            session["role"] = user.get("role", "user")

            if session["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("user_dashboard"))

        else:
            flash("Incorrect password")
            return redirect(url_for("login"))

    return render_template("login.html")


# ---------------- USER DASHBOARD ----------------
@app.route("/user_dashboard")
def user_dashboard():
    return render_template("dashboard_user.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("dashboard_admin.html")


# ---------------- CONTACT ----------------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------------- ENROLL ----------------
@app.route("/enroll", methods=["GET","POST"])
def enroll():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        age = request.form["age"]
        phone = request.form["phone"]
        training = request.form["training"]
        batch = request.form["batch"]
        message = request.form["message"]

        enrollments.insert_one({
            "name": name,
            "email": email,
            "age": age,
            "phone": phone,
            "training": training,
            "batch": batch,
            "message": message
        })

        flash("🎉 Enrollment Successful!")

        return redirect("/enroll")

    return render_template("enroll.html")


# ---------------- CHATBOT PAGE ----------------
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


# ---------------- AI CHATBOT API ----------------
@app.route("/ask_ai", methods=["POST"])
def ask_ai():

    data = request.get_json()
    message = data["message"]

    reply = ask_cricket_ai(message)

    return jsonify({"reply": reply})


# ---------------- TEST ROUTE ----------------
@app.route("/test")
def test():
    return "Server working"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)