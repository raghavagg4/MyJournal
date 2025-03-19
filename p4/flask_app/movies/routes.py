import base64,io
from io import BytesIO
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import movie_client
from ..forms import MovieReviewForm, SearchForm
from ..models import User, Review
from ..utils import current_time

movies = Blueprint("movies", __name__)
""" ************ Helper for pictures uses username to get their profile picture************ """
def get_b64_img(username):
    user = User.objects(username=username).first()
    bytes_im = io.BytesIO(user.profile_pic)
    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image

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
            if review.commenter.profile_pic:
                review_dict['image'] = get_b64_img(review.commenter.username)
        except:
            # Handle case where profile picture might be corrupted or missing
            pass

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
    if user.profile_pic:
        try:
            image = get_b64_img(username)
        except:
            # Handle case where profile picture might be corrupted or missing
            pass

    return render_template(
        "user_detail.html",
        username=username,
        reviews=reviews,
        image=image
    )
