import uuid
import datetime
from flask import Blueprint, render_template, session, redirect, request, current_app, url_for,abort, flash
from movie_library.forms import MovieForm, ExtendedMovieForm, registerForm, LoginForm
from movie_library.models import Movie, User, Public_Comment
from dataclasses import asdict
from passlib.hash import pbkdf2_sha256
import functools



pages = Blueprint(
    "pages", __name__, template_folder = "templates", static_folder = "static"
)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))

        return route(*args, **kwargs)

    return route_wrapper

#***********INDEX************
@pages.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)
    movie_data = current_app.db.movie.find({"_id": {"$in": user.movies}})
    movies = [Movie(**movie) for movie in movie_data]

    return render_template(
        "index.html", 
        title = "Movies Watchlist",
        movies_data = movies
        )
#***********INDEX---END************

#***********PUBLIC_RED*************
@pages.route("/chat_publico")
def public_chat():

    return render_template('chat_publico.html', movies_data = None, title = "Movies Watchlist" )

@pages.route("/make_public/<string:_id>")
def make_public(_id):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    if not movie_data:
        abort(404)

    # Actualiza la visibilidad
    current_app.db.movie.update_one(
        {"_id": _id}, 
        {"$set": {"is_public": True}}  # Cambia a un booleano
    )

    return redirect(url_for(".movie", _id=_id))

@pages.route("/toggle_public/<string:_id>")
def toggle_public(_id):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    if not movie_data:
        abort(404)

    is_public = movie_data.get("is_public", False)  # Default False
    current_app.db.movie.update_one(
        {"_id": _id}, 
        {"$set": {"is_public": not is_public}}  # Cambia el estado
    )

    return redirect(url_for(".movie", _id=_id))

#***********PUBLIC_RED----END*************


#************USER_LOBBY****************
@pages.route("/add", methods=["GET", "POST"])
@login_required
def add_movie():

    form = MovieForm()

    if form.validate_on_submit():
        movie = Movie(
            _id = uuid.uuid4().hex,
            title =  form.title.data,
            director = form.director.data,
            year= form.year.data,
        )
        current_app.db.movie.insert_one(asdict(movie))
        current_app.db.user.update_one(
            {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
            )
        return redirect(url_for(".index"))

    return render_template(
        "new_movie.html",
        title="Movie Watchlist - Add Movie",
        form=form)

@pages.get("/movie/<string:_id>")
def movie(_id: str):

    movie_data = current_app.db.movie.find_one({"_id": _id})

    if not movie_data:
        abort(404) 

    movie = Movie(**movie_data)

    return render_template(
        "movie_details.html",
        movie = movie
    )

@pages.get("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id):

    rating = int(request.args.get("rating"))
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".movie", _id=_id))

@pages.get("/movie/<string:_id>/watch")
@login_required
def watch_movie(_id):

    current_app.db.movie.update_one(
            {"_id": _id}, 
            {"$set": {"last_watched": datetime.datetime.today()} }
        )

    return redirect(url_for(".movie", _id=_id))

@pages.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    form = ExtendedMovieForm(obj=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data

        current_app.db.movie.update_one({"_id": movie._id}, {"$set": asdict(movie)})
        return redirect(url_for(".movie", _id=movie._id))
    return render_template("movie_form.html", movie=movie, form=form)

#************USER_LOBBY------------END****************

#************DARK_LIGHT_MODE**********************
@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"

    else:
        session["theme"] = "dark"
    
    return redirect(request.args.get("current_page"))
#************DARK_LIGHT_MODE---------END**********************

#****************FUCTIONS*********************
@pages.route("/register", methods=["POST", "GET"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = registerForm()

    if form.validate_on_submit():
        # Verificar si el nombre de usuario ya existe
        existing_user = current_app.db.user.find_one({"username": form.username.data})
        if existing_user:
            flash("El nombre de usuario ya está en uso. Por favor, elige otro.", "error")
            return redirect(url_for(".register"))

        # Verificar si el correo electrónico ya existe
        existing_email = current_app.db.user.find_one({"email": form.email.data})
        if existing_email:
            flash("El correo electrónico ya está registrado. Por favor, utiliza otro.", "error")
            return redirect(url_for(".register"))

        # Crear el nuevo usuario
        user = User(
            _id=uuid.uuid4().hex,
            username=form.username.data,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )

        # Guardar el usuario en la base de datos
        current_app.db.user.insert_one(asdict(user))

        flash("Usuario registrado exitosamente", "success")
        return redirect(url_for(".login"))

    return render_template(
        "register.html", title="Movies Watchlist - Register", form=form
    )

@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = LoginForm()

    if form.validate_on_submit():
        user_data = current_app.db.user.find_one({"email": form.email.data})
        if not user_data:
            flash("Login credentials not correct", category="error")
            return redirect(url_for(".login"))
        user = User(**user_data)

        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email

            return redirect(url_for(".index"))

        flash("Login credentials not correct", category="error")

    return render_template("login.html", title="Movies Watchlist - Login", form=form)

@pages.route("/logout")
def logout():
    current_theme = session.get("theme")
    session.clear()
    session["theme"] = current_theme

    return redirect(url_for(".login"))

#****************FUCTIONS-----END*********************
