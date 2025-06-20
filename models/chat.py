from sqlalchemy.sql import func
from init import db

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    oauth_id = db.Column(db.Integer, db.ForeignKey('user_oauth.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
class ChatMessages(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chat_type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())