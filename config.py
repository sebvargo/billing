import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "some_random_word"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL").replace('postgres://', 'postgresql://') or os.environ.get("HEROKU_POSTGRESQL_IVORY_URL").replace('postgres://', 'postgresql://') or "sqlite:///" + os.path.join(basedir, "app.db")
    MESSAGES_PER_PAGE=5
    ADMINS = [os.environ.get('MAIL_DEFAULT_SENDER')]
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    POSTS_PER_PAGE = 25
    REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("REDISCLOUD_URL") or "redis://"
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(basedir, "uploads")
    # OBJC_DISABLE_INITIALIZE_FORK_SAFETY = os.environ.get("OBJC_DISABLE_INITIALIZE_FORK_SAFETY") or "YES"
    ENV=os.environ.get("ENV") or "DEV"
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET = os.environ.get("S3_BUCKET")
    
    # OpenAI Configuration
    OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
    OPENAI_ORGANIZATION=os.environ.get("OPENAI_ORGANIZATION")
    OPENAI_MODEL_NAME=os.environ.get("OPENAI_MODEL_NAME")
    
    # Application-wide variables
    ALLOWED_EXTENSIONS=['pdf']
    DOCUMENTS_PER_PAGE=os.environ.get("DOCUMENTS_PER_PAGE") or 10
    
