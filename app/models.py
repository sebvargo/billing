import os
import sqlalchemy as sa
import sqlalchemy.orm as orm   
import secrets
import tiktoken

from app import db, login
from app.utils import utc_time_now, time_to_utc
from datetime import datetime, timezone, timedelta
from flask import url_for, current_app
from flask_login import UserMixin
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP, JSON, Numeric
from time import time
from typing import List, Optional
from werkzeug.security import generate_password_hash, check_password_hash



OPEN_AI_EMBEDDINGS_MODEL = os.environ.get("OPEN_AI_EMBEDDINGS_MODEL")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME")

# ______________________________________________________________________
# API Mixins
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page,
                                error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

@login.user_loader
def load_user(id: int) -> "User":
    return User.query.get(int(id))

class User(PaginatedAPIMixin, UserMixin, db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    firstname: orm.Mapped[str] = orm.mapped_column(String(64), server_default="Firstname")
    lastname: orm.Mapped[str] = orm.mapped_column(String(64), server_default="Lastname")
    username: orm.Mapped[str] = orm.mapped_column(String(64), index=True, unique=True)
    email: orm.Mapped[str] = orm.mapped_column(String(120), index=True, unique=True)
    password_hash: orm.Mapped[Optional[str]] = orm.mapped_column(String(256))
    about_me: orm.Mapped[Optional[str]] = orm.mapped_column(String(140))
    first_seen: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        default=utc_time_now, type_=TIMESTAMP(timezone=True))
    last_seen: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        default=utc_time_now, type_=TIMESTAMP(timezone=True))
    last_message_read_time: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        type_=TIMESTAMP(timezone=True))
    organization: orm.Mapped[Optional[str]] = orm.mapped_column(
        String(64), default="Acme Corp.")
    token: orm.Mapped[Optional[str]] = orm.mapped_column(String(32), index=True, unique=True)
    token_expiration: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        type_=TIMESTAMP(timezone=True))
    
    # relationships
    documents: orm.WriteOnlyMapped["Document"] = orm.relationship(
        back_populates="user"
    )

    # User profile utilities
    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def fullname(self):
        return f"{self.firstname} {self.lastname}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size=128):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=retro&s={size}"

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def to_utc(self, attribute):
        if attribute == "first_seen":
            return time_to_utc(self.first_seen)
        elif attribute == "last_seen":
            return time_to_utc(self.last_seen)
        elif attribute == "last_message_read_time":
            return time_to_utc(self.last_message_read_time)
        elif attribute == "token_expiration":
            return time_to_utc(self.token_expiration)
        else:
            raise ValueError("Invalid attribute")
        
    def get_token(self, expires_in=3600):
        now = utc_time_now()
        if self.token and self.to_utc('token_expiration') > now + timedelta(seconds=60):
            self.token_expiration = now + timedelta(seconds=expires_in)
            return self.token
        
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token
    
    def revoke_token(self):
        self.token_expiration = utc_time_now() - timedelta(seconds=1)
        
    @staticmethod
    def check_token(token):
        query = sa.select(User).where(User.token == token)
        user = db.session.scalar(query)
        if user is None or user.to_utc('token_expiration') < utc_time_now():
            return None
        # update token expiration
        user.get_token()
        
        return user

    # API utilities
    def to_dict(self, include_email=False):
        data = {
            "id": self.id,
            "username": self.username,
            "last_seen": self.last_seen.replace(tzinfo=timezone.utc).isoformat(),
            "about_me": self.about_me,
            "organization": self.organization,
            "follower_count": self.follower_count(),
            "following_count": self.following_count(),
            "_links": {
                "self": url_for("api.get_user", id=self.id),
                "followers": url_for("api.get_followers", id=self.id),
                "following": url_for("api.get_following", id=self.id),
                "avatar": self.avatar(),
            },
        }
        if include_email:
            data["email"] = self.email
        return data
    
    

# ______________________________________________________________________
# DOCUMENTS MODEL


class Document(PaginatedAPIMixin, db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    user_id: orm.Mapped[int] = orm.mapped_column(ForeignKey(User.id), index=True)
    filename: orm.Mapped[str] = orm.mapped_column(String(128), index=True)
    timestamp: orm.Mapped[datetime] = orm.mapped_column(default=utc_time_now, type_=TIMESTAMP(timezone=True))
    last_modified: orm.Mapped[datetime] = orm.mapped_column(default=utc_time_now, type_=TIMESTAMP(timezone=True), server_default='2024-02-13 11:11:11.391181-07')
    full_text: orm.Mapped[Optional[str]]
    filepath: orm.Mapped[Optional[str]]
    customer: orm.Mapped[Optional[str]] 
    effective_date: orm.Mapped[Optional[datetime]] = orm.mapped_column(type_=TIMESTAMP(timezone=True))
    contract_value: orm.Mapped[Optional[float]]
    frequency: orm.Mapped[Optional[str]]
    price_escalator: orm.Mapped[Optional[float]]  # Assuming percentage form
    payment_terms: orm.Mapped[Optional[str]]
    billing_contact: orm.Mapped[Optional[str]]
    product: orm.Mapped[Optional[str]]
    
    # relationships
    user: orm.Mapped[User] = orm.relationship("User", back_populates="documents")
    schedule: orm.WriteOnlyMapped["Schedule"] = orm.relationship("Schedule", back_populates="document")
    
    
    def __repr__(self) -> str:
        return f"<Document {self.filename}>"
    
    def archive(self):
        self.archived = True
        db.session.commit()
        
    def unarchive(self):
        self.archived = False
        db.session.commit()
        
        
    def count_tokens(self, model=None):
        if not model:
            model = current_app.config["OPENAI_MODEL_NAME"]

        enc = tiktoken.encoding_for_model(model)
        tokens = len(enc.encode(self.full_text))
        if tokens > 0:
            return tokens
        return 0
    
    def to_dict(self):
        data = {
            "id": self.id,
            "filename": self.filename,
            "timestamp": self.timestamp.replace(tzinfo=timezone.utc).isoformat(),
            "num_pages": self.num_pages,
            "last_modified": self.last_modified.replace(tzinfo=timezone.utc).isoformat(),
            "customer": self.customer,
            "effective_date": self.effective_date.replace(tzinfo=timezone.utc).isoformat() if self.effective_date else None,
            "contract_value": str(self.contract_value),  # Convert to string to handle precision
            "frequency": self.frequency,
            "price_escalator": str(self.price_escalator),  # Convert to string for consistency
            "payment_terms": self.payment_terms,
            "billing_contact": self.billing_contact,
            "product": self.product
        }
        return data

class Schedule(PaginatedAPIMixin, db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    document_id: orm.Mapped[int] = orm.mapped_column(ForeignKey(Document.id), index=True)
    customer_name: orm.Mapped[Optional[str]]
    invoice_number: orm.Mapped[Optional[str]] 
    invoice_date: orm.Mapped[Optional[datetime]] = orm.mapped_column(type_=TIMESTAMP(timezone=True))
    due_date: orm.Mapped[Optional[datetime]] = orm.mapped_column(type_=TIMESTAMP(timezone=True))
    product_name: orm.Mapped[Optional[str]]
    price: orm.Mapped[Optional[float]]
    sent: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    invoice_id: orm.Mapped[Optional[str]]

    # relationships
    document: orm.Mapped[Document] = orm.relationship("Document", back_populates="schedule")
    
class Customer(PaginatedAPIMixin, db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    customer_name: orm.Mapped[Optional[str]]
    stripe_id: orm.Mapped[Optional[str]]
