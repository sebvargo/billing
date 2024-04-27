import datetime
import os
import requests
import sqlalchemy as sa

from app import db
from app.main import bp
from app.models import Document, User
from app.utils import (
    utc_time_now,
   )
from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response, 
    stream_with_context,
    request
)
from flask_login import login_required, current_user


# ___________________________________________________________________________________________
@bp.before_request
def before_request():
    if current_user.is_authenticated and User.check_token(current_user.token):
        session.permanent = True
        current_app.permanent_session_lifetime = datetime.timedelta(minutes=60)
        session.modified = True
        current_user.last_seen = utc_time_now()
        db.session.commit()
    else:
        flash("Session expired. Please log in again.", "danger")
        return redirect(url_for("auth.logout"))


# ___________________________________________________________________________________________
@bp.route("/")
def main():
    return redirect(url_for("auth.login"))



# ___________________________________________________________________________________________
@bp.route("/home")
@login_required
def home():
    # Get all the documents for the current user

    query = current_user.documents.select()
    documents = db.session.scalars(query).all()
    token = current_user.token
    
    return render_template("main/home.html", title="Home", documents=documents, token=token)



# ___________________________________________________________________________________________

@bp.route("/pdf_proxy")
def pdf_proxy():
    pdf_url = request.args.get(
        "pdf_url"
    )  # Assuming you pass the signed URL as a query parameter
    if not pdf_url:
        return "Missing PDF URL", 400

    req = requests.get(pdf_url, stream=False)

    return Response(
        stream_with_context(req.iter_content()), content_type="application/pdf"
    )
