from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
import base64
import os
from io import BytesIO
from .. import bcrypt
from werkzeug.utils import secure_filename
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm
from ..models import User

users = Blueprint("users", __name__)

""" ************ User Management views ************ """


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("movies.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        user.save()

        return redirect(url_for("users.login"))

    return render_template("register.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("movies.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()

        if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("users.account"))
        else:
            flash("Login failed. Check your username and password.")
            return redirect(url_for("users.login"))

    return render_template("login.html", form=form)


@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("movies.index"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    update_username_form = UpdateUsernameForm()
    update_profile_pic_form = UpdateProfilePicForm()

    if request.method == "POST":
        if update_username_form.submit_username.data and update_username_form.validate():
            current_user.modify(username=update_username_form.username.data)
            current_user.save()
            flash("Username has been updated!")
            return redirect(url_for("users.account"))

        if update_profile_pic_form.submit_picture.data and update_profile_pic_form.validate():
            # Get the uploaded image data
            image = update_profile_pic_form.picture.data
            if image:
                image_data = image.read()
                if image_data:  # Ensure we have actual image data
                    # Handle the two cases: replacing vs adding a profile picture
                    if current_user.profile_pic:
                        # Case 1: User already has a profile picture - replace it
                        current_user.modify(profile_pic=image_data)
                        current_user.save()
                        flash("Profile picture has been updated!")
                    else:
                        # Case 2: User doesn't have a profile picture - add the uploaded one
                        current_user.modify(profile_pic=image_data)
                        current_user.save()
                        flash("Profile picture has been added!")

                    # Verify the image was saved correctly
                    user = User.objects(username=current_user.username).first()
                    if not user or not user.profile_pic:
                        flash("Error: Profile picture was not saved properly. Please try again.")
                else:
                    flash("Unable to read image data. Please try again.")
            return redirect(url_for("users.account"))

    image = None
    if current_user.profile_pic:
        bytes_im = BytesIO(current_user.profile_pic)
        image = base64.b64encode(bytes_im.getvalue()).decode()
    else:
        # Use sample picture when profile pic is None (for display only)
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Images', 'sample_pic.jpg'), 'rb') as f:
            bytes_im = BytesIO(f.read())
            image = base64.b64encode(bytes_im.getvalue()).decode()

    return render_template(
        "account.html",
        update_username_form=update_username_form,
        update_profile_pic_form=update_profile_pic_form,
        image=image
    )
