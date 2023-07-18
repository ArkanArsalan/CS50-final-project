import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
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
    celebs = db.execute("SELECT * FROM people WHERE favorite_vote > 0 ORDER BY favorite_vote DESC LIMIT 10")
    return render_template("index.html", movies=movies, celebs=celebs)


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


@app.route("/movies/id:<string:movie_id>")
@login_required
def movie_detail(movie_id):
    # Get user id
    user_id  = session["user_id"]

    # Handling if movie_id not found
    if not movie_id:
        return redirect("/movies")
    
    # Get all the movie information
    movie_info = db.execute("SELECT * FROM movies WHERE id = ?", movie_id)

    # Get the movie stars and director
    movie_stars = db.execute("SELECT * FROM people JOIN stars ON people.id = stars.person_id WHERE stars.movie_id = ?", movie_id)
    movie_directors = db.execute("SELECT * FROM people JOIN directors ON people.id = directors.person_id WHERE directors.movie_id = ?", movie_id)

    # Get user review
    user_review = db.execute("SELECT * FROM user_review JOIN users ON user_review.user_id = users.id WHERE movie_id = ? ORDER BY RANDOM() LIMIT 5", movie_id)

    # Return the page
    return render_template("movie_detail.html", movie_info=movie_info[0], movie_stars=movie_stars, movie_directors=movie_directors[0], user_review=user_review)
    
 
@app.route("/movies/user_review/id:<string:movie_id>")
@login_required
def movie_user_review(movie_id):
    # Get the data
    user_review = db.execute("SELECT * FROM user_review JOIN users ON user_review.user_id = users.id WHERE movie_id = ? ORDER BY RANDOM()", movie_id)
    movie_info = db.execute("SELECT * FROM movies WHERE id = ?", movie_id)
    print(movie_info)

    # return the page
    return render_template("movie_user_review.html", user_review=user_review, movie_info=movie_info)


@app.route("/celebs", methods=["GET", "POST"])
@login_required
def celebs():
    if request.method == "POST":
        celeb_name = request.form.get("celeb-name")
        birth_year = request.form.get("birth-year")
        print(birth_year)
        
        if not celeb_name:
            error_message = "Celeb name required"
            flash(error_message)

        if not birth_year:
            outputs = db.execute("SELECT * FROM people WHERE name LIKE ? ORDER BY birth DESC LIMIT 100", "%"+celeb_name+"%")
            return render_template("celebs.html", outputs=outputs)
        else:
            outputs = db.execute("SELECT * FROM people WHERE name LIKE ? AND birth == ? ORDER BY birth DESC LIMIT 100", "%"+celeb_name+"%", birth_year)
            return render_template("celebs.html", outputs=outputs)
    
    else:
        outputs = db.execute("SELECT * FROM people WHERE birth IS NOT NULL ORDER BY RANDOM() LIMIT 100")
        return render_template("celebs.html", outputs=outputs)


def insert_to_favceleb(celeb_id):
    # Get user id
    user_id = session["user_id"]

    # Handling if celeb_id not found
    if not celeb_id:
        return redirect("/celebs")

    # Check if already in favorite celebs list
    list_favorite_celeb = db.execute("SELECT * FROM favorite_celebs WHERE user_id = ?", user_id)
    for row in list_favorite_celeb:
        if str(row["person_id"]) == celeb_id:
            return False
    
    # Insert the data to watch_later table in database
    db.execute("INSERT INTO favorite_celebs(person_id, user_id) VALUES (?, ?)", celeb_id, user_id)
    
    # Update favorite vote data on people table
    curr_vote = db.execute("SELECT favorite_vote FROM people WHERE id = ?", celeb_id)
    new_vote = curr_vote[0]["favorite_vote"] + 1
    db.execute("UPDATE people SET favorite_vote = ? WHERE id = ?", new_vote, celeb_id)
    return True


@app.route("/celebs/addfav/id:<string:celeb_id>")
@login_required
def add_favorite_celeb_celebs_page(celeb_id):
    # If celeb already in favorite list flash error message
    if not insert_to_favceleb(celeb_id):
        error_message = "Already in your favorite list"
        flash(error_message)

    # Redirect to celeb page
    return redirect(url_for("celebs"))


@app.route("//addfav/id:<string:celeb_id>")
@login_required
def add_favorite_celeb_main_page(celeb_id):
    # If celeb already in favorite list flash error message
    if not insert_to_favceleb(celeb_id):
        error_message = "Already in your favorite list"
        flash(error_message)

    # Redirect to celeb page
    return redirect(url_for("index"))


@app.route("/celebs/actor_director/addfav/id<string:celeb_id>")
@login_required
def add_favorite_celeb_movie_list_actor_director_page(celeb_id):
    # If celeb already in favorite list flash error message
    if not insert_to_favceleb(celeb_id):
        error_message = "Already in your favorite list"
        flash(error_message)

    # Redirect to celeb page
    return redirect(url_for("celeb_movie_list", celeb_id=celeb_id))


@app.route("/celebs/actor/addfav/id<string:celeb_id>")
@login_required
def add_favorite_celeb_movie_list_actor_page(celeb_id):
    # If celeb already in favorite list flash error message
    if not insert_to_favceleb(celeb_id):
        error_message = "Already in your favorite list"
        flash(error_message)

    # Redirect to celeb page
    return redirect(url_for("celeb_movie_list", celeb_id=celeb_id))


@app.route("/celebs/director/addfav/id<string:celeb_id>")
@login_required
def add_favorite_celeb_movie_list_director_page(celeb_id):
    # If celeb already in favorite list flash error message
    if not insert_to_favceleb(celeb_id):
        error_message = "Already in your favorite list"
        flash(error_message)

    # Redirect to celeb page
    return redirect(url_for("celeb_movie_list", celeb_id=celeb_id))


def insert_to_watchlater(movie_id):
    # Get user id
    user_id = session["user_id"]

    # Handling if movie_id not found
    if not movie_id:
        return redirect("/watchlater")

    # Check if already in watchlater list  
    list_watchlater = db.execute("SELECT * FROM watch_later WHERE user_id = ?", user_id)
    for row in list_watchlater:
        if str(row["movie_id"]) == movie_id:
            return False

    # Insert the data to watch_later table in database
    db.execute("INSERT INTO watch_later(movie_id, user_id) VALUES (?, ?)", movie_id, user_id)
    return True


@app.route("//add/<string:movie_id>")
@login_required
def add_watchlater_main_page(movie_id):
    # If movies already in watchlater list flash error message
    if not insert_to_watchlater(movie_id):
        error_message = "Already in watch later"
        flash(error_message)

    # Redirect to main page
    return redirect(url_for("index"))


@app.route("/movies/add/<string:movie_id>")
@login_required
def add_watchlater_movies_page(movie_id):
    # If movies already in watchlater list flash error message
    if not insert_to_watchlater(movie_id):
        error_message = "Already in watch later"
        flash(error_message)

    # Redirect to movies page
    return redirect(url_for("movies"))


@app.route("/movies/detail/add/<string:movie_id>")
@login_required
def add_watchlater_movies_detail_page(movie_id):
    # If movies already in watchlater list flash error message
    if not insert_to_watchlater(movie_id):
        error_message = "Already in watch later"
        flash(error_message)

    # Redirect to movies page
    return redirect(url_for("movie_detail", movie_id=movie_id))


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


def is_director(celeb_id):
    # Check celeb id in director table
    director = db.execute("SELECT * FROM directors WHERE person_id = ?", celeb_id)

    # return true if data exist otherwise false
    if not director:
        return False
    return True


def is_actor(celeb_id):
    # Check celeb id in director table
    actor = db.execute("SELECT * FROM stars WHERE person_id = ?", celeb_id)

    # return true if data exist otherwise false
    if not actor:
        return False
    return True


@app.route("/celebs/id:<string:celeb_id>")
@login_required
def celeb_movie_list(celeb_id):
    # Check is celeb director or actor
    actor = is_actor(celeb_id)
    director = is_director(celeb_id)

    # Find list movie if celeb is actor
    if actor == True and director == False:
        movie_list = db.execute("SELECT * FROM movies JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id WHERE people.id = ?", celeb_id)
        return render_template("movie_list_actor.html", movie_list=movie_list)
    # Find list movie if celeb is director
    elif actor == False and director == True:
        movie_list = db.execute("SELECT * FROM movies JOIN directors on movies.id = directors.movie_id JOIN people ON directors.person_id = people.id WHERE people.id = ?", celeb_id)
        return render_template("movie_list_director.html", movie_list=movie_list)
    # Find list movie if celeb director and actor
    elif actor == True and director == True:
        movie_list_actor = db.execute("SELECT * FROM movies JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id WHERE people.id = ?", celeb_id)
        movie_list_director = db.execute("SELECT * FROM movies JOIN directors on movies.id = directors.movie_id JOIN people ON directors.person_id = people.id WHERE people.id = ?", celeb_id)
        return render_template("movie_list_actor_director.html", movie_list_actor=movie_list_actor, movie_list_director=movie_list_director)

if __name__ == "__main__":
    app.run(debug=True)