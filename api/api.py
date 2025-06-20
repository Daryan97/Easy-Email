from flask import Blueprint
from flask_restx import Api
from .user import user_ns
from .chat import chat_ns
from .role import role_ns
from .contact import contact_ns
from .oauth import oauth_ns

# Create authorizations
authorizations = {
    'JWT': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

# Create API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Create API
api = Api(
    api_bp, 
    version='1.0', 
    title='Easy-Email API', 
    description='Easy-Email is a platform that helps you to generate emails and send them without any hassle.', 
    doc='/doc', 
    authorizations=authorizations, 
    terms_url='/terms', 
    contact_email='contact@daryandev.com', 
)

# Add namespaces
api.add_namespace(user_ns)
api.add_namespace(role_ns)
api.add_namespace(contact_ns)
api.add_namespace(chat_ns)
api.add_namespace(oauth_ns)