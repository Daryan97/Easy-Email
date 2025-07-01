from flask_restx import Resource, Namespace
from flask import jsonify, make_response, request
from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies, get_jwt, unset_access_cookies, unset_jwt_cookies, current_user

from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import timedelta, datetime

from decorators import admin_required, privacy_accepted_required, terms_accepted_required
from models.role import Role
from models.user import User, RevokedTokens
from init import db, limiter
from functions.verification import EmailVerification, Password
from functions.email import Email
from functions.api_model import APIModel
from functions.api import rate_limit_key

# Create User API namespace
user_ns = Namespace('user', description='User Account operations API')

# Create rate limiter for User API
rate_limiter = limiter.shared_limit("450 per minute", key_func=rate_limit_key, scope='api', error_message='Too many requests, please slow down')

# set rate limit for User API
user_ns.decorators = [rate_limiter]

# Get User API models
user_model, user_all_model, user_create_model, user_update_model,    user_delete_model, user_auth_model, user_confirm_model, user_email_update_model, user_reset_password_model, user_password_update_model = APIModel.get_user_api_model(user_ns)

# Get Users API (/api/user) - GET methods
@user_ns.route('')
class Users(Resource):    
    # GET method - Get all users
    @user_ns.doc(security='JWT', responses={200: 'Success', 401: 'Unauthorized'},  description='Get all users', params={'page': 'Page number', 'per_page': 'Items per page'})
    @user_ns.marshal_list_with(user_all_model)
    @jwt_required()
    @admin_required
    def get(self):
        # Check if current user is admin
        is_admin = current_user.has_role('admin')

        if not is_admin:
            user_ns.abort(401, 'You are not authorized to view this resource')

        # Get page and per_page query parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=5, type=int)

        # Get users
        users = User.query.paginate(page=page, per_page=per_page)

        return users, 200
    
    # POST method - Create a new user
    @user_ns.expect(user_create_model)
    @user_ns.doc(security=None, responses={201: 'Created', 400: 'Bad Request'}, description='Create a new user')
    def post(self):
        # Get data from request
        data = request.get_json()
            
        email = data["email"] # Get email from request
        username = data["username"] # Get username from request
        password = data["password"] # Get password from request
        first_name = data["first_name"] # Get first name from request
        last_name = data["last_name"] # Get last name from request
        phone_code = data["phone_code"] # Get phone code from request
        phone_number = data["phone_number"] # Get phone number from request
        
        # Validate user data - email (format)
        validate = Email.validate_email(email, True)
        if isinstance(validate, str):
            # Return error message
            user_ns.abort(400, validate)
        
        # Validate user data - email (If email already exists)
        if User.query.filter_by(email=validate.normalized).first():
            user_ns.abort(400, 'Email already in use')
            
        # Validate user data - username (format - letters, numbers, underscores,hyphens)
        if not re.match(r'^[A-Za-z0-9_-]+$', username):
            user_ns.abort(400, 'Username can only contain letters, numbers,underscores, and hyphens')
        
        # Validate user data - username (If username already exists)
        if User.query.filter_by(username=username).first():
            user_ns.abort(400, 'Username already in use')
        
        # Validate user data - password
        validate_password = Password.validate_password(password)
        if not validate_password:
            # Return error message
            user_ns.abort(400, 'Password must be at least 8 characters, contain at least one lowercase letter, one uppercase letter, one number, and one special character')
        
        # Validate user data - first name and last name (letters)
        if not first_name.isalpha() or not last_name.isalpha():
            # Return error message
            user_ns.abort(400, 'First name and last name can only contain letters')
            
        # Validate user data - phone number (format)
        if not re.match(r'\+\d{1,3}', phone_code):
            # Return error message
            user_ns.abort(400, 'Phone code can only contain numbers and +')
        
        # Validate user data - phone number (format)
        if not re.match(r'^\d{5,15}$', phone_number):
            # Return error message
            user_ns.abort(400, 'Phone number can only contain numbers')
        
        # Check if terms and conditions are accepted
        if "terms" not in data:
            # Return error message
            user_ns.abort(400, 'Terms and conditions must be accepted')
        
        # Check if terms and conditions are accepted
        if data["terms"] != True:
            # Return error message
            user_ns.abort(400, 'Terms and conditions must be accepted')
            
        # Check if privacy policy is accepted
        if "privacy" not in data:
            # Return error message
            user_ns.abort(400, 'Privacy policy must be accepted')
        
        # Check if privacy policy is accepted
        if data["privacy"] != True:
            # Return error message
            user_ns.abort(400, 'Privacy policy must be accepted')
        
        # Create new user
        user = User(
            username=data["username"],
            email=validate.normalized,
            password=generate_password_hash(data["password"]),
            phone_code=data["phone_code"],
            phone_number=data["phone_number"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            terms_accepted_at=datetime.now(),
            privacy_accepted_at=datetime.now()
        )
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Generate and send email confirmation OTP
        send_verification = EmailVerification.set_email_otp(user.id)
        
        # Check if email confirmation OTP was not sent
        if not send_verification:
            # Return error message
            user_ns.abort(500, 'Failed to send email confirmation OTP')
            
        # Create access token
        access_token = create_access_token(identity=user, fresh=True)
        
        # Update user last login date, IP, and access token
        user.last_login_ip = request.remote_addr
        user.last_login_at = datetime.now()
        
        # Commit changes to database
        db.session.commit()
        
        # Create response with access token
        response = jsonify(access_token=access_token)
        
        # Set access token in cookies
        set_access_cookies(response, access_token)
        
        # Return response
        return make_response(response, 201)

# User API (/api/user/<int:user_id>) - GET, PUT, DELETE methods
@user_ns.route('/<int:user_id>')
class UserByID(Resource):
    
    # Add JWT required, terms accepted, and privacy accepted decorators to all methods
    method_decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required]
    
    # GET method - Get user by ID
    @user_ns.doc(security='JWT', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'}, description='Get user by ID')
    @user_ns.marshal_with(user_model)
    def get(self, user_id):
        # Check if current user is admin or viewing their own information
        is_admin = current_user.has_role('admin')
        if not is_admin and current_user.id != user_id:
            user_ns.abort(401, 'You are not authorized to view this resource')

        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            user_ns.abort(400, 'Please confirm your email address before viewing this   resource')

        # Get user by ID
        user = current_user if current_user.id == user_id else User.query.filter_by (id=user_id).first()

        # Check if user exists
        if not user:
            user_ns.abort(404, 'User {} not found.'.format(user_id))
            
        # Return user
        return user, 200
    
    # PUT method - Update user by ID
    @user_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Update user by ID')
    @user_ns.expect(user_update_model)
    @user_ns.marshal_with(user_model)
    def put(self, user_id):
        # Check if current user is admin
        is_admin = current_user.has_role('admin')

        # Check if current user is authorized to update user
        if not is_admin and current_user.id != user_id:
            user_ns.abort(401, 'You are not authorized to view this resource')

        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            user_ns.abort(400, 'Please confirm your email address before viewing this resource')

        # Get user by ID
        user = current_user if current_user.id == user_id else User.query.filter_by(id=user_id).first()

        # Check if user exists
        if not user:
            user_ns.abort(404, 'User {} not found.'.format(user_id))

        # Get data from request
        data = request.get_json()

        # Update user data
        # Update username
        if "username" in data:
            username_exists = User.query.filter_by(username=data["username"]).first()
            if username_exists and data["username"] != user.username:
                user_ns.abort(400, 'Username already in use')

            # Validate username (format - letters, numbers, underscores, hyphens)
            if not re.match(r'^[A-Za-z0-9_-]+$', data["username"]):
                user_ns.abort(400, 'Username can only contain letters, numbers, underscores, and hyphens')

            # Check if username is different from current username
            if data["username"] != user.username:
                # Update username
                user.username = data["username"]

        # Update email
        if "email" in data:
            # Validate email (format)
            validate = Email.validate_email(data["email"], False)
            if isinstance(validate, str):
                user_ns.abort(400, validate)
            # Check if email is different from current email
            if validate.normalized != user.email:
                email_exists = User.query.filter_by(email=validate.normalized).first()
                if email_exists:
                    user_ns.abort(400, 'Email already in use')     
                # Update email
                user.email = validate.normalized
                # Generate and send email confirmation OTP
                send_verification = EmailVerification.set_email_otp(user.id)
                # Check if email confirmation OTP was not sent
                if not send_verification:
                    user_ns.abort(500, 'Failed to send email confirmation OTP')

        # Update password
        if "new_password" in data:
            # Validate password (length)
            validate_password = Password.validate_password(data["new_password"])
            if not validate_password:
                user_ns.abort(400, 'Password must be at least 8 characters, contain at least one lowercase letter, one uppercase letter, one number, and one special character')

            if "confirm_password" not in data:
                user_ns.abort(400, 'Confirm password required')

            if data["new_password"] != data["confirm_password"]:
                user_ns.abort(400, 'Passwords do not match')

            # Validate if current password is present
            if "current_password" not in data:
                user_ns.abort(400, 'Current password required')

            # Validate current password
            if not check_password_hash(user.password, data["current_password"]):
                user_ns.abort(400, 'Current password is incorrect')

            # Check if new password is different from current password
            if not check_password_hash(user.password, data["password"]):
                # Update password
                user.password = generate_password_hash(data["password"])

        # Update first name
        if "first_name" in data:
            # Validate first name (letters)
            if not data["first_name"].isalpha():
                user_ns.abort(400, 'First name can only contain letters')

            # Check if first name is different from current first name
            if data["first_name"] != user.first_name:
                # Update first name
                user.first_name = data["first_name"]

        # Update last name
        if "last_name" in data:
            # Validate last name (letters)
            if not data["last_name"].isalpha():
                user_ns.abort(400, 'Last name can only contain letters')

            # Check if last name is different from current last name
            if data["last_name"] != user.last_name:
                # Update last name
                user.last_name = data["last_name"]

        # Update phone number
        if "phone_number" in data:
            # Check if the number is valid
            if not re.match(r'^\d{5,15}$', data["phone_number"]):
                user_ns.abort(400, 'Phone number can only contain numbers')
            
            # Check if the phone number is different from the current phone number
            if data["phone_number"] != user.phone_number:
                # Update phone number
                user.phone_number = data["phone_number"]
                
        # Update phone code
        if "phone_code" in data:
            # Check if the code is valid
            if not re.match(r'\+\d{1,3}', data["phone_code"]):
                user_ns.abort(400, 'Phone code can only contain numbers and +')
            
            # Check if the phone code is different from the current phone code
            if data["phone_code"] != user.phone_code:
                # Update phone code
                user.phone_code = data["phone_code"]

        # Update company
        if "company" in data:
            # Check if company is different from current company
            if data["company"] != user.company:
                # Update company
                user.company = data["company"]

        # Update work title
        if "work_title" in data:
            # Check if work title is different from current work title
            if data["work_title"] != user.work_title:
                # Update work title
                user.work_title = data["work_title"]

        # Update college
        if "college" in data:
            # Check if college is different from current college
            if data["college"] != user.college:
                # Update college
                user.college = data["college"]

        # Update major
        if "major" in data:
            # Check if major is different from current major
            if data["major"] != user.major:
                # Update major
                user.major = data["major"]

        # Update graduation year
        if "graduation_year" in data:
            # Check if graduation year is different from current graduation year
            if data["graduation_year"] != user.graduation_year:
                if re.match(r'^[0-9]{4}$', data["graduation_year"]):
                    # Update graduation year
                    user.graduation_year = data["graduation_year"]
                else:
                    user_ns.abort(400, 'Invalid graduation year')

        if "roles" in data:
            if not is_admin:
                user_ns.abort(401, 'Unauthorized request')

            # User roles
            user_roles = [role.name for role in user.roles]
            if user_roles != data["roles"]:
                # Get roles
                roles = Role.query.filter(Role.name.in_(data["roles"])).all()

                # Update user roles
                user.roles = roles

        # Commit changes to database
        db.session.commit()

        return user, 200
        
    # DELETE method - Delete user by ID
    @user_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Delete user by ID')
    @user_ns.expect(user_delete_model)
    def delete(self, user_id):
        # Check if current user is admin
        is_admin = current_user.has_role('admin')

        # Check if current user is authorized to delete user
        if not is_admin and current_user.id != user_id:
            user_ns.abort(401, 'You are not authorized to view this resource')

        # Get user by ID
        user = current_user if current_user.id == user_id else User.query.filter_by(id=user_id).first()

        # Check if user exists
        if not user:
            user_ns.abort(404, 'User {} not found.'.format(user_id))

        # Check if user is deleting their own account
        if current_user.id == user_id:
            # Get data from request
            data = request.get_json()

            # Check if username is correct
            if data["username"] != user.username:
                user_ns.abort(400, 'Incorrect username')

            # Check if password is correct
            if not check_password_hash(user.password, data["password"]):
                user_ns.abort(400, 'Incorrect password')

        # Delete user
        db.session.delete(user)
        db.session.commit()

        response = jsonify(message='User deleted successfully')
        # Check if user is deleting their own account
        if user_id == current_user.id:
            # Get JTI (JWT ID) from JWT
            jti = get_jwt()["jti"]
            # Create revoked token model
            revoked_token = RevokedTokens(jti=jti)

            # Add revoked token to database
            db.session.add(revoked_token)
            db.session.commit()

            # Unset cookies
            unset_access_cookies(response)
            unset_jwt_cookies(response)

        return make_response(response, 200)
    
    
# UserProfile API (/api/user/profile) - GET, PUT, DELETE methods
@user_ns.route('/profile')
class UserProfile(Resource):
    
    # Add JWT required decorator to all methods
    method_decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required]
    
    # GET method - Get user profile
    @user_ns.doc(security='JWT', responses={200: 'Success', 401: 'Unauthorized'}, description='Get user profile')
    @user_ns.marshal_with(user_model)
    def get(self):
        
        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed:
            user_ns.abort(400, 'Please confirm your email address before viewing this resource')

        return current_user, 200
    
    # PUT method - Update user profile
    @user_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized'}, description='Update user profile')
    @user_ns.expect(user_update_model)
    @user_ns.marshal_with(user_model)
    def put(self):
        
        # Get data from request
        data = request.get_json()
        
        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        
        # Check if email is confirmed unless the user updates their email
        if not is_confirmed and "email" not in data:
            user_ns.abort(400, 'Please confirm your email address before viewing this resource')
        
        # Update username
        if "username" in data:
            username_exists = User.query.filter_by(username=data["username"]).first()
            if username_exists and data["username"] != current_user.username:
                user_ns.abort(400, 'Username already in use')
            
            # Validate username (format - letters, numbers, underscores, hyphens)
            if not re.match(r'^[A-Za-z0-9_-]+$', data["username"]):
                user_ns.abort(400, 'Username can only contain letters, numbers, underscores, and hyphens')
            
            # Check if username is different from current username
            if data["username"] != current_user.username:
                # Update username
                current_user.username = data["username"]
                
        # Update email
        if "email" in data:
            # Validate email (format)
            validate = Email.validate_email(data["email"], False)
            if isinstance(validate, str):
                user_ns.abort(400, validate)
            # Check if email is different from current email
            if validate.normalized != current_user.email:
                # Check if email is valid
                email_exists = User.query.filter_by(email=validate.normalized).first()
                if email_exists:
                    user_ns.abort(400, 'Email already in use')
                    # Update email
                current_user.email = validate.normalized
                # Generate and send email confirmation OTP
                send_verification = EmailVerification.set_email_otp(current_user.id)
                # Check if email confirmation OTP was not sent
                if not send_verification:
                    user_ns.abort(500, 'Failed to send email confirmation OTP')
                    
        # Update password
        if "new_password" in data:
            # Validate password (length)
            validate_password = Password.validate_password(data["new_password"])
            if not validate_password:
                user_ns.abort(400, 'Password must be at least 8 characters, contain at least one lowercase letter, one uppercase letter, one number, and one special character')
            
            if "confirm_password" not in data:
                user_ns.abort(400, 'Confirm password required')
                
            if data["new_password"] != data["confirm_password"]:
                user_ns.abort(400, 'Passwords do not match')
            
            # Validate if current password is present
            if "current_password" not in data:
                user_ns.abort(400, 'Current password required')
            
            # Validate current password
            if not check_password_hash(current_user.password, data["current_password"]):
                user_ns.abort(400, 'Current password is incorrect')
            
            # Check if new password is different from current password
            if not check_password_hash(current_user.password, data["new_password"]):
                # Update password
                current_user.password = generate_password_hash(data["new_password"])
                
        # Update first name
        if "first_name" in data:
            # Validate first name (letters)
            if not data["first_name"].isalpha():
                user_ns.abort(400, 'First name can only contain letters')
            
            # Check if first name is different from current first name
            if data["first_name"] != current_user.first_name:
                # Update first name
                current_user.first_name = data["first_name"]
                
        # Update last name
        if "last_name" in data:
            # Validate last name (letters)
            if not data["last_name"].isalpha():
                user_ns.abort(400, 'Last name can only contain letters')
            
            # Check if last name is different from current last name
            if data["last_name"] != current_user.last_name:
                # Update last name
                current_user.last_name = data["last_name"]
                
        # Update phone number
        if "phone_number" in data:
            # Check if the number is valid
            if not re.match(r'^\d{5,15}$', data["phone_number"]):
                user_ns.abort(400, 'Phone number can only contain numbers')
            
            # Check if the phone number is different from the current phone number
            if data["phone_number"] != current_user.phone_number:
                # Update phone number
                current_user.phone_number = data["phone_number"]
                
        # Update phone code
        if "phone_code" in data:
            # Check if the code is valid
            if not re.match(r'\+\d{1,3}', data["phone_code"]):
                user_ns.abort(400, 'Phone code can only contain numbers and +')
            
            # Check if the phone code is different from the current phone code
            if data["phone_code"] != current_user.phone_code:
                # Update phone code
                current_user.phone_code = data["phone_code"]
                
        # Update company
        if "company" in data:
            # Check if company is different from current company
            if data["company"] != current_user.company:
                # Update company
                current_user.company = data["company"]
                
        # Update work title
        if "work_title" in data:
            # Check if work title is different from current work title
            if data["work_title"] != current_user.work_title:
                # Update work title
                current_user.work_title = data["work_title"]
                
        # Update college
        if "college" in data:
            # Check if college is different from current college
            if data["college"] != current_user.college:
                # Update college
                current_user.college = data["college"]
                
        # Update major
        if "major" in data:
            # Check if major is different from current major
            if data["major"] != current_user.major:
                # Update major
                current_user.major = data["major"]
                
        # Update graduation year
        if "graduation_year" in data:
            # Check if graduation year is different from current graduation year
            if data["graduation_year"] != current_user.graduation_year:
                if re.match(r'^[0-9]{4}$', data["graduation_year"]) or data["graduation_year"] == "":
                    # Update graduation year
                    current_user.graduation_year = data["graduation_year"]
                else:
                    user_ns.abort(400, 'Invalid graduation year')
                    
        # Check if user is admin
        is_admin = current_user.has_role('admin')
                    
        # Update user roles
        if "roles" in data:
            if not is_admin:
                user_ns.abort(401, 'Unauthorized request')
            
            # User roles
            user_roles = [role.name for role in current_user.roles]
            if user_roles != data["roles"]:
                # Get roles
                roles = Role.query.filter(Role.name.in_(data["roles"])).all()
                
                # Update user roles
                current_user.roles = roles
                
        # Commit changes to database
        db.session.commit()
        
        return current_user, 200
    
    # DELETE method - Delete user profile
    @user_ns.doc(security='JWT', responses={200: 'Success', 401: 'Unauthorized'}, description='Delete user profile')
    @user_ns.expect(user_delete_model)
    def delete(self):
        # Get data from request
        data = request.get_json()
        
        # Check if username is correct
        if data["username"] != current_user.username:
            user_ns.abort(400, 'Incorrect username')
        
        # Check if password is correct
        if not check_password_hash(current_user.password, data["password"]):
            user_ns.abort(400, 'Incorrect password')
        
        # Delete user
        db.session.delete(current_user)
        db.session.commit()
        
        response = jsonify(message='User deleted successfully')
        # Get JTI (JWT ID) from JWT
        jti = get_jwt()["jti"]
        # Create revoked token model
        revoked_token = RevokedTokens(jti=jti)
        
        # Add revoked token to database
        db.session.add(revoked_token)
        db.session.commit()
        
        # Unset cookies
        unset_access_cookies(response)
        unset_jwt_cookies(response)
        
        return make_response(response, 200)
    
# User Email API (/api/user/email) - POST method
@user_ns.route('/email')
class UserEmail(Resource):
    
        # Add JWT required decorator to all methods
        method_decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required]
        
        # POST method - Update user email
        @user_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request'}, description='Update user email')
        @user_ns.expect(user_email_update_model)
        def put(self):
            # Get data from request
            data = request.get_json()
            
            # Update email
            if "email" in data:
                # Validate email
                validate = Email.validate_email(data["email"], False)
                if isinstance(validate, str):
                    user_ns.abort(400, validate)
                    
                # Check if email is different from current email
                if validate.normalized != current_user.email:
                    email_exists = User.query.filter_by(email=validate.normalized).first()
                    if email_exists:
                        user_ns.abort(400, 'Email already in use')
                        
                    # Update email
                    current_user.email = validate.normalized
                    # Remove email confirmation date
                    current_user.email_confirmed_at = None
                    # Generate and send email confirmation OTP
                    send_verification = EmailVerification.set_email_otp(current_user.id)
                    # Check if email confirmation OTP was not sent
                    if not send_verification:
                        user_ns.abort(500, 'Failed to send email confirmation OTP')
                else:
                    user_ns.abort(400, 'Email is the same as current email')
                        
            # Commit changes to database
            db.session.commit()
            
            response = jsonify(message='OTP code has been sent to your new email address')
            
            return make_response(response, 200)

# User Auth API (/api/user/auth) - POST, DELETE methods
@user_ns.route('/auth')
class UserAuth(Resource):
    
    method_decorators = [rate_limiter]
    
    # POST method - Authenticate user
    @user_ns.doc(description='Authenticate user', responses={201: 'Created', 400: 'Bad Request', 404: 'Not Found'}, security=None)
    @user_ns.expect(user_auth_model)
    def post(self):
        # Get data from request
        data = request.get_json()

        # Check if the input is username or email
        if "@" in data["username"]:
            # Validate email
            validate = Email.validate_email(data["username"], False)
            if isinstance(validate, str):
                user_ns.abort(400, validate)
            # Get user by email
            user = User.query.filter_by(email=validate.normalized).first()
        else:
            # Get user by username
            user = User.query.filter_by(username=data["username"]).first()

        # Check if user exists
        if not user:
            user_ns.abort(404, 'User not found')

        # Check if user entered correct password
        if not check_password_hash(user.password, data["password"]):
            user_ns.abort(400, 'Incorrect password')

        # Check if user checked remember me (30 days if checked, 1 day if not)
        # (default is set in the create_app function)
        expires_delta = timedelta(days=30) if data['remember'] == True else timedelta(days=1)

        # Create access token
        access_token = create_access_token(identity=user, fresh=True, expires_delta=expires_delta)

        # Update user last login date, IP, and access token
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            user.last_login_ip = request.environ['REMOTE_ADDR']
        else:
            user.last_login_ip = request.environ['HTTP_X_FORWARDED_FOR']
        user.last_login_at = datetime.now()

        # Commit changes to database
        db.session.commit()

        # Create response with access token
        response = jsonify(access_token=access_token)
        
        # Set access token in cookies
        set_access_cookies(response=response, encoded_access_token=access_token)

        return make_response(response, 201)
    
    # DELETE method - Logout user
    @user_ns.doc(description='Logout user', responses={202: 'Accepted', 400: 'Bad Request', 401: 'Unauthorized Request'}, security='JWT')
    @jwt_required()
    def delete(self):
        # Get JTI (JWT ID) from JWT
        jti = get_jwt()["jti"]
        # Create revoked token model
        revoked_token = RevokedTokens(jti=jti)

        # Add revoked token to database
        db.session.add(revoked_token)
        db.session.commit()

        # Create response
        response = jsonify(message="Logged out")

        # Unset cookies
        unset_jwt_cookies(response)
        unset_access_cookies(response)

        return make_response(response, 202)
    
# UserEmail API (/api/user/email) - GET, POST methods
@user_ns.route('/verify')
class UserEmailConfirmation(Resource):
    
    # Add JWT required decorator to all methods
    method_decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required]
    
    # POST method - Confirm user email
    @user_ns.doc(description='Confirm user email using One-time Password', responses={200: 'Success', 400: 'Bad Request'}, security='JWT')
    @user_ns.expect(user_confirm_model)
    def post(self):
        # Check if email is already confirmed
        if current_user.email_confirmed_at is not None:
            user_ns.abort(400, 'Email already confirmed')

        # Get email confirmation OTP from query parameters
        data = request.get_json()

        # Check if OTP is present
        if "otp" not in data:
            user_ns.abort(400, 'OTP is required')

        otp = str(data["otp"])
        # Confirm user email
        verify = EmailVerification.verify_email_otp(current_user.id, otp)
        if not verify:
            user_ns.abort(400, 'OTP is invalid or expired')
            
        # Create response
        response = jsonify(message="Email confirmed successfully")

        return make_response(response, 200)
    
@user_ns.route('/verify/send')
class UserEmailConfirmationSend(Resource):
    
    method_decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required]
    
    # POST method - Send email confirmation email
    @user_ns.doc(description='Send confirm user email OTP', responses={200: 'Success', 400: 'Bad Request'}, security='JWT')
    def post(self):
        # Check if email is already confirmed
        if current_user.email_confirmed_at is not None:
            user_ns.abort(400, 'Email already confirmed')

        send_verification = EmailVerification.set_email_otp(current_user.id)
        if not send_verification:
            user_ns.abort(500, 'Failed to send email confirmation OTP')

        # Create response
        response = jsonify(message="Email confirmation OTP sent")

        return make_response(response, 200)
    
# UserPassword API (/api/user/password) - POST, PUT methods
@user_ns.route('/password')
class UserPassword(Resource):
    
    method_decorators = [rate_limiter]
    
    # Request password reset
    @user_ns.doc(description='Request password reset', responses={200: 'Success', 404: 'Not found', 400: 'Bad Request'}, security=None)
    @user_ns.expect(user_reset_password_model)
    def post(self):
        # Get data from request
        data = request.get_json()
        
        # Check if the input is present
        if not "email" in data:
            user_ns.abort(400, 'Email is required')
        
        # Validate email
        validate = Email.validate_email(data["email"], False)
        if isinstance(validate, str):
            user_ns.abort(400, validate)
            
        # Get user by email
        user = User.query.filter_by(email=validate.normalized).first()
        
        # Check if user exists
        if not user:
            user_ns.abort(404, 'User not found')
            
        # Generate and send password reset OTP
        send_verification = Password.reset_password_otp(user.id)
        if not send_verification:
            user_ns.abort(500, 'Failed to send password reset OTP')
            
        # Create response
        response = jsonify(message="Password reset OTP sent")
        
        return make_response(response, 200)
    
    # Reset password
    @user_ns.doc(description='Reset user password', responses={200: 'Success', 400: 'Bad Request'}, security=None)
    @user_ns.expect(user_password_update_model)
    def put(self):
        # Get data from request
        data = request.get_json()
        
        # Check if the input is present
        if not "email" in data:
            user_ns.abort(400, 'Email is required')
        
        # Validate email
        validate = Email.validate_email(data["email"], False)
        if isinstance(validate, str):
            user_ns.abort(400, validate)
            
        # Get user by email
        user = User.query.filter_by(email=validate.normalized).first()
        
        # Check if user exists
        if not user:
            user_ns.abort(404, 'User not found')
            
        # Check if OTP is present
        if "otp" not in data:
            user_ns.abort(400, 'OTP is required')
        
        # Check if new password is present
        if "new_password" not in data:
            user_ns.abort(400, 'New password is required')
            
        # Validate password (length)
        validate_password = Password.validate_password(data["new_password"])
        if not validate_password:
            user_ns.abort(400, 'Password must be at least 8 characters, contain at least one lowercase letter, one uppercase letter, one number, and one special character')
        
        # Check if confirm password is present
        if "confirm_password" not in data:
            user_ns.abort(400, 'Confirm password is required')
        
        # Check if new password matches confirm password
        if data["new_password"] != data["confirm_password"]:
            user_ns.abort(400, 'Passwords do not match')
            
        # Get password reset OTP
        otp = str(data["otp"])
        
        update_password = Password.reset_password(user.id, otp, data["new_password"])
        if not update_password:
            user_ns.abort(400, 'OTP is invalid or expired')
            
        # Create response
        response = jsonify(message="Password reset successfully")
        
        return make_response(response, 200)