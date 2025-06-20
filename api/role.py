from flask_restx import Resource, Namespace
from flask import jsonify, make_response, request
from flask_jwt_extended import  jwt_required, current_user

import re

from decorators import admin_required
from models.user import User as User
from models.role import Role
from init import db, limiter
from functions.api_model import APIModel
from functions.api import rate_limit_key

# Create Role API namespace
role_ns = Namespace('role', description='Role related operations API')

# Create rate limit for Role API
rate_limiter = limiter.shared_limit("10 per minute", key_func=rate_limit_key, scope='api', error_message='Too many requests, please slow down')

# Apply decorators to Role API
role_ns.decorators = [jwt_required(), admin_required, rate_limiter]

# Get User API models
role_model, role_all_model, role_create_model, role_update_model, role_delete_model = APIModel.get_role_api_model(role_ns)

# Role API (/api/role) - POST, GET, PUT, DELETE methods
@role_ns.route('')
class UserRoles(Resource):
    
    # POST method - Add user role
    @role_ns.doc(security='JWT', responses={201: 'Created', 400: 'Bad Request', 401: 'Unauthorized'}, description='Create role')
    @role_ns.expect(role_create_model, validate=True)
    @role_ns.marshal_with(role_model)
    def post(self):
        # Check if user is admin
        is_admin = current_user.has_role('admin')

        # Check if user is admin
        if not is_admin:
            role_ns.abort(401, 'Unauthorized request')

        # Get data from request
        data = request.get_json()

        # Check if role name is valid
        if not re.match(r'^[A-Za-z0-9\s]+$', data["name"]):
            role_ns.abort(400, 'Invalid role name')
            

        # Create new role
        new_role = Role(name=data["name"], description=data["description"])

        # Add new role to database
        db.session.add(new_role)

        # Commit changes to database
        db.session.commit()

        # Return new role
        return new_role, 201
    
    @role_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized'}, description='Get roles', params={'page': 'Page number', 'per_page': 'Items per page'})
    @role_ns.marshal_list_with(role_all_model)
    def get(self):
        # Check if user is admin
        is_admin = current_user.has_role('admin')
        
        # Check if user is admin
        if not is_admin:
            role_ns.abort(401, 'Unauthorized request')

        # Get page and per_page query parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=5, type=int)

        # Get roles
        roles = Role.query.paginate(page=page, per_page=per_page)

        # Return roles
        return roles, 200
    
# Role API (/api/role/<int:role_id>) - GET, PUT, DELETE methods
@role_ns.route('/<int:role_id>')
class UserRole(Resource):
        # GET method - Get role by ID
        @role_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Get role by ID')
        @role_ns.marshal_with(role_model)
        def get(self, role_id):
            # Check if user is admin
            is_admin = current_user.has_role('admin')

            # Check if user is admin
            if not is_admin:
                role_ns.abort(401, 'Unauthorized request')

            # Get role by ID
            role = Role.query.filter_by(id=role_id).first()

            # Check if role exists
            if not role:
                # Return error if role not found
                role_ns.abort(404, 'Role not found')

            # Return role
            return role, 200
        
        # PUT method - Update role by ID
        @role_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Update role by ID')
        @role_ns.expect(role_update_model, validate=True)
        @role_ns.marshal_with(role_model)
        def put(self, role_id):
            # Check if user is admin
            is_admin = current_user.has_role('admin')
            
            # Check if user is admin
            if not is_admin:
                # Return error if user is not admin
                role_ns.abort(401, 'Unauthorized request')

            # Get role by ID
            role = Role.query.filter_by(id=role_id).first()

            # Check if role exists
            if not role:
                # Return error if role not found
                role_ns.abort(404, 'Role not found')

            # Get data from request
            data = request.get_json()

            # Update role name
            if "name" in data:
                # Validate role name
                if not re.match(r'^[A-Za-z0-9\s]+$', data["name"]):
                    role_ns.abort(400, 'Invalid role name')

                # Check if role name is different from current role name
                if data["name"] != role.name:
                    # Update role name
                    role.name = data["name"]

                    # Commit changes to database
            
            # Update role description
            if "description" in data:
                role.description = data["description"]
            
            # Commit changes to database
            db.session.commit()

            # Return updated role
            return role, 200
        
        # DELETE method - Delete role by ID
        @role_ns.doc(security='JWT', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'}, description='Delete role by ID')
        def delete(self, role_id):
            # Check if user is admin
            is_admin = current_user.has_role('admin')

            # Check if user is admin
            if not is_admin:
                # Return error if user is not admin
                role_ns.abort(401, 'Unauthorized request')

            # Get role by ID
            role = Role.query.filter_by(id=role_id).first()

            # Check if role exists
            if not role:
                # Return error if role not found
                role_ns.abort(404, 'Role not found')

            # Delete role
            db.session.delete(role)
            db.session.commit()

            # Create response
            response = jsonify(message="Role deleted")

            # Return response
            return make_response(response, 200)