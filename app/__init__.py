import os
from config import Config

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()
login = LoginManager()  
login.login_view = 'auth.login' 
login.login_message = 'Please log in to access this page.'
migrate = Migrate()
moment = Moment()

def create_app(config_class=Config):    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # from app.api import bp as api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

from app import models