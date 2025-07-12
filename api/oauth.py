from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, current_user
from flask import request

from decorators import privacy_accepted_required, terms_accepted_required
from init import db, fernet, limiter

import json

from functions.api_model import APIModel
from functions.api import rate_limit_key

from models.oauth import Oauth
from functions.oauth import Google, Microsoft

# Create OAuth API namespace
oauth_ns = Namespace('link', description='OAuth related operations API')

# Create rate limit for OAuth API
rate_limiter = limiter.shared_limit("300 per minute", key_func=rate_limit_key, scope='api', error_message='Too many requests, please slow down')

# Apply decorators to OAuth API
oauth_ns.decorators = [jwt_required(), privacy_accepted_required, terms_accepted_required, rate_limiter]

# Get OAuth API models
oauth_model, google_oauth_model = APIModel.get_oauth_api_model(oauth_ns)

@oauth_ns.route('/')
class OAuth(Resource):
    
    # Get all the linked OAuth accounts
    @oauth_ns.doc(security='JWT', description='Get all the linked OAuth accounts', responses={200: 'Success', 401: 'Unauthorized'})
    @oauth_ns.marshal_list_with(oauth_model)
    def get(self):
        
        # Check if the user is confirmed
        if not current_user.email_confirmed_at:
            # Return an error message
            return {'message': 'You need to verify your user before doing this action.'}, 401
        
        # Get all the linked OAuth accounts
        oauth_accounts = Oauth.query.filter_by(user_id=current_user.id).all()
        
        # Return the linked OAuth accounts
        return oauth_accounts
    
# OAuth API (/api/link/<int:oauth_id>) - Get, DELETE methods
@oauth_ns.route('/<int:oauth_id>')
class OAuthID(Resource):
    
    # Get OAuth by ID
    @oauth_ns.doc(security='JWT', description='Get OAuth by ID', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
    @oauth_ns.marshal_with(oauth_model)
    def get(self, oauth_id):
        # Get the OAuth by ID
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first()
        
        # Check if the OAuth exists
        if not oauth:
            # Return an error message
            oauth_ns.abort(404, 'OAuth not found.')
        
        # Return the OAuth
        return oauth, 200
    
    # Unlink OAuth by ID
    @oauth_ns.doc(security='JWT', description='Unlink OAuth by ID', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
    def delete(self, oauth_id):
        # Get the OAuth by ID
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first()
        
        # Check if the OAuth exists
        if not oauth:
            # Return an error message
            oauth_ns.abort(404, 'Account not found.')
        
        # Delete the OAuth
        db.session.delete(oauth)
        
        # Commit the changes
        db.session.commit()
        
        # Return a success message
        return {'message': 'Acount unlinked successfully.'}, 200

# OAuth API (/api/link/<string:service>) - POST method
@oauth_ns.route('/<string:service>')
class OAuth(Resource):
    
    # Create OAuth token
    @oauth_ns.doc(security='JWT', description='Create OAuth token', responses={200: 'Success', 401: 'Unauthorized', 400: 'Bad Request'})
    def post(self, service):
        
        # Get the current user
        user = current_user
        
        # Check if the user is confirmed
        if not user.email_confirmed_at:
            # Return an error message
            oauth_ns.abort(401, 'You need to verify your account before linking your Google account.')
        
        # Get the data from the request
        data = request.get_json()
        
        # Check if the service is Google
        if service == 'google':
            # Check if the data is not empty
            if data:
                # Check if the data has the required parameters
                if any([key not in data for key in ['token', 'expiry', 'refresh_token']]):
                    # Return an error message
                    oauth_ns.abort(400, 'Bad request.')

                user_id = user.id # Get the user ID
                service = 'google' # Set the service
                google = Google(data) # Create a new Google object
                profile = google.fetch_user_profile() # Get the user profile
                email = profile['email'] # Get the user email
                first_name = profile['first_name'] # Get the user first name
                last_name = profile['last_name'] # Get the user last name

                # Check if the email is already linked to another account
                oauth = Oauth.query.filter_by(email=email).first()
                
                # Check if the OAuth account exists
                if oauth:
                    # Check if the email is linked to another account
                    if oauth.user_id != user_id:
                        # Return an error message
                        return {'message': 'Email already linked to another account.'}, 400

                    # Update the Google OAuth account
                    oauth.data = fernet.encrypt(str(data).encode()).decode()
                    oauth.first_name = first_name
                    oauth.last_name = last_name
                    # Commit the changes
                    db.session.commit()
                else:
                    # Create a new Google OAuth account
                    new_oauth = Oauth(
                        user_id=user_id, 
                        service=service, 
                        email=email, 
                        first_name=first_name, 
                        last_name=last_name, 
                        data=fernet.encrypt(str(data).encode()).decode()
                        )

                    # Add the new Google OAuth account to the database
                    db.session.add(new_oauth)
                    # Commit the changes
                    db.session.commit()

                # Return a success message
                return {'message': 'Google account linked successfully.'}, 200
            else:
                # Return an error message
                oauth_ns.abort(400, 'Bad request.')
        # Check if the service is Microsoft
        elif service == 'microsoft':
            # Convert the data to JSON
            data = json.loads(data)

            # Check if the data is not empty
            if data:
                # Check if the data has the required parameters
                if any([key not in data for key in ['access_token', 'expires_in', 'refresh_token']]):
                    # Return an error message
                    oauth_ns.abort(400, 'Bad request.')

                user_id = user.id # Get the user ID
                service = 'microsoft' # Set the service
                email = data['id_token_claims']['preferred_username'] # Get the user email
                first_name = data['id_token_claims']['name'].split(' ')[0] # Get the user first name
                last_name = data['id_token_claims']['name'].split(' ')[1] # Get the user last name

                # Check if the email is already linked to another account
                oauth = Oauth.query.filter_by(email=email).first()
                
                # Check if the OAuth account exists
                if oauth:
                    # Check if the email is linked to another account
                    if oauth.user_id != user_id:
                        # Return an error message
                        return {'message': 'Email already linked to another account.'}, 400

                    # Update the Microsoft OAuth account
                    oauth.data = fernet.encrypt(str(data).encode()).decode()
                    oauth.first_name = first_name
                    oauth.last_name = last_name
                    # Commit the changes
                    db.session.commit()
                else:
                    # Create a new Microsoft OAuth account
                    new_oauth = Oauth(user_id=user_id, service=service, email=email, first_name=first_name, last_name=last_name, data=fernet.encrypt(str(data).encode()).decode())

                    # Add the new Microsoft OAuth account to the database
                    db.session.add(new_oauth)
                    # Commit the changes
                    db.session.commit()

                # Return a success message
                return {'message': 'Microsoft account linked successfully.'}, 200
            else:
                # Return an error message
                oauth_ns.abort(400, 'Bad request.')
        else:
            # Return an error message
            oauth_ns.abort(400, 'Service not found.')
        
# OAuth Messages API (/api/link/google/<int:oauth_id>) - GET, POST methods
@oauth_ns.route('/<string:service>/<int:oauth_id>')
class OAuthMessages(Resource):
        
        # Get the messages from the Google account
        @oauth_ns.doc(security='JWT', description='Get the messages from the Google account', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
        def post(self, oauth_id, service):
            # Get the current user
            user = current_user
            
            # Get the data from the request
            data = request.get_json()
            
            # Check if the user is confirmed
            if not user.email_confirmed_at:
                # Return an error message
                return {'message': 'You need to verify your account before linking your Google account.'}, 401
            
            # Get the OAuth account
            oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id, service=service).first()
            
            # Check if the OAuth account exists
            if not oauth:
                # Return an error message
                oauth_ns.abort(404, 'Account not found.')
            
            # Check if the service is Google
            if service == 'google':
                # Get the query, max_results, and next_page_token from the data
                query = data['query'] if 'query' in data else None
                folder_name = data['folder_name'] if 'folder_name' in data else None

                # Set the max_results to 5 if not provided
                max_results = data['max_result'] if 'max_result' in data else 10
                # Set the max_results to 10 if it is greater than 10
                if max_results > 10:
                    max_results = 10

                # Get the next_page_token from the data
                next_page = data['next_page'] if 'next_page' in data else None

                # Decrypt the OAuth data
                oauth_data = fernet.decrypt(oauth.data.encode()).decode()

                # Create a new Google object
                google = Google(json.loads(str(oauth_data).replace("'", '"')))

                # Get the messages
                messages = google.list_messages(query=query, max_results=max_results, next_page=next_page, folder_name=folder_name)

                # Return the messages
                return messages, 200
            # Check if the service is Microsoft
            elif service == 'microsoft':
                # Get the folder_name, query, max_results, and next_page_url from the data
                folder_name = data['folder_name'] if 'folder_name' in data else 'Inbox'
                query = data['query'] if 'query' in data else None
                max_results = data['max_result'] if 'max_result' in data else 10
                next_page = data['next_page'] if 'next_page' in data else None
                
                # Decrypt the OAuth data
                oauth_data = fernet.decrypt(oauth.data.encode()).decode()
                
                # Create a new Microsoft object
                microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
                
                # Get the messages
                messages = microsoft.list_messages(query=query, max_results=max_results, next_page=next_page, folder_name=folder_name)
                
                # Return the messages
                return messages, 200
            else:
                # Return an error message
                oauth_ns.abort(404, 'Service not found.')
            
# OAuth Message API (/api/link/<string:service>/<int:oauth_id>/message/<string:message_id>) - GET method
@oauth_ns.route('/<string:service>/<int:oauth_id>/message/<string:message_id>')
class OAuthMessage(Resource):
        # Get the message from the Google account
        @oauth_ns.doc(security='JWT', description='Get the message from the Google account', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
        def get(self, oauth_id, message_id, service):
            # Get the current user
            user = current_user
            
            # Check if the user is confirmed
            if not user.email_confirmed_at:
                # Return an error message
                return {'message': 'You need to verify your account before linking your Google account.'}, 401
            
            # Get the OAuth account
            oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id).first()
            
            # Check if the OAuth account exists
            if not oauth:
                # Return an error message
                oauth_ns.abort(404, 'Account not found.')
            
            # Decrypt the OAuth data
            oauth_data = fernet.decrypt(oauth.data.encode()).decode()
            
            # Check if the service is Google
            if service == 'google':
                # Create a new Google object
                google = Google(json.loads(str(oauth_data).replace("'", '"')))
            
                # Get the message
                message = google.get_message(message_id)
                
            # Check if the service is Microsoft
            elif service == 'microsoft':
                # Create a new Microsoft object
                microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
                
                # Get the message
                message = microsoft.get_message(message_id)
            else:
                # Return an error message
                oauth_ns.abort(404, 'Service not found.')
            
            # Return the message
            return message, 200
        
# OAuth Folder API (/api/link/<string:service>/<int:oauth_id>/folder) - GET method
@oauth_ns.route('/<string:service>/<int:oauth_id>/folder')
class OAuthFolder(Resource):
    
    # Get the folders
    @oauth_ns.doc(security='JWT', description='Get the folders', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
    def get(self, oauth_id, service):
        # Get the current user
        user = current_user
        
        # Check if the user is confirmed
        if not user.email_confirmed_at:
            # Return an error message
            return {'message': 'You need to verify your account before linking your Google account.'}, 401
        
        # Get the OAuth account
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id).first()
        
        # Check if the OAuth account exists
        if not oauth:
            # Return an error message
            oauth_ns.abort(404, 'Account not found.')
        
        # Decrypt the OAuth data
        oauth_data = fernet.decrypt(oauth.data.encode()).decode()
        
        # Check if the service is Google
        if service == 'google':
            # Create a new Google object
            google = Google(json.loads(str(oauth_data).replace("'", '"')))
        
            # Get the folders
            folders = google.list_folders()
            
        # Check if the service is Microsoft
        elif service == 'microsoft':
            # Create a new Microsoft object
            microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
            
            # Get the folders
            folders = microsoft.list_folders()
        else:
            # Return an error message
            oauth_ns.abort(404, 'Service not found.')
        
        # Return the folders
        return folders, 200
    
# OAuth Single Folder API (/api/link/<string:service>/<int:oauth_id>/folder/<string:folder_name>) - GET method
@oauth_ns.route('/<string:service>/<int:oauth_id>/folder/<string:folder_name>')
class OAuthSingleFolder(Resource):
        
        # Get the messages from the folder
        @oauth_ns.doc(security='JWT', description='Get the messages from the folder', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
        def get(self, oauth_id, folder_name, service):
            # Get the current user
            user = current_user
            
            # Check if the user is confirmed
            if not user.email_confirmed_at:
                # Return an error message
                return {'message': 'You need to verify your account before linking your Google account.'}, 401
            
            # Get the OAuth account
            oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id).first()
            
            # Check if the OAuth account exists
            if not oauth:
                # Return an error message
                oauth_ns.abort(404, 'Account not found.')
            
            # Decrypt the OAuth data
            oauth_data = fernet.decrypt(oauth.data.encode()).decode()
            
            # Check if the service is Google
            if service == 'google':
                # Create a new Google object
                google = Google(json.loads(str(oauth_data).replace("'", '"')))
            
                # Get the messages from the folder
                messages = google.get_folder(folder_name=folder_name)
                
            # Check if the service is Microsoft
            elif service == 'microsoft':
                # Create a new Microsoft object
                microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
                
                # Get the messages from the folder
                messages = microsoft.get_folder(folder_name=folder_name)
            else:
                # Return an error message
                oauth_ns.abort(404, 'Service not found.')
            
            # Return the messages
            return messages, 200
        
# OAuth Message Read/Unread/Delete API (/api/link/<string:service>/<int:oauth_id>/message/<string:message_id>/<string:action>) - POST method
@oauth_ns.route('/<string:service>/<int:oauth_id>/message/<string:message_id>/<string:action>')
class OAuthMessageAction(Resource):
            
            # Update the message status
            @oauth_ns.doc(security='JWT', description='Update the message status', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
            def post(self, oauth_id, message_id, action, service):
                # Get the current user
                user = current_user
                
                # Check if the user is confirmed
                if not user.email_confirmed_at:
                    # Return an error message
                    return {'message': 'You need to verify your account before linking your Google account.'}, 401
                
                # Get the OAuth account
                oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id).first()
                
                # Check if the OAuth account exists
                if not oauth:
                    # Return an error message
                    oauth_ns.abort(404, 'Account not found.')
                    
                # Get the action
                action = action.lower()
                
                # Decrypt the OAuth data
                oauth_data = fernet.decrypt(oauth.data.encode()).decode()
                
                # Check if the service is Google
                if service == 'google':
                    # Create a new Google object
                    google = Google(json.loads(str(oauth_data).replace("'", '"')))
                    
                    if action == 'read':
                        # Mark the message as read
                        update = google.read_message(message_id)
                        
                        # Check if the message was updated
                        if update:
                            # Return a success message
                            return {'message': 'Message marked as read successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                        
                    elif action == 'unread':
                        # Mark the message as unread
                        update = google.unread_message(message_id)
                        
                        # Check if the message was updated
                        if update:
                            # Return a success message
                            return {'message': 'Message marked as unread successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                    elif action == 'delete':
                        # Delete the message
                        update = google.delete_message(message_id)
                        
                        # Check if the message was deleted
                        if update:
                            # Return a success message
                            return {'message': 'Message deleted successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                    
                # Check if the service is Microsoft
                elif service == 'microsoft':
                    # Create a new Microsoft object
                    microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
                    
                    if action == 'read':
                        # Mark the message as read
                        update = microsoft.read_message(message_id)
                        
                        # Check if the message was updated
                        if update:
                            # Return a success message
                            return {'message': 'Message marked as read successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                        
                    elif action == 'unread':
                        # Mark the message as unread
                        update = microsoft.unread_message(message_id)
                        
                        # Check if the message was updated
                        if update:
                            # Return a success message
                            return {'message': 'Message marked as unread successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                    elif action == 'delete':
                        # Delete the message
                        update = microsoft.delete_message(message_id)
                        
                        # Check if the message was deleted
                        if update:
                            # Return a success message
                            return {'message': 'Message deleted successfully.'}, 200
                        else:
                            # Return an error message
                            oauth_ns.abort(404, 'Message not found.')
                else:
                    # Return an error message
                    oauth_ns.abort(404, 'Service not found.')
                    
# OAuth Message Reply API (/api/link/<string:service>/<int:oauth_id>/message/<string:message_id>/reply) - POST method
@oauth_ns.route('/<string:service>/<int:oauth_id>/message/<string:message_id>/reply')
class OAuthMessageReply(Resource):
        
        # Reply to the message
        @oauth_ns.doc(security='JWT', description='Reply to the message', responses={200: 'Success', 401: 'Unauthorized', 404: 'Not Found'})
        def post(self, oauth_id, message_id, service):
            # Get the current user
            user = current_user
            
            # Check if the user is confirmed
            if not user.email_confirmed_at:
                # Return an error message
                return {'message': 'You need to verify your account before replying to an email.'}, 401
            
            # Get the OAuth account
            oauth = Oauth.query.filter_by(id=oauth_id, user_id=user.id).first()
            
            # Check if the OAuth account exists
            if not oauth:
                # Return an error message
                oauth_ns.abort(404, 'Account not found.')
            
            # Decrypt the OAuth data
            oauth_data = fernet.decrypt(oauth.data.encode()).decode()
            
            # Get the data from the request
            data = request.get_json()
            
            # Check if the service is Google
            if service == 'google':
                # Create a new Google object
                google = Google(json.loads(str(oauth_data).replace("'", '"')))
                
                if not 'body' in data or not data['body']:
                    # Return an error message
                    return {'message': 'Body is required.'}, 400
                
                if not 'subject' in data or not data['subject']:
                    # Return an error message
                    return {'message': 'Subject is required.'}, 400
                
                body = data['body'].replace('\n', '<br>')
                to = data['to'] if 'to' in data else None
                cc = data['cc'].split(',') if 'cc' in data else None
                bcc = data['bcc'].split(',') if 'bcc' in data else None
                
                sender = f"{oauth.first_name} {oauth.last_name if oauth.last_name else ''} <{oauth.email}>"
                
                # Reply to the message
                reply = google.reply_email(
                    sender=sender, 
                    message_id=message_id, 
                    reply_message=body,
                    subject=data['subject'],
                    cc=cc, 
                    bcc=bcc
                )
                
                # Return the reply
                if reply:
                    return {
                        'message': 'Email sent successfully.',
                        }, 200
                    
                # Return an error message
                oauth_ns.abort(400, 'Email not sent.')
            # Check if the service is Microsoft
            elif service == 'microsoft':
                # Create a new Microsoft object
                microsoft = Microsoft(json.loads(str(oauth_data).replace("'", '"')))
                
                if not 'body' in data or not data['body']:
                    # Return an error message
                    return {'message': 'Body is required.'}, 400
                
                if not 'subject' in data or not data['subject']:
                    # Return an error message
                    return {'message': 'Subject is required.'}, 400
                
                body = data['body']
                to = data['to'] if 'to' in data else None
                cc = data['cc'].split(',') if 'cc' in data else None
                bcc = data['bcc'].split(',') if 'bcc' in data else None
                
                sender = f"{oauth.first_name} {oauth.last_name if oauth.last_name else ''} <{oauth.email}>"
                
                
                # Reply to the message
                reply = microsoft.reply_email(
                    sender=sender,
                    message_id=message_id,
                    reply_message=body,
                    subject=data['subject'],
                    cc=cc,
                    bcc=bcc
                )
                
                # Return the reply
                if reply:
                    return {
                        'message': 'Email sent successfully.',
                        }, 200
                
                # Return an error message
                oauth_ns.abort(400, 'Email not sent.')
            else:
                # Return an error message
                oauth_ns.abort(404, 'Service not found.')
