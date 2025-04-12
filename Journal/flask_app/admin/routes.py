from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from .. import db

admin = Blueprint("admin", __name__)

@admin.route("/admin", methods=["GET", "POST"])
@login_required
def admin_panel():
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
