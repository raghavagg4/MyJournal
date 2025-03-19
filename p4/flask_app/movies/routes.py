import base64,io
from io import BytesIO
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user
import os

from .. import movie_client
from ..forms import MovieReviewForm, SearchForm
from ..models import User, Review
from ..utils import current_time

movies = Blueprint("movies", __name__)
""" ************ Helper for pictures uses username to get their profile picture************ """
def get_b64_img(username):
    user = User.objects(username=username).first()
    content_type = "image/jpeg"  # Default for sample image

    if not user or not user.profile_pic:
        # Use sample picture when profile pic is None
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Images', 'sample_pic.jpg'), 'rb') as f:
            bytes_im = io.BytesIO(f.read())
    else:
        bytes_im = io.BytesIO(user.profile_pic)
        if user.profile_pic_content_type:
            content_type = user.profile_pic_content_type

    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image, content_type

""" ************ View functions ************ """


@movies.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("movies.query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@movies.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    try:
        results = movie_client.search(query)
    except ValueError as e:
        return render_template("query.html", error_msg=str(e))

    return render_template("query.html", results=results)


@movies.route("/movies/<movie_id>", methods=["GET", "POST"])
def movie_detail(movie_id):
    try:
        result = movie_client.retrieve_movie_by_id(movie_id)
    except ValueError as e:
        return render_template("movie_detail.html", error_msg=str(e))

    form = MovieReviewForm()
    if form.validate_on_submit():
        review = Review(
            commenter=current_user._get_current_object(),
            content=form.text.data,
            date=current_time(),
            imdb_id=movie_id,
            movie_title=result.title,
        )

        review.save()

        return redirect(request.path)

    reviews = Review.objects(imdb_id=movie_id)

    # Add profile pictures to reviews
    reviews_with_images = []
    for review in reviews:
        review_dict = {
            'commenter': review.commenter,
            'content': review.content,
            'date': review.date,
            'movie_title': review.movie_title,
            'image': None
        }

        try:
            review_dict['image'], review_dict['content_type'] = get_b64_img(review.commenter.username)
        except Exception as e:
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Images', 'sample_pic.jpg'), 'rb') as f:
                bytes_im = BytesIO(f.read())
                review_dict['image'] = base64.b64encode(bytes_im.getvalue()).decode()
                review_dict['content_type'] = "image/jpeg"

        reviews_with_images.append(review_dict)

    return render_template(
        "movie_detail.html", form=form, movie=result, reviews=reviews_with_images
    )


@movies.route("/user/<username>")
def user_detail(username):
    user = User.objects(username=username).first()

    if not user:
        return render_template("user_detail.html", error="User not found")

    reviews = Review.objects(commenter=user)

    image = None
    try:
        image, content_type = get_b64_img(username)
    except Exception as e:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Images', 'sample_pic.jpg'), 'rb') as f:
            bytes_im = BytesIO(f.read())
            image = base64.b64encode(bytes_im.getvalue()).decode()
            content_type = "image/jpeg"

    return render_template(
        "user_detail.html",
        username=username,
        reviews=reviews,
        image=image,
        content_type=content_type
    )
