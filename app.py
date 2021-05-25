from helpers import apology, login_required, lookup, usd
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from tempfile import mkdtemp
from flask_session import Session
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from cs50 import SQL
from datetime import datetime
import os
import re


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///social_1000115132.db")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return jsonify(msg="Must provide username", code=400, redirect=False)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return jsonify(msg="Must provide password", code=400, redirect=False)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return jsonify(msg="Authentication failed", code=400, redirect=False)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return jsonify(code=200, redirect=True)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return jsonify(msg="Must provide username", code=400, redirect=False)

        # Query database for username match
        elif not len(db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))) == 0:
            return jsonify(msg="Username is already taken", code=400, redirect=False)

        elif not len(db.execute("SELECT id FROM users WHERE email = ?", request.form.get("email"))) == 0:
            return jsonify(msg="this email has account already", code=400, redirect=False)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return jsonify(msg="Must provide password", code=400, redirect=False)

        # Ensure password is strong enough
        # elif not re.fullmatch(r'[A-Za-z0-9@#$%^&+=]{8,}', request.form.get("password")):
        #     return jsonify(msg="Weak password must contain: At least 8 characters, uppercase letters: A-Z, lowercase letters: a-z, numbers: 0-9, any of the special characters: @#$%^&+=", code=400, redirect=False)

        # Set optional field to NULL if left empty
        last_name = 'NULL' if not request.form.get(
            "last_name") else request.form.get("last_name")
        address = 'NULL' if not request.form.get(
            "address") else request.form.get("address")
        birth_date = 'NULL' if not request.form.get(
            "birth_date") else request.form.get("birth_date")
        bio = 'NULL' if not request.form.get(
            "bio") else request.form.get("bio")
        gender = 'NULL' if not request.form.get(
            "gender") else request.form.get("gender")

        # Insert the new user's data to the DataBase
        id = db.execute("INSERT INTO users (first_name, last_name, username, email, password, birth_date, address, bio, gender_id) VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?)",
                        request.form.get("first_name"), last_name, request.form.get(
                            "username"), request.form.get("email"),
                        generate_password_hash(request.form.get("password")), request.form.get("birth_date"), address, bio, gender)

        # Remember which user has logged in
        session["user_id"] = id

        # Redirect user to home page
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        genders = db.execute("SELECT id, name FROM gender")
        return render_template("register.html", genders=genders)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        db.execute("INSERT INTO posts (content, user_id) VALUES (?, ?)",
                   request.form.get('content'), session['user_id'])
        return redirect("/profile")

    else:
        # User reached route via GET (as by clicking a link or via redirect)
        user = db.execute(
            f"SELECT username FROM users WHERE id = {session['user_id']}")
        posts = db.execute(
            f"SELECT p.id, u.username, p.content, p.created_at FROM users u, posts p WHERE p.user_id = { session['user_id'] }")
        for post in posts:
            post['comments'] = db.execute(
                f"SELECT c.content, u.username FROM users u, comments c WHERE post_id = {post['id']} and u.id = c.user_id")

            post['like_count'] = db.execute(
                f"SELECT count(id) as count FROM likes WHERE post_id = {post['id']}")

        return render_template("profile.html", posts=posts, user=user)


@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    db.execute("INSERT INTO comments (content, user_id, post_id) VALUES (?, ?, ?)",
               request.form.get('content'), session['user_id'], post_id)
    return redirect("/profile")


@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    db.execute("INSERT INTO likes ( user_id, post_id) VALUES (?, ?)",
               session['user_id'], post_id)
    return redirect("/profile")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
