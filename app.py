import os
import logging
import sqlalchemy
import sqlalchemy.pool
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///toefl_practice.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 15,
    "max_overflow": 5,
    "pool_timeout": 5,
    "connect_args": {
        "options": "-c statement_timeout=5000"
    }
}

# Initialize the app with the extension
db.init_app(app)

# Import routes after app creation to avoid circular imports
from routes import *

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Temporarily disable background task manager to restore responsiveness
    # TODO: Re-enable after fixing database contention
    # try:
    #     from services.background_task_manager import get_task_manager
    #     task_manager = get_task_manager()
    #     logging.info("Background task manager initialized")
    # except Exception as e:
    #     logging.error(f"Failed to initialize background task manager: {e}")
    logging.info("Background task manager temporarily disabled")
