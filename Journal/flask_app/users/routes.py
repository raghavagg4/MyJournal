from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from .. import bcrypt, db
from ..forms import RegistrationForm, LoginForm, JournalEntryForm
from ..models import User, JournalEntry
from datetime import datetime

users = Blueprint("users", __name__)

@users.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("users.journal"))
    return redirect(url_for("users.login"))

@users.route("/welcome", methods=["GET"])
@login_required
def welcome():
    try:
        return render_template("welcome.html")
    except Exception as e:
        flash("An error occurred. Please try logging in again.")
        return redirect(url_for("users.login"))

@users.route("/journal", methods=["GET", "POST"])
@users.route("/journal/<entry_id>", methods=["GET", "POST"])
@login_required
def journal(entry_id=None):
    form = JournalEntryForm()
    selected_entry = None
    decrypted_entries = []

    # Load entries with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of entries per page

    try:
        # Get entries with projection to only fetch needed fields
        entries = JournalEntry.objects(user=current_user.id).only(
            'title', 'created_at', 'updated_at'
        ).order_by('-created_at').paginate(page=page, per_page=per_page)

        # Decrypt only the entries for the current page
        for entry in entries.items:
            decrypted_entries.append({
                'id': str(entry.id),
                'title': entry.title,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            })

        if entry_id:
            # Load only the selected entry with all fields
            selected_entry = JournalEntry.objects(id=entry_id, user=current_user.id).first()
            if selected_entry:
                form.title.data = selected_entry.title
                form.content.data = selected_entry.decrypt_content()

    except Exception as e:
        flash(f"Error loading journal entries: {str(e)}")
        entries = []

    if form.validate_on_submit():
        try:
            # Encrypt the journal entry content
            encrypted_content = JournalEntry.encrypt_content(
                form.content.data,
                str(current_user.id)
            )

            if selected_entry:
                # Update existing entry
                entry = JournalEntry.objects(id=entry_id, user=current_user.id).first()
                if entry:
                    entry.update(
                        title=form.title.data,
                        content=encrypted_content,
                        updated_at=datetime.now()
                    )
                    flash("Journal entry updated successfully!")
                else:
                    flash("Journal entry not found.")
            else:
                # Create new entry
                entry = JournalEntry(
                    user=current_user.id,
                    title=form.title.data,
                    content=encrypted_content,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entry.save()
                flash("Journal entry saved successfully!")

            return redirect(url_for("users.journal"))
        except Exception as e:
            flash(f"Error saving journal entry: {str(e)}")

    return render_template("journal/index.html", form=form, entries=decrypted_entries, selected_entry=selected_entry)

@users.route("/journal/<entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    try:
        # Ensure the entry belongs to the current user
        entry = JournalEntry.objects(id=entry_id, user=current_user.id).first()
        if entry:
            entry.delete()
            flash("Journal entry deleted successfully.")
        else:
            flash("Journal entry not found.")
    except Exception as e:
        flash(f"Error deleting entry: {str(e)}")

    return redirect(url_for("users.journal"))

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
                return redirect(url_for("users.journal"))
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
