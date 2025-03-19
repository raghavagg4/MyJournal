from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
import base64
import os
from io import BytesIO
from .. import bcrypt
from werkzeug.utils import secure_filename
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm
from ..models import User
from ..movies.routes import get_b64_img

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

    if update_username_form.validate_on_submit():
        current_user.modify(username=update_username_form.username.data)
        current_user.save()
        return redirect(url_for("users.account"))

    if update_profile_pic_form.validate_on_submit():
        img = update_profile_pic_form.picture.data
        content_type = img.content_type

        if content_type not in ["image/jpeg", "image/png"]:
            flash("Invalid image type! Please upload a JPEG or PNG image.")
            return redirect(url_for("users.account"))

        img_data = BytesIO()
        img.save(img_data)
        img_data.seek(0)  # Reset position to beginning of file

        current_user.modify(profile_pic=img_data.getvalue(), profile_pic_content_type=content_type)
        current_user.save()
        return redirect(url_for("users.account"))

    # Get profile image using the utility function
    try:
        image = get_b64_img(current_user.username)
        content_type = current_user.profile_pic_content_type
    except Exception as e:
        # If there's any error getting the image, use the sample image
        sample_pic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Images', 'sample_pic.jpg')
        with open(sample_pic_path, 'rb') as f:
            bytes_im = BytesIO(f.read())
            image = base64.b64encode(bytes_im.getvalue()).decode()
            content_type = "image/jpeg"

    return render_template(
        "account.html",
        update_username_form=update_username_form,
        update_profile_pic_form=update_profile_pic_form,
        image=image,
        content_type=content_type
    )
