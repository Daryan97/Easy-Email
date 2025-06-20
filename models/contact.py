from sqlalchemy.sql import func
from init import db

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_code = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(50), nullable=True)
    work_title = db.Column(db.String(50), nullable=True)
    college = db.Column(db.String(50), nullable=True)
    major = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
        
class UserContacts(db.Model):
    __tablename__ = 'user_contacts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)