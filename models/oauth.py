from sqlalchemy import func
from init import db

class Oauth(db.Model):
    __tablename__ = 'user_oauth'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())