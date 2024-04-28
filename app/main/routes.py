import datetime
import os
import requests
import stripe
import sqlalchemy as sa
import time


from app import db
from app.classes import PDFClient
from app.llm import generate_invoice_schedule
from app.main import bp
from app.models import Document, User, Schedule
from app.utils import (
    utc_time_now,
    safely_save_file,
    validate_file_extension,
    check_file_size,
    is_file_present
   )
from datetime import timezone
from flask import (
    abort,
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
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import HTTPException
from werkzeug.http import HTTP_STATUS_CODES

auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

DOCUMENTS_PER_PAGE = int(os.environ.get("DOCUMENTS_PER_PAGE"))
OPEN_AI_EMBEDDINGS_MODEL = os.environ.get("OPEN_AI_EMBEDDINGS_MODEL")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

def error_response(status_code, message=None):
    payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
    if message:
        payload["message"] = message
    return payload, status_code


@auth.verify_password
def verify_password(username, password):
    query = sa.select(User).where(User.username == username)
    user = db.session.scalar(query)
    if user and user.check_password(password):
        return user

@auth.error_handler
def auth_error(status):
    return error_response(status)


@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)


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


@bp.route("/stripe/<int:schedule_id>")
@login_required
def stripe_bill(schedule_id):
    
    bill = db.session.get(Schedule, schedule_id)
    # Set your secret API key
    stripe.api_key = STRIPE_API_KEY

    # Define the customer ID & product details
    # TODO: Replace the customer_id with the actual customer ID from your Stripe account
    customer_id = {
        "EdgeDB": "cus_Q0GAyIdHPixUMv", 
        "Vals.ai": "cus_Q0Itweq1qw8MoT", 
        "Guardrails AI": "cus_Q0In85vECzYcos",
        "Guardrails Al": "cus_Q0In85vECzYcos",
    }
    customer = customer_id[bill.customer_name]
    product_description = "Software Platform"
    price_in_cents = int(bill.price * 100)
    due_date = bill.due_date
    currency = "usd"

    # Create the invoice explicitly linking the invoice items
    invoice = stripe.Invoice.create(
        customer=customer,
        auto_advance=False,  # Auto-advance invoices (auto-finalize) this might need to be set to false depending on the use case
        collection_method="send_invoice",
        due_date=int(due_date.timestamp()),
    )
    
    
    # Create an invoice item
    invoice_item = stripe.InvoiceItem.create(
        customer=customer,
        invoice=invoice.id,
        amount=price_in_cents,
        currency=currency,
        description=product_description
    )
    # Finalize and send the invoice
    finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)
    
    bill.sent = True
    bill.invoice_id = invoice.id
    db.session.commit()
    
    
    flash(f"Invoice sent: {invoice.id}", "success")
    return redirect(url_for("main.home"))
    

# ___________________________________________________________________________________________
@bp.route("/home")
@login_required
def home():
    # Get all the documents for the current user

    query = current_user.documents.select().order_by(Document.timestamp.desc())
    documents = db.session.scalars(query).all()
    schedule = []
    for document in documents:
        query = (
            sa.select(Schedule)
            .join(Document)  # Join Schedule with Document
            .filter(Document.user_id == current_user.id)  # Filter documents by current_user
            .order_by(Schedule.invoice_date.asc())  # Order by invoice date descending
        )
    schedule = db.session.scalars(query).all()
    token = current_user.token
    
    
    return render_template("main/home.html", title="Home", documents=documents, token=token, schedule=schedule)


@bp.route("/documents", methods=["POST"])
@token_auth.login_required
def upload_document():
    user = token_auth.current_user()

    # Check if the file is included in the request
    file, error = is_file_present(request)
    if error:
        return abort(400,)

    # Validate file extension
    error = validate_file_extension(file)
    if error:
        return abort(400)

    # Save the file safely
    filepath = safely_save_file(file)
    filename = os.path.basename(filepath)

    # Check file size
    max_size_mb = 50
    filesize_in_mb = check_file_size(filepath, max_size_mb)  # Allow up to 50MB
    if not filesize_in_mb:
        return abort(400)
    
    # Read the document
    pdf = PDFClient(filepath)
    pages, images, texts = pdf.extract_text()
    
    # Save document to database
    try: 
        document = Document(user_id=user.id, filename=filename, filepath=filepath, full_text=" ".join(texts))
        db.session.add(document)
        db.session.commit()
        print("langchain")
        schedule = generate_invoice_schedule(document.full_text)
        datetime_fields = ['invoice_date', 'due_date']
        print("correcting datetimes")
        # correct datetime fields
        for item in schedule["invoice_items"]:
            for field in datetime_fields:
                if field in item and item[field] and item[field] != 'null':
                    # Parse the 'MM/DD/YYYY' datetime string to a datetime object
                    dt = datetime.datetime.strptime(item[field], '%m/%d/%Y')
                    # Assume the datetime is in UTC and make it timezone-aware
                    item[field] = dt.replace(tzinfo=timezone.utc)
        print(schedule)
        for bill in schedule["invoice_items"]:
            print(bill)
            print("_"*100)
            s = Schedule(document_id=document.id)
            s.invoice_number =  bill["invoice_number"]
            s.invoice_date =  bill["invoice_date"]
            s.due_date =  bill["due_date"]
            s.product_name =  bill["product_name"]
            s.price =  bill["price"]
            s.customer_name =  bill["customer_name"]
            db.session.add(s)
        db.session.commit()
    
    except Exception as e:
        print(e)
        db.session.rollback()
        return abort(500)
    
    return {
        "document_id": document.id,
        "filename": document.filename,
        "filepath": document.filepath,
    }, 201




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
