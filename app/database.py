from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """All SQLAlchemy models will inherit from this Base via Flask-SQLAlchemy."""
    pass

# Initialize Flask-SQLAlchemy with our declarative base
db = SQLAlchemy(model_class=Base)
