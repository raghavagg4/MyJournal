from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from .. import bcrypt, db
from ..forms import RegistrationForm, LoginForm
from ..models import User

users = Blueprint("users", __name__)

@users.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("users.welcome"))
    return redirect(url_for("users.login"))

@users.route("/welcome", methods=["GET"])
@login_required
def welcome():
    try:
        return render_template("welcome.html")
    except Exception as e:
        flash("An error occurred. Please try logging in again.")
        return redirect(url_for("users.login"))

""" ************ User Management views ************ """


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("users.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            user = User(username=form.username.data, email=form.email.data, password=hashed)
            user.save()
            flash("Your account has been created! You can now log in.")
            return redirect(url_for("users.login"))
        except Exception as e:
            flash(f"Database connection error: {str(e)}. Please try again later.")
            return render_template("register.html", form=form)

    return render_template("register.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users.index"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.objects(username=form.username.data).first()

            if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("users.welcome"))
            else:
                flash("Login failed. Check your username and password.")
                return redirect(url_for("users.login"))
        except Exception as e:
            flash(f"Database connection error: {str(e)}. Please try again later.")
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("users.index"))

@users.route("/admin", methods=["GET", "POST"])
def admin():
    all_entries = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "show_all_entries":
            try:
                # Get all collections from the database
                collections = db.connection.get_database(db.get_db().name).list_collection_names()
                all_entries = {}

                # Fetch only email fields from each collection
                for collection_name in collections:
                    collection = db.connection.get_database(db.get_db().name)[collection_name]
                    # Only fetch documents that have an email field
                    entries = list(collection.find({"email": {"$exists": True}}, {"email": 1, "_id": 0}))
                    if entries:  # Only add collections that have entries with emails
                        all_entries[collection_name] = entries
            except Exception as e:
                flash(f"Error fetching entries: {str(e)}", "error")
        elif action == "delete_user":
            try:
                email = request.form.get("email")
                if not email:
                    flash("Please provide an email address", "error")
                    return render_template("admin.html", all_entries=all_entries)

                # Get all collections
                collections = db.connection.get_database(db.get_db().name).list_collection_names()
                deleted = False

                # Try to delete from each collection
                for collection_name in collections:
                    collection = db.connection.get_database(db.get_db().name)[collection_name]
                    result = collection.delete_many({"email": email})
                    if result.deleted_count > 0:
                        deleted = True

                if deleted:
                    flash(f"Successfully deleted all entries for email: {email}", "success")
                else:
                    flash(f"No entries found for email: {email}", "warning")
            except Exception as e:
                flash(f"Error deleting user: {str(e)}", "error")

    return render_template("admin.html", all_entries=all_entries)
