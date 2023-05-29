import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
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
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect data from user
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation_pass = request.form.get("confirmation")

        # Ensure username, password, and confirmation password submitted
        if not username:
            error_message = "Must provide username"
            flash(error_message)
            return redirect("/register")
        if not password:
            error_message = "Must provide password"
            flash(error_message)
            return redirect("/register")
        if not confirmation_pass:
            error_message = "Must provide confirmation password"
            flash(error_message)
            return redirect("/register")

        # Check if password and confirmation_pass password do not match
        if confirmation_pass != password:
            error_message = "Confirmation password do not match"
            flash(error_message)
            return redirect("/register")

        # Check if username already in database
        user = db.execute("SELECT * FROM users")
        for row in user:
            if username == row["username"]:
                error_message = "Username already been used"
                flash(error_message)
                return redirect("/register")
        else:
            # Insert new user info to database
            hash_password = generate_password_hash(password)
            new_user = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", username, hash_password)
            session["user_id"] = new_user
        return redirect("/")

    else:
        return render_template("register.html")



