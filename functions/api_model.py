from flask_restx import fields
from .api import DateTime

# Define the data model for the API
class APIModel:
    # Role API model
    def get_role_api_model(api):
        # Role API model
        role_model = api.model('Roles', {
            'id': fields.Integer(description='Role ID', example=1),
            'name': fields.String(description='Role Name', example='admin'),
            'description': fields.String(description='Role Description', example='Administrator'),
            'created_at': DateTime(description='Role Created At', example='Mon, 30 Sep 2024 01:10:35 +0300'),
            'updated_at': DateTime(description='Role Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        role_all_model = api.model('RolesAll', {
            'items': fields.List(fields.Nested(role_model), description='List of Roles'),
            'total': fields.Integer(description='Total Roles', example=1),
            'pages': fields.Integer(description='Total Pages', example=1),
            'page': fields.Integer(description='Current Page', example=1),
            'per_page': fields.Integer(description='Items per Page', example=10),
            'has_prev': fields.Boolean(description='Has Previous Page', example=False),
            'has_next': fields.Boolean(description='Has Next Page', example=False),
        })
    
        role_create_model = api.model('RoleCreate', {
            'name': fields.String(required=True, description='Role Name', example='admin'),
            'description': fields.String(description='Role Description', example='Administrator'),
        })
    
        role_update_model = api.model('RoleUpdate', {
            'name': fields.String(description='Role Name', example='admin'),
            'description': fields.String(description='Role Description', example='Administrator'),
        })
    
        role_delete_model = api.model('RoleDelete', {
            'name': fields.String(required=True, description='Role Name', example='Admin'),
        })
        
        return role_model, role_all_model, role_create_model, role_update_model, role_delete_model
    
    # Contact API model
    def get_contact_api_model(api):
        contact_model = api.model('Contacts', {
            'id': fields.Integer(description='Contact ID', example=1),
            'name': fields.String(description='Contact Name', example='John Doe'),
            'email': fields.String(description='Contact Email', example='email@example.com'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Contact Company', example='Company Inc.'),
            'work_title': fields.String(description='Contact Work Title', example='CEO'),
            'college': fields.String(description='Contact College', example='College University'),
            'major': fields.String(description='Contact Major', example='Computer Science'),
            'created_at': DateTime(description='Contact Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='Contact Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        contact_all_model = api.model('ContactsAll', {
            'items': fields.List(fields.Nested(contact_model), description='List of Contacts'),
            'total': fields.Integer(description='Total Contacts', example=1),
            'pages': fields.Integer(description='Total Pages', example=1),
            'page': fields.Integer(description='Current Page', example=1),
            'per_page': fields.Integer(description='Items per Page', example=10),
            'has_prev': fields.Boolean(description='Has Previous Page', example=False),
            'has_next': fields.Boolean(description='Has Next Page', example=False),
        })
    
        contact_create_model = api.model('ContactCreate', {
            'name': fields.String(required=True, description='Contact Name', example='John Doe'),
            'email': fields.String(required=True, description='Contact Email', example='email@example.com'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Contact Company', example='Company Inc.'),
            'work_title': fields.String(description='Contact Work Title', example='CEO'),
            'college': fields.String(description='Contact College', example='College University'),
            'major': fields.String(description='Contact Major', example='Computer Science'),
        })
    
        contact_update_model = api.model('ContactUpdate', {
            'name': fields.String(description='Contact Name', example='John Doe'),
            'email': fields.String(description='Contact Email', example='email@example.com'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Contact Company', example='Company Inc.'),
            'work_title': fields.String(description='Contact Work Title', example='CEO'),
            'college': fields.String(description='Contact College', example='College University'),
            'major': fields.String(description='Contact Major', example='Computer Science'),
        })
        
        return contact_model, contact_all_model, contact_create_model, contact_update_model
        
    # User API model
    def get_user_api_model(api):
        role_model = api.model('RolesInfo', {
            'id': fields.Integer(description='Role ID', example=1),
            'name': fields.String(description='Role Name', example='admin'),
            'description': fields.String(description='Role Description', example='Administrator'),
            'expires_at': DateTime(description='Role Expires At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'created_at': DateTime(description='Role Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='Role Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        contact_model = api.model('Contacts', {
            'id': fields.Integer(description='Contact ID', example=1),
            'name': fields.String(description='Contact Name', example='John Doe'),
            'email': fields.String(description='Contact Email', example='email@example.com'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Contact Company', example='Company Inc.'),
            'work_title': fields.String(description='Contact Work Title', example='CEO'),
            'college': fields.String(description='Contact College', example='College University'),
            'major': fields.String(description='Contact Major', example='Computer Science'),
            'created_at': DateTime(description='Contact Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='Contact Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        oauth_model = api.model('OAuth', {
            'id': fields.Integer(description='OAuth ID', example=1),
            'email': fields.String(description='OAuth Email', example='email@example.com'),
            'first_name': fields.String(description='OAuth First Name', example='John'),
            'last_name': fields.String(description='OAuth Last Name', example='Doe'),
            'service': fields.String(description='OAuth Service', example='google'),
            'created_at': DateTime(description='OAuth Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='OAuth Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
    
        # User API model
        user_model = api.model('Users', {
            'id': fields.Integer(description='User ID', example=1),
            'username': fields.String(description='Username', example='john_doe'),
            'email': fields.String(description='Email', example='email@example.com'),
            'first_name': fields.String(description='First Name', example='John'),
            'last_name': fields.String(description='Last Name', example='Doe'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Company', example='Company Inc.'),
            'work_title': fields.String(description='Work Title', example='CEO'),
            'college': fields.String(description='College', example='College University'),
            'major': fields.String(description='Major', example='Computer Science'),
            'graduation_year': fields.String(description='Graduation Year', example='2024'),
            'roles_info': fields.Nested(role_model, description='User Roles'),
            'contacts': fields.Nested(contact_model, description='User Contacts'),
            'oauth': fields.Nested(oauth_model, description='User OAuth'),
            'created_at': DateTime(description='Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'email_confirmed_at': DateTime(description='Email Confirmed At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'last_login_at': DateTime(description='Last Login At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'last_login_ip': fields.String(description='Last Login IP', example='127.0.0.1'),
            'is_active': fields.Boolean(description='Is Active', example=True),
            'terms_accepted_at': DateTime(description='Terms Accepted At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'privacy_accepted_at': DateTime(description='Privacy Accepted At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        user_all_model = api.model('UsersAll', {
            'items': fields.List(fields.Nested(user_model), description='List of Users'),
            'total': fields.Integer(description='Total Users', example=1),
            'pages': fields.Integer(description='Total Pages', example=1),
            'page': fields.Integer(description='Current Page', example=1),
            'per_page': fields.Integer(description='Items per Page', example=10),
            'has_prev': fields.Boolean(description='Has Previous Page', example=False),
            'has_next': fields.Boolean(description='Has Next Page', example=False),
        })
    
        user_create_model = api.model('UserCreate', {
            'username': fields.String(required=True, description='Username', example='john_doe'),
            'email': fields.String(required=True, description='Email', example='email@example.com'),
            'password': fields.String(required=True, description='Password', example='@password123'),
            'first_name': fields.String(required=True, description='First Name', example='John'),
            'last_name': fields.String(required=True, description='Last Name', example='Doe'),
            'phone_number': fields.String(required=True, description='Phone Number', example='+1234567890'),
            'terms': fields.Boolean(description='Terms and Conditions', example=True),
        })
    
        user_update_model = api.model('UserUpdate', {
            'username': fields.String(description='Username', example='john_doe'),
            'email': fields.String(description='Email', example='email@example.com'),
            'first_name': fields.String(description='First Name', example='John'),
            'last_name': fields.String(description='Last Name', example='Doe'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Company', example='Company Inc.'),
            'work_title': fields.String(description='Work Title', example='CEO'),
            'college': fields.String(description='College', example='College University'),
            'major': fields.String(description='Major', example='Computer Science'),
            'graduation_year': fields.String(description='Graduation Year', example='2024'),
            'new_password': fields.String(description='New Password', example='@password123'),
            'confirm_password': fields.String(description='Confirm Password', example='@password123'),
            'current_password': fields.String(description='Current Password', example='@password123'),
        })
    
        user_delete_model = api.model('UserDelete', {
            'username': fields.String(required=True, description='Username', example='john_doe'),
            'password': fields.String(required=True, description='Password', example='@password123'),
        })
    
        user_auth_model = api.model('UserAuth', {
            'username': fields.String(required=True, description='Username or Email', example='john_doe'),
            'password': fields.String(required=True, description='Password', example='@password123'),
            'remember': fields.Boolean(description='Remember Me (for 30 days)', example=False),
        })
        
        user_confirm_model = api.model('UserConfirm', {
            'otp': fields.String(required=True, description='One-Time Password', example='123456'),
        })
        
        user_email_update_model = api.model('UserEmailUpdate', {
            'email': fields.String(required=True, description='Email', example='example@email.com'),
        })
        
        user_reset_password_model = api.model('UserResetPassword', {
            'email': fields.String(required=True, description='Email', example='example@email.com'),
        })
        
        user_password_update_model = api.model('UserPasswordUpdate', {
            'otp': fields.String(required=True, description='One-Time Password', example='123456'),
            'new_password': fields.String(required=True, description='New Password', example='@password123'),
            'confirm_password': fields.String(required=True, description='Confirm Password', example='@password123'),
        })
        
        return user_model, user_all_model, user_create_model, user_update_model,    user_delete_model, user_auth_model, user_confirm_model, user_email_update_model, user_reset_password_model, user_password_update_model
    
    # Email API model
    def get_chat_api_model(api):        
        # Contact Email API model
        contact_model = api.model('Contacts', {
            'id': fields.Integer(description='Contact ID', example=1),
            'name': fields.String(description='Contact Name', example='John Doe'),
            'email': fields.String(description='Contact Email', example='email@example.com'),
            'phone_code': fields.String(description='Contact Phone Code', example='+1'),
            'phone_number': fields.String(description='Contact Phone Number', example='1234567890'),
            'company': fields.String(description='Contact Company', example='Company Inc.'),
            'work_title': fields.String(description='Contact Work Title', example='CEO'),
            'college': fields.String(description='Contact College', example='College University'),
            'major': fields.String(description='Contact Major', example='Computer Science'),
        })
        
        chat_contacts_model = api.model('ChatContacts', {
            'to': fields.List(fields.Nested(contact_model), required=True, description='Recipient Contact'),
            'cc': fields.List(fields.Nested(contact_model), description='CC Contact'),
            'bcc': fields.List(fields.Nested(contact_model), description='BCC Contact'),
        })
        
        chat_model = api.model('Chat', {
            'id': fields.Integer(description='Chat ID', example=1),
            'name': fields.String(description='Chat Name', example='Email to Boss'),
            'oauth_id': fields.Integer(description='OAuth ID', example=1),
            'is_sent': fields.Boolean(description='Chat Sent', example=False),
            'created_at': DateTime(description='Chat Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='Chat Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        chat_all_model = api.model('ChatsAll', {
            'items': fields.List(fields.Nested(chat_model), description='List of Chats'),
            'total': fields.Integer(description='Total Chats', example=1),
            'pages': fields.Integer(description='Total Pages', example=1),
            'page': fields.Integer(description='Current Page', example=1),
            'per_page': fields.Integer(description='Items per Page', example=10),
            'has_prev': fields.Boolean(description='Has Previous Page', example=False),
            'has_next': fields.Boolean(description='Has Next Page', example=False),
        })
        
        # Chat Modify API model
        chat_modify_model = api.model('ChatModify', {
            'name': fields.String(required=True, description='Chat Name', example='Email to Boss'),
        })
        
        # Chat messages API model
        chat_message_model = api.model('ChatMessages', {
            'id': fields.Integer(description='Message ID', example=1),
            'chat_id': fields.Integer(description='Chat ID', example=1),
            'data': fields.Raw(description='Message Data', example='{"subject": "Email Subject", "body": "Email Body"}'),
            'chat_type': fields.String(description='Chat Type', example='assistant'),
            'created_at': DateTime(description='Message Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        # Generate Email API model
        chat_email_generate_model = api.model('ChatGenerate', {
            'contacts': fields.List(fields.Nested(chat_contacts_model), required=True, description='Contact'),
            'oauth_id': fields.Integer(required=True, description='Authenticated Email ID', example=1),
            'instruction': fields.String(required=True, description='Email Instruction', example='Write me an email to my boss.'),
            'language_tone': fields.String(required=True, description='Language Tone', example='formal'),
            'length': fields.String(required=True, description='Text Length', example='short'),
            'ai': fields.String(description='AI Model', example='gpt-3'),
        })
        
        # Modify Email API model
        chat_email_modify_model = api.model('ChatModify', {
            'chat_id': fields.Integer(required=True, description='Chat ID', example=1),
            'contacts': fields.List(fields.Nested(chat_contacts_model), required=True, description='Contact'),
            'instruction': fields.String(required=True, description='Email Instruction', example='Refine my email to my boss.'),
            'language_tone': fields.String(required=True, description='Language Tone', example='formal'),
            'length': fields.String(required=True, description='Text Length', example='short'),
            'ai': fields.String(description='AI Model', example='gpt-3'),
        })
        
        chat_email_send_model = api.model('ChatSend', {
            'chat_id': fields.Integer(required=True, description='Chat ID', example=1),
            'contacts': fields.List(fields.Nested(chat_contacts_model), required=True, description='Contact'),
            'subject': fields.String(required=True, description='Email Subject', example='Email Subject'),
            'body': fields.String(required=True, description='Email Body', example='Email Body'),
        })
        
        
        return chat_email_generate_model, chat_email_modify_model, chat_email_send_model, chat_all_model, chat_model, chat_modify_model,chat_message_model
    
    def get_oauth_api_model(api):
        oauth_model = api.model('OAuth', {
            'id': fields.Integer(description='OAuth ID', example=1),
            'email': fields.String(description='OAuth Email', example='john.doe@example.com'),
            'first_name': fields.String(description='OAuth First Name', example='John'),
            'last_name': fields.String(description='OAuth Last Name', example='Doe'),
            'service': fields.String(description='OAuth Service', example='google'),
            'created_at': DateTime(description='OAuth Created At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
            'updated_at': DateTime(description='OAuth Updated At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        google_oauth_model = api.model('GoogleOAuth', {
            'access_token': fields.String(required=True, description='Access Token', example='access_token'),
            'refresh_token': fields.String(required=True, description='Refresh Token', example='refresh_token'),
            'expires_at': DateTime(description='Token Expires At', example='Mon, 30 Sep 2024 01:10:35 -0000'),
        })
        
        return oauth_model, google_oauth_model