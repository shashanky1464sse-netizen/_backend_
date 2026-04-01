from app.main import create_app
from app.database import db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables created successfully!")
