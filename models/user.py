from sqlalchemy import func
from init import db
from .role import Role, UserRoles

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_code = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(50), nullable=True)
    work_title = db.Column(db.String(50), nullable=True)
    college = db.Column(db.String(50), nullable=True)
    major = db.Column(db.String(50), nullable=True)
    graduation_year = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    email_confirmed_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    terms_accepted_at = db.Column(db.DateTime)
    privacy_accepted_at = db.Column(db.DateTime)
    contacts = db.relationship('Contact', secondary='user_contacts')
    otp = db.relationship('UserOTPs', backref='user', lazy=True)
    chats = db.relationship('Chat', backref='user', lazy=True)
    roles = db.relationship('Role', secondary='user_roles')
    oauth = db.relationship('Oauth', backref='user', lazy=True)
    
    @property
    def roles_info(self):
        user_roles = UserRoles.query.filter_by(user_id=self.id).all()
        roles = []
        for user_role in user_roles:
            role = Role.query.get(user_role.role_id)
            roles.append(UserRolesInfo(role.id, role.name, role.description, user_role.expires_at, user_role.created_at, user_role.updated_at))
        return roles
    
    def has_role(self, role_name):
        for role in self.roles:
            if role.name == role_name:
                return True
        return False
    
    def role_info(self, role_name):
        for role in self.roles_info:
            if role.name == role_name:
                return UserRolesInfo(role.id, role.name, role.description, role.expires_at, role.created_at, role.updated_at)
        return None


class RevokedTokens(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
class UserOTPs(db.Model):
    __tablename__ = 'user_otps'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    otp = db.Column(db.String(6), nullable=False)
    otp_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    expired_at = db.Column(db.DateTime)
    
class UserRolesInfo:
    def __init__(self, id, name, description, expires_at, created_at, updated_at):
        self.id = id
        self.name = name
        self.description = description
        self.expires_at = expires_at
        self.created_at = created_at
        self.updated_at = updated_at