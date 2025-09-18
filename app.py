import os
from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    request,
    session,
    url_for,
)
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import mysql.connector
from hashlib import sha256
from config import dbHost, dbpasswd, dbport, dbuser, db

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")


# Config MySQL - Use connection pooling for better performance
def get_db_connection():
    return mysql.connector.connect(
        host=dbHost,
        user=dbuser,
        password=dbpasswd,
        port=dbport,
        database=db,
        autocommit=True,  # Enable autocommit to avoid manual commits
    )


# Home
@app.route("/")
def index():
    return render_template("home.html")


# Favicon Icon
@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicon.ico"))


# About
@app.route("/about")
def about():
    return render_template("about.html")


# Articles
@app.route("/articles", methods=["GET"])
def articles():
    mydb = None
    mycursor = None
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        sql = "SELECT * FROM articles ORDER BY id DESC"
        mycursor.execute(sql)

        doc_2 = mycursor.fetchall()

        if doc_2:
            return render_template("articles.html", articles=doc_2)
        else:
            msg = "No Articles Found"
            return render_template("articles.html", msg=msg)

    except Exception as e:
        app.logger.error(f"Error in articles route: {e}")
        flash("Error loading articles", "danger")
        return render_template("articles.html", msg="Error loading articles")
    finally:
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()


# View Article
@app.route("/article/<int:id>/", methods=["GET"])
def articled(id):
    mydb = None
    mycursor = None
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        sql = "SELECT * FROM articles WHERE id = %s"
        mycursor.execute(sql, (id,))

        doc = mycursor.fetchone()

        if doc:
            return render_template("article.html", article=doc)
        else:
            flash("Article not found", "danger")
            return redirect(url_for("articles"))

    except Exception as e:
        app.logger.error(f"Error in article view: {e}")
        flash("Error loading article", "danger")
        return redirect(url_for("articles"))
    finally:
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()


# Register Form
class RegisterForm(Form):  # Fixed class name typo
    name = StringField("Name", [validators.Length(min=1, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50), validators.Email()])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.Length(min=6),
            validators.EqualTo("confirm", message="Passwords do not match"),
        ],
    )
    confirm = PasswordField("Confirm Password")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        password = password.encode("utf-8")
        password = sha256(password).hexdigest()

        mydb = None
        mycursor = None
        try:
            mydb = get_db_connection()
            mycursor = mydb.cursor()

            # Check if username or email already exists
            check_sql = "SELECT * FROM users WHERE username = %s OR email = %s"
            mycursor.execute(check_sql, (username, email))
            existing_user = mycursor.fetchone()

            if existing_user:
                flash("Username or email already exists", "danger")
                return render_template("register.html", form=form)

            # Insert new user
            sql = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)"
            val = (name, email, username, password)
            mycursor.execute(sql, val)

            flash("You are now registered and can log in", "success")
            return redirect(url_for("login"))  # Redirect to login instead of index

        except Exception as e:
            app.logger.error(f"Error in registration: {e}")
            flash("Registration failed. Please try again.", "danger")
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()

    return render_template("register.html", form=form)


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password_candidate = request.form.get("password")

        if not username or not password_candidate:
            error = "Please provide both username and password"
            return render_template("login.html", error=error)

        mydb = None
        mycursor = None
        try:
            mydb = get_db_connection()
            mycursor = mydb.cursor()

            sql = "SELECT * FROM users WHERE username = %s"
            mycursor.execute(sql, (username,))

            doc = mycursor.fetchone()

            if doc:
                hash_pass = doc[4]  # Assuming password is at index 4
                password = password_candidate.encode("utf-8")
                password = sha256(password).hexdigest()

                if password == hash_pass:
                    session["logged_in"] = True
                    session["username"] = username
                    app.logger.info("PASSWORD MATCHED")

                    flash("You are now logged in", "success")
                    return redirect(url_for("dashboard"))
                else:
                    app.logger.info("PASSWORD NOT MATCHED")
                    error = "Invalid Password"
                    return render_template("login.html", error=error)
            else:
                app.logger.info("NO USER IS MATCHED")
                error = "Username not found"
                return render_template("login.html", error=error)

        except Exception as e:
            app.logger.error(f"Error in login: {e}")
            error = "Login failed. Please try again."
            return render_template("login.html", error=error)
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()

    return render_template("login.html")


# Check Session
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please login", "danger")
            return redirect(url_for("login"))

    return wrap


# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You are logged out", "success")
    return redirect(url_for("login"))


# Dashboard
@app.route("/dashboard", methods=["GET"])
@is_logged_in
def dashboard():
    mydb = None
    mycursor = None
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        sql = "SELECT * FROM articles WHERE author = %s ORDER BY id DESC"
        mycursor.execute(sql, (session["username"],))

        doc_2 = mycursor.fetchall()

        if doc_2:
            return render_template("dashboard.html", articles=doc_2)
        else:
            msg = "No Articles Found"
            return render_template("dashboard.html", msg=msg)

    except Exception as e:
        app.logger.error(f"Error in dashboard: {e}")
        flash("Error loading dashboard", "danger")
        return render_template("dashboard.html", msg="Error loading dashboard")
    finally:
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()


# Article Form
class ArticleForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=200)])
    body = TextAreaField("Body", [validators.Length(min=30)])


# Add Article
@app.route("/add_article", methods=["GET", "POST"])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        mydb = None
        mycursor = None
        try:
            mydb = get_db_connection()
            mycursor = mydb.cursor()

            sql = "INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)"
            val = (title, body, session["username"])
            mycursor.execute(sql, val)

            flash("Article Created", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            app.logger.error(f"Error creating article: {e}")
            flash("Error creating article", "danger")
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()

    return render_template("add_article.html", form=form)


# Edit Article
@app.route("/edit_article/<int:id>/", methods=["GET", "POST"])
@is_logged_in
def edit_article(id):
    mydb = None
    mycursor = None
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        # Get the article
        mycursor.execute(
            "SELECT * FROM articles WHERE id = %s AND author = %s",
            (id, session["username"]),
        )
        article = mycursor.fetchone()

        if not article:
            flash("Article not found or you don't have permission to edit it", "danger")
            return redirect(url_for("dashboard"))

        form = ArticleForm(request.form)

        if request.method == "GET":
            form.title.data = article[1]  # Assuming title is at index 1
            form.body.data = article[3]  # Assuming body is at index 3

        if request.method == "POST" and form.validate():
            title = form.title.data
            body = form.body.data

            sql = "UPDATE articles SET title=%s, body=%s WHERE id=%s AND author=%s"
            val = (title, body, id, session["username"])
            mycursor.execute(sql, val)

            if mycursor.rowcount > 0:
                flash("Article Updated", "success")
            else:
                flash("No changes made or article not found", "warning")

            return redirect(url_for("dashboard"))

    except Exception as e:
        app.logger.error(f"Error editing article: {e}")
        flash("Error updating article", "danger")
    finally:
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()

    return render_template("edit_article.html", form=form)


# Delete Article
@app.route(
    "/delete_article/<int:id>", methods=["POST"]
)  # Changed to POST only for security
@is_logged_in  # Added authentication check
def delete_article(id):
    mydb = None
    mycursor = None
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        # Only allow deletion of user's own articles
        sql = "DELETE FROM articles WHERE id = %s AND author = %s"
        val = (id, session["username"])
        mycursor.execute(sql, val)

        if mycursor.rowcount > 0:
            flash("Article Deleted", "success")
        else:
            flash(
                "Article not found or you don't have permission to delete it", "danger"
            )

    except Exception as e:
        app.logger.error(f"Error deleting article: {e}")
        flash("Error deleting article", "danger")
    finally:
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(port=5001, debug=True)
