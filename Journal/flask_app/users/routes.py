from flask import Blueprint, redirect, url_for, render_template, flash, request, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from .. import bcrypt, db
from ..forms import RegistrationForm, LoginForm, JournalEntryForm
from ..models import User, JournalEntry, APICallCounter
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

    if form.validate_on_submit():
        print("DEBUG: Form submitted and validated")
        try:
            encrypted_content = JournalEntry.encrypt_content(
                form.content.data,
                str(current_user.id)
            )

            if entry_id:
                print(f"DEBUG: Attempting to update entry with ID: {entry_id}")
                entry_to_update = JournalEntry.objects(id=entry_id, user=current_user.id).first()
                if entry_to_update:
                    entry_to_update.update(
                        title=form.title.data,
                        content=encrypted_content,
                        updated_at=datetime.now()
                    )
                    print("DEBUG: Entry update successful")
                    flash("Journal entry updated successfully!")
                    return redirect(url_for("users.journal", entry_id=entry_id))
                else:
                    print(f"DEBUG: Entry {entry_id} not found or access denied during update attempt.")
                    flash("Journal entry not found or access denied.")
                    return redirect(url_for("users.journal"))
            else:
                print("DEBUG: Creating new entry")
                entry = JournalEntry(
                    user=current_user.id,
                    title=form.title.data,
                    content=encrypted_content,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                entry.save()
                print("DEBUG: New entry saved successfully")
                flash("Journal entry saved successfully!")
                return redirect(url_for("users.journal", entry_id=str(entry.id)))

        except Exception as e:
            print(f"ERROR: Error saving/updating journal entry: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f"An error occurred while saving the entry. Please try again.")

    page = request.args.get('page', 1, type=int)
    per_page = 10
    entries_obj = None
    decrypted_entries = []
    try:
        entries_obj = JournalEntry.objects(user=current_user.id).order_by('-created_at').paginate(page=page, per_page=per_page)

        for entry in entries_obj.items:
            try:
                decrypted_entries.append({
                    'id': str(entry.id),
                    'title': entry.title,
                    'created_at': entry.created_at,
                    'updated_at': entry.updated_at
                })
            except Exception as e:
                print(f"DEBUG: Error processing entry for list: {entry.id} - {e}")
                decrypted_entries.append({
                    'id': str(entry.id),
                    'title': "Error processing title",
                    'created_at': None,
                    'updated_at': None
                })

    except Exception as e:
        print(f"ERROR: Error loading journal entries for render: {str(e)}")
        flash(f"Error loading journal entries list.")
        entries_obj = None
        decrypted_entries = []

    current_selected_entry = None
    if entry_id:
        try:
            entry_obj = JournalEntry.objects(id=entry_id, user=current_user.id).first()
            if entry_obj:
                current_selected_entry = {
                    'id': str(entry_obj.id),
                    'title': entry_obj.title,
                    'content': entry_obj.decrypt_content(),
                    'created_at': entry_obj.created_at,
                    'updated_at': entry_obj.updated_at
                }
                if not form.is_submitted():
                    form.title.data = current_selected_entry['title']
                    form.content.data = current_selected_entry['content']
            else:
                if not flash:
                    flash("Journal entry not found or access denied.")
                return redirect(url_for("users.journal"))
        except Exception as e:
            print(f"ERROR: Error loading specific journal entry {entry_id}: {str(e)}")
            if not flash: flash(f"Error loading journal entry.")
            return redirect(url_for("users.journal"))

    return render_template("journal/index.html",
                           form=form,
                           entries=decrypted_entries,
                           selected_entry=current_selected_entry,
                           pagination=entries_obj)

@users.route("/journal/<entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    try:
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
    api_call_count = None

    try:
        # Get API call count
        counter = APICallCounter.objects.first()
        api_call_count = counter.counter if counter else 0
    except Exception as e:
        flash(f"Error fetching API call count: {str(e)}", "error")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "show_all_entries":
            try:
                collections = db.connection.get_database(db.get_db().name).list_collection_names()
                all_entries = {}

                for collection_name in collections:
                    collection = db.connection.get_database(db.get_db().name)[collection_name]
                    entries = list(collection.find({"email": {"$exists": True}}, {"email": 1, "_id": 0}))
                    if entries:
                        all_entries[collection_name] = entries
            except Exception as e:
                flash(f"Error fetching entries: {str(e)}", "error")
        elif action == "delete_user":
            try:
                email = request.form.get("email")
                if not email:
                    flash("Please provide an email address", "error")
                    return render_template("admin.html", all_entries=all_entries, api_call_count=api_call_count)

                collections = db.connection.get_database(db.get_db().name).list_collection_names()
                deleted = False

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

    return render_template("admin.html", all_entries=all_entries, api_call_count=api_call_count)
