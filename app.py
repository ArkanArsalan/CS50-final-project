import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///MOVRAT.db")


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
    # Getting movies and user review data from databases
    movies = db.execute("SELECT id, title, year, rating FROM movies ORDER BY rating DESC LIMIT 10")
    user_review = db.execute("SELECT users.username AS username, movies.title AS title, user_review.review_comment AS comment, user_review.rating AS rating FROM user_review JOIN movies ON user_review.movie_id = movies.id JOIN users ON user_review.user_id = users.id LIMIT 3")
    return render_template("index.html", movies=movies, user_review=user_review)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Collect username and password
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username, password, and confirmation password submitted
        if not username:
            error_message = "Must provide username"
            flash(error_message)
            return render_template("login.html")
        if not password:
            error_message = "Must provide password"
            flash(error_message)
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], password):
            error_message = "Pasword incorrect"
            flash(error_message)
            return render_template("login.html")

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
    

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        # Get the data from user (movie name, rating, comment)
        movie_name = request.form.get("movie-name")
        rating = request.form.getlist("rating")
        comment = request.form.get("comment")
        

        # Ensure user insert all the data required
        if not movie_name:
            error_message = "Must provide movie name"
            flash(error_message)
        elif not rating:
            error_message = "Must select rating"
            flash(error_message)
        elif not comment:
            error_message = "Must provide comment"
            flash(error_message)
        else:
            # Get user id and movie id
            user_id = session["user_id"]
            movie_id = db.execute("SELECT id FROM movies WHERE title = ?", movie_name)
            if not movie_id:
                flash("Movie doesn't exist")
                return redirect("/review")
            else:
                # Insert data user review to database
                datetoday = date.today()
                comment_date = datetoday.strftime("%d %B, %Y")
                db.execute("INSERT INTO user_review (user_id, movie_id, rating, review_comment, datetime) VALUES (?, ?, ?, ?, ?)", user_id, int(movie_id[0]["id"]), rating, comment, comment_date)
                # Update rating accumulation
                movie_rating = db.execute("SELECT * FROM user_review WHERE movie_id = ?", int(movie_id[0]["id"]))
                sum = 0
                for row in movie_rating:
                    sum += int(row["rating"])
                avg_rating = sum / len(movie_rating)
                db.execute("UPDATE movies SET rating = ? WHERE id = ?", avg_rating, int(movie_id[0]["id"]))
                return redirect("/")
    else:
        return render_template("review.html")


@app.route("/movies", methods=["GET", "POST"])
@login_required
def movies():
    if request.method == "POST":
        movie_name = request.form.get("movie-name")
        movie_year_release = request.form.get("movie-year")
        
        if not movie_name:
            error_message = "Movie name required"
            flash(error_message)

        if not movie_year_release:
            outputs = db.execute("SELECT * FROM movies WHERE title LIKE ? ORDER BY rating DESC LIMIT 100", "%"+movie_name+"%")
            return render_template("movies.html", outputs=outputs)
        else:
            movie_year_release = int(movie_year_release)
            outputs = db.execute("SELECT * FROM movies WHERE title LIKE ? AND year == ? ORDER BY rating DESC LIMIT 100", "%"+movie_name+"%", movie_year_release)
            return render_template("movies.html", outputs=outputs)
    
    else:
        outputs = db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 100")
        return render_template("movies.html", outputs=outputs)


@app.route("/actors", methods=["GET", "POST"])
@login_required
def actors():
    return render_template("actors.html")


@app.route("//<string:movie_title>")
@login_required
def add_watchlater_main_page(movie_title):
    print(f"movie title: {movie_title}")
    # Get the user id
    user_id = session["user_id"]

    # Get movie id
    new_movie_id = db.execute("SELECT id FROM movies WHERE title = ?", movie_title) 

    # Handling if movie_id not found
    if not new_movie_id:
        return redirect("/watchlater")

    # Check if already in watchlater list  
    in_list = False
    list_watchlater = db.execute("SELECT * FROM watch_later WHERE user_id = ?", user_id)
    for row in list_watchlater:
        if row["movie_id"] == new_movie_id[0]["id"]:
            error_message = "Already in watch later"
            flash(error_message)
            in_list = True
            return redirect("/")
    
    # Insert the data to watch_later table in database
    if not in_list:
        db.execute("INSERT INTO watch_later(movie_id, user_id) VALUES (?, ?)", new_movie_id[0]["id"], user_id)
    
    # Redirect to index page
    return redirect("/")

@app.route("/movies/<string:movie_title>")
@login_required
def add_watchlater_movies_page(movie_title):
    # Get the user id
    user_id = session["user_id"]

    # Get movie id
    new_movie_id = db.execute("SELECT id FROM movies WHERE title = ?", movie_title) 

    # Handling if movie_id not found
    if not new_movie_id:
        return redirect("/watchlater")

    # Check if already in watchlater list  
    in_list = False
    list_watchlater = db.execute("SELECT * FROM watch_later WHERE user_id = ?", user_id)
    for row in list_watchlater:
        if row["movie_id"] == new_movie_id[0]["id"]:
            error_message = "Already in watch later"
            flash(error_message)
            in_list = True
            return redirect("/movies")
    
    # Insert the data to watch_later table in database
    if not in_list:
        db.execute("INSERT INTO watch_later(movie_id, user_id) VALUES (?, ?)", new_movie_id[0]["id"], user_id)

    return redirect("/movies")


@app.route("/watchlater")
@login_required
def watch_later():
    # Get list of watchlater movies from the databases
    user_id = session["user_id"]
    movie_list = db.execute("SELECT movies.title, movies.year FROM movies JOIN watch_later ON movies.id = watch_later.movie_id WHERE watch_later.user_id = ?", user_id)
    
    return render_template("watchlater.html", movie_list=movie_list)


@app.route("/watchlater/<string:movie_title>")
@login_required
def remove_watchlater(movie_title):
    # Get movie id
    movie_id = db.execute("SELECT id FROM movies WHERE title = ?", movie_title)

    # Handling if movie_id not found
    if not movie_id:
        return redirect("/watchlater")
    
    # Get user_id
    user_id = session["user_id"]

    # Remove the movie from watch_later table in database
    db.execute("DELETE FROM watch_later WHERE movie_id = ? AND user_id = ?", movie_id[0]["id"], user_id)
    
    # Redirect to watchlater page
    return redirect("/watchlater")

if __name__ == "__main__":
    app.run()