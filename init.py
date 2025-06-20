from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv
from os import environ as env
from urllib.parse import quote_plus
from datetime import timedelta
from openai import OpenAI
from cryptography.fernet import Fernet
import logging
from redis import Redis
from sqlalchemy import create_engine

from functions.ai import WorkersAI

# Global variables for the application
app = Flask(__name__)
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()
openai = OpenAI()
workersai = WorkersAI()
cors = CORS()
redis = None
limiter = None
fernet = Fernet(env.get('FERNET_KEY'))

# Create a logger for the application
def create_logger(name):
    # Get the global variable for the logger
    global logger
    # Create a logger for the application
    logger = logging.getLogger(name)
    # Set the logging level to DEBUG
    logger.setLevel(logging.DEBUG)
    # Create a file handler for the logger
    error_handler = logging.FileHandler('error.log')
    # Set the logging level for the file handler to ERROR
    error_handler.setLevel(logging.ERROR)
    # Create a formatter for the logger
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Set the formatter for the file handler
    error_handler.setFormatter(formatter)
    # Add the file handler to the logger
    logger.addHandler(error_handler)
    
    return logger

logger = create_logger(__name__)

# initialize the application with the blueprints, database, and other configurations
def create_app():
    # load the environment variables
    load_dotenv()
    
    create_logger(__name__)  # Initialize the logger

    # set the configurations
    app.config['FLASK_APP'] = env.get('FLASK_APP')
    app.config['FLASK_ENV'] = env.get('FLASK_ENV')
    app.config['FLASK_DEBUG'] = bool(env.get('FLASK_DEBUG'))
    app.config['SECRET_KEY'] = env.get('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = env.get('JWT_SECRET_KEY')
    app.config['JWT_COOKIE_SECURE'] = bool(env.get('JWT_COOKIE_SECURE'))
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
    
    # Check if the database is MySQL or PostgreSQL
    database_type = env.get('DATABASE_TYPE')
    
    # check if the database type is MySQL or PostgreSQL
    if database_type == 'mysql':
        # connect to MySQL
        connect_mysql(app)
    elif database_type == 'postgres':
        # connect to PostgreSQL
        connect_postgres(app)
    else:
        # log the error and exit the application
        logger.error('Invalid database type')
        exit(1)
    
    # initialize redis
    redis_host = env.get('REDIS_HOST')
    redis_port = env.get('REDIS_PORT')
    redis_password = env.get('REDIS_PASSWORD')
    redis_db = env.get('REDIS_DB')
    redis_uri = f'redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}' if len(redis_password) > 0 else f'redis://{redis_host}:{redis_port}/{redis_db}'

    # Connect to the Redis server
    global redis
    redis = Redis(host=redis_host, port=redis_port, password=redis_password, db=redis_db)

    # initialize the limiter
    global limiter
    limiter = Limiter(
        key_func=lambda: get_remote_address(),
        app=app,
        storage_uri=redis_uri,
    )

    # set the email configurations
    app.config['MAIL_SERVER'] = env.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = env.get('MAIL_PORT')
    app.config['MAIL_USE_TLS'] = env.get('MAIL_USE_TLS')
    app.config['MAIL_USERNAME'] = env.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = env.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = env.get('MAIL_DEFAULT_SENDER')

    # disable the help message for 404 errors
    app.config['RESTX_ERROR_404_HELP'] = False

    # initialize the database
    db.init_app(app)

    # import models and loaders
    from models.user import User, UserOTPs, RevokedTokens
    from models.role import Role, UserRoles
    from models.contact import Contact, UserContacts
    from models.chat import Chat, ChatMessages
    
    from loader import FlaskErrorLoaders, JWTErrorLoaders, JWTUserCallbacks, TemplateFilters
    
    # initialize JWT and migrate
    jwt.init_app(app)
    migrate.init_app(app, db)

    # initialize the mail
    mail.init_app(app)

    # import and register blueprints
    from api.api import api_bp
    from web.main import main
    
    # register the blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(main, url_prefix='/')

    # create the database
    create_database(app)

    # Get the CORS origins list
    origins_list = env.get('CORS_ORIGINS').split(',')
    cors.init_app(app, resources={r"/api/*": {"origins": origins_list}}, supports_credentials=True)

    # initialize OpenAI
    global openai
    openai.api_key = env.get('OPENAI_API_KEY')
    openai.base_url = env.get('OPENAI_BASE_URL')
    # initialize WorkersAI
    workersai.api_key = env.get('WORKERSAI_API_KEY')
    workersai.base_url = env.get('WORKERSAI_BASE_URL')
    workersai.model = env.get('WORKERSAI_MODEL')
    

    # disable sorting of the JSON response
    app.json.sort_keys = False
    
    # return the application
    return app

# Connect to the MySQL database
def connect_mysql(app):
    # get the environment variables for the MySQL database
    user = quote_plus(env.get("MYSQL_DATABASE_USER"))
    password = quote_plus(env.get("MYSQL_DATABASE_PASSWORD"))
    host = quote_plus(env.get("MYSQL_DATABASE_HOST"))
    port = env.get("MYSQL_DATABASE_PORT")
    database = quote_plus(env.get("MYSQL_DATABASE_DB"))
    # Create the engine for the MySQL database
    engine = create_engine(
        f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        )
    
    # set the configurations for the application
    app.config['SQLALCHEMY_DATABASE_URI'] = engine.url
    app.config['SQLALCHEMY_ENGINE'] = engine
    
# Connect to the PostgreSQL database
def connect_postgres(app):
    # get the environment variables for the PostgreSQL database
    user = quote_plus(env.get("POSTGRES_DATABASE_USER"))
    password = quote_plus(env.get("POSTGRES_DATABASE_PASSWORD"))
    host = quote_plus(env.get("POSTGRES_DATABASE_HOST"))
    port = env.get("POSTGRES_DATABASE_PORT")
    database = quote_plus(env.get("POSTGRES_DATABASE_DB"))
    # Set the database URI
    uri = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
    # Create the engine for the PostgreSQL database
    engine = create_engine(
        uri,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        )
    # set the configurations for the application
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_ENGINE'] = engine

# Create the database
def create_database(app):
    try:
        # create the database
        with app.app_context():
            # create the tables
            db.create_all()
    except Exception as e:
        # log the error and exit the application
        logger.error(e)
        exit(1)