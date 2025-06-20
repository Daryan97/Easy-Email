from flask_restx import Resource, Namespace
from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, current_user

import re

from decorators import privacy_accepted_required, terms_accepted_required
from models.user import User as User
from models.contact import Contact, UserContacts as UserContactsModel
from init import db, limiter
from functions.email import Email
from functions.api_model import APIModel
from functions.api import rate_limit_key

# Contact API namespace
contact_ns = Namespace('contact', description='Contact related operations API')

# Rate limit for contact API
rate_limiter = limiter.shared_limit("25 per minute", key_func=rate_limit_key, scope='api', error_message='Too many requests, please slow down')

# Apply decorators to contact API
contact_ns.decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required, rate_limiter]

# Get contact API models
contact_model, contact_all_model, contact_create_model, contact_update_model = APIModel.get_contact_api_model(contact_ns)

# UserContacts API (/api/contact) - POST method
@contact_ns.route('')
class UserContacts(Resource):
    
    # POST method - Add user contact
    @contact_ns.expect(contact_create_model, validate=True)
    @contact_ns.marshal_with(contact_model)
    @contact_ns.doc(description='Add user contact', responses={201: 'Created', 400: 'Bad Request', 401: 'Unauthorized'}, security='JWT')
    def post(self):
        # Check if current user is admin
        is_admin = current_user.has_role('admin')

        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            contact_ns.abort(400, 'Please confirm your email address before viewing this resource')

        # Get data from request
        data = request.get_json()

        # Check if contact name is valid
        if not re.match(r'^[A-Za-z0-9\s]+$', data["name"]):
            contact_ns.abort(400, 'Invalid contact name')

        # Check if contact email is valid
        validate = Email.validate_email(data["email"], True)
        if isinstance(validate, str):
            contact_ns.abort(400, validate)

        # Check if optional fields are present
        # Check if contact phone is valid
        if "phone_number" in data and "phone_code" in data:
            if not re.match(r'^\d{5,15}$', data["phone_number"]):
                contact_ns.abort(400, 'Phone number can only contain numbers')
            if not re.match(r'\+\d{1,3}', data["phone_code"]):
                contact_ns.abort(400, 'Phone code can only contain numbers and +')

        # Check if contact company is valid
        if "company" in data:
            if not re.match(r'^[A-Za-z0-9\s]+$', data["company"]):
                contact_ns.abort(400, 'Invalid contact company')

        # Check if contact work title is valid
        if "work_title" in data:
            if not re.match(r'^[A-Za-z0-9\s]+$', data["work_title"]):
                contact_ns.abort(400, 'Invalid contact work title')

        # Check if contact college is valid
        if "college" in data:
            if not re.match(r'^[A-Za-z0-9\s]+$', data["college"]):
                contact_ns.abort(400, 'Invalid contact college')

        # Check if contact major is valid
        if "major" in data:
            if not re.match(r'^[A-Za-z0-9\s]+$', data["major"]):
                contact_ns.abort(400, 'Invalid contact major')

        # Create new contact
        new_contact = Contact(
            name=data["name"],
            email=validate.normalized,
            phone_number=data["phone_number"] if "phone_number" in data and "phone_code" in data and data["phone_number"] is not None else None,
            phone_code=data["phone_code"] if "phone_code" in data and "phone_number" in data and data["phone_code"] is not None else None,
            company=data["company"] if "company" in data else None,
            work_title=data["work_title"] if "work_title" in data else None,
            college=data["college"] if "college" in data else None,
            major=data["major"] if "major" in data else None,
        )

        # Add the new contact to current_user.contacts
        current_user.contacts.append(new_contact)

        # Commit changes to database
        db.session.commit()

        return new_contact, 201
    
    @contact_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized'}, description='Get user contacts', params={'page': 'Page number', 'per_page': 'Contacts per page'})
    @contact_ns.marshal_list_with(contact_all_model)
    def get(self):
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Check if user is admin
        is_admin = current_user.has_role('admin')
        
        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            contact_ns.abort(400, 'Please confirm your email address before viewing this resource')

        # Get user contacts
        contacts = Contact.query.join(UserContactsModel, Contact.id == UserContactsModel.contact_id) \
                          .filter(UserContactsModel.user_id == current_user.id) \
                          .order_by(Contact.name) \
                          .paginate(page=page, per_page=per_page, error_out=False)

        return contacts, 200
    
# UserContact API (/api/contact/<int:id>) - GET, PUT, DELETE methods
@contact_ns.route('/<int:id>')
class UserContact(Resource):
    
    # GET method - Get user contact by ID
    @contact_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Get user contact by ID')
    @contact_ns.marshal_with(contact_model)
    def get(self, id):
        # Check if user is admin
        is_admin = current_user.has_role('admin')

        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            contact_ns.abort(400, 'Please confirm your email address before viewing this resource')

        # Get contact by ID
        contact = Contact.query.filter_by(id=id).first()

        # Check if contact exists
        if not contact:
            contact_ns.abort(404, 'Contact not found')

        # Check if contact belongs to user
        if contact not in current_user.contacts and not is_admin:
            contact_ns.abort(401, 'Unauthorized')

        return contact, 200
        
    # PUT method - Update user contact by ID
    @contact_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Update user contact by ID')
    @contact_ns.expect(contact_update_model, validate=True)
    @contact_ns.marshal_with(contact_model)
    def put(self, id):
        # Check if user is admin
        is_admin = current_user.has_role('admin')

        # Check if email is confirmed
        is_confirmed = current_user.email_confirmed_at is not None
        if not is_confirmed and not is_admin:
            contact_ns.abort(400, 'Please confirm your email address before viewing this resource')

        # Get contact by ID
        contact = Contact.query.filter_by(id=id).first()

        # Check if contact exists
        if not contact:
            contact_ns.abort(404, 'Contact {} not found'.format(id))

        # Check if contact belongs to user
        if contact not in current_user.contacts and not is_admin:
            contact_ns.abort(401, 'Unauthorized')

        # Get data from request
        data = request.get_json()

        # Update contact data
        # Update contact name
        if "name" in data:
            # Validate contact name
            if not re.match(r'^[A-Za-z0-9\s]+$', data["name"]):
                contact_ns.abort(400, 'Invalid contact name')

            # Check if contact name is different from current contact name
            if data["name"] != contact.name:
                # Update contact name
                contact.name = data["name"]

        # Update contact email
        if "email" in data:
            # Validate contact email
            validate = Email.validate_email(data["email"], True)
            if isinstance(validate, str):
                contact_ns.abort(400, validate)

            # Check if contact email is different from current contact email
            if validate.normalized != contact.email:
                # Update contact email
                contact.email = validate.normalized

        # Update contact phone
        if "phone_number" in data and "phone_code" in data:
            # Validate contact phone number
            if not re.match(r'^\d{5,15}$', data["phone_number"]) and not data["phone_number"] == "":
                contact_ns.abort(400, 'Phone number can only contain numbers')
                
            # Validate contact phone code
            if not re.match(r'\+\d{1,3}', data["phone_code"]) and not data["phone_code"] == "":
                contact_ns.abort(400, 'Phone code can only contain numbers and +')

            # Check if contact phone is different from current contact phone
            if data["phone_number"] != contact.phone_number:
                # Update contact phone number
                contact.phone_number = data["phone_number"]
            
            # Check if contact phone code is different from current contact phone code
            if data["phone_code"] != contact.phone_code:
                # Update contact phone code
                contact.phone_code = data["phone_code"]
                
            # Set phone number and phone code to None if both are empty
            if data["phone_number"] == "" or data["phone_code"] == "":
                contact.phone_number = None
                contact.phone_code = None

        # Update contact company
        if "company" in data:
            # Validate contact company
            if not re.match(r'^[A-Za-z0-9\s]+$', data["company"]) and not data["company"] == "":
                contact_ns.abort(400, 'Invalid contact company')

            # Check if contact company is different from current contact company
            if data["company"] != contact.company:
                # Update contact company
                contact.company = data["company"]

        # Update contact work title
        if "work_title" in data:
            # Validate contact work title
            if not re.match(r'^[A-Za-z0-9\s]+$', data["work_title"]) and not data["work_title"] == "":
                contact_ns.abort(400, 'Invalid contact work title')

            # Check if contact work title is different from current contact work title
            if data["work_title"] != contact.work_title:
                # Update contact work title
                contact.work_title = data["work_title"]

        # Update contact college
        if "college" in data:
            # Validate contact college
            if not re.match(r'^[A-Za-z0-9\s]+$', data["college"]) and not data["college"] == "":
                contact_ns.abort(400, 'Invalid contact college')

            # Check if contact college is different from current contact college
            if data["college"] != contact.college:
                # Update contact college
                contact.college = data["college"]

        # Update contact major
        if "major" in data:
            # Validate contact major
            if not re.match(r'^[A-Za-z0-9\s]+$', data["major"]) and not data["major"] == "":
                contact_ns.abort(400, 'Invalid contact major')

            # Check if contact major is different from current contact major
            if data["major"] != contact.major:
                # Update contact major
                contact.major = data["major"]

        # Commit changes to database
        db.session.commit()

        return contact, 200
    
    # DELETE method - Delete user contact by ID
    @contact_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Delete user contact by ID')
    def delete(self, id):
        # Check if user is admin
        is_admin = current_user.has_role('admin')

        # Get contact by ID
        contact = Contact.query.filter_by(id=id).first()

        # Check if contact exists
        if not contact:
            contact_ns.abort(404, 'Contact {} not found'.format(id))

        # Check if contact belongs to user
        if contact not in current_user.contacts and not is_admin:
            contact_ns.abort(401, 'Unauthorized')

        # Delete corresponding records in user_contacts table
        user_contact = UserContactsModel.query.filter_by(user_id=current_user.id, contact_id=contact.id).first()
        if user_contact:
            db.session.delete(user_contact)
            db.session.commit()

        # Delete contact
        db.session.delete(contact)
        db.session.commit()

        # Create response
        response = jsonify(message="Contact deleted")
        # Return response
        return make_response(response, 200)