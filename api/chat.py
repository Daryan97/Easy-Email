from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, current_user, verify_jwt_in_request
from flask import request
from decorators import admin_required, privacy_accepted_required, terms_accepted_required
from init import db, fernet, limiter, redis

import json

from models.oauth import Oauth

from functions.api_model import APIModel
from functions.api import rate_limit_key, role_bypass

from functions.chat import ChatAssistant
from models.chat import Chat as ChatModel, ChatMessages

# Create Chat API namespace
chat_ns = Namespace('chat', description='Chat related operations API')

# Create rate limit for Chat API
rate_limiter = limiter.shared_limit("400 per minute", 
                                    key_func=rate_limit_key, 
                                    scope='api', 
                                    error_message='Too many requests, please slow down',
                                    exempt_when=lambda: verify_jwt_in_request(optional=True) and role_bypass('admin')
                                    )

# Apply decorators to Chat API
chat_ns.decorators = [jwt_required(), terms_accepted_required, privacy_accepted_required, rate_limiter]

# Get Chat API models
chat_email_generate_model, chat_email_modify_model, chat_email_send_model, chat_all_model, chat_model, chat_modify_model, chat_message_model = APIModel.get_chat_api_model(chat_ns)

# Chat History API (/api/chat) - GET method
@chat_ns.route('/')
class ChatHistory(Resource):
    
    # Get all the chat history
    @chat_ns.doc(security='JWT', description='Get all the chat history', responses={200: 'Success', 401: 'Unauthorized', 404: 'User not found'}, params={'page': 'The page number', 'per_page': 'The number of items per page'})
    @chat_ns.marshal_list_with(chat_all_model)
    def get(self):
        # Get page and per_page query parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=5, type=int)
        
        # Get the chat history
        chat_history = ChatModel.query.filter_by(user_id=current_user.id).order_by(ChatModel.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        # Return the chat history
        return chat_history, 200
    
# Chat API (/api/chat/<int:chat_id>) - GET, PUT, DELETE methods
@chat_ns.route('/<int:chat_id>')
class Chat(Resource):
    
    # Get chat by ID
    @chat_ns.doc(security='JWT', description='Get chat by ID', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'})
    @chat_ns.marshal_with(chat_model)
    def get(self, chat_id):
        # Get the chat by ID
        chat = ChatModel.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        # Check if chat exists
        if not chat:
            chat_ns.abort(404, 'Chat not found')
        
        # Return the chat
        return chat, 200
    
    # Update chat by ID
    @chat_ns.doc(security='JWT', description='Update chat by ID', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'})
    @chat_ns.expect(chat_model, validate=True)
    @chat_ns.marshal_with(chat_model)
    def put(self, chat_id):
        # Get the form data
        data = request.get_json()
        
        # Get the chat by ID
        chat = ChatModel.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        # Check if chat exists
        if not chat:
            chat_ns.abort(404, 'Chat not found')
        
        # Update the chat
        if 'name' in data and data['name'] and data['name'] != chat.name:
            chat.name = data['name']
        
            db.session.commit()
        
        # Return the chat
        return chat, 200
    
    # Delete chat by ID
    @chat_ns.doc(security='JWT', description='Delete chat by ID', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'})
    def delete(self, chat_id):
        # Get the chat by ID
        chat = ChatModel.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        # Check if chat exists
        if not chat:
            chat_ns.abort(404, 'Chat not found')
        
        chat_messages = ChatMessages.query.filter_by(chat_id=chat_id).all()
        
        # Delete the chat messages
        for chat_message in chat_messages:
            db.session.delete(chat_message)
        
        # Delete the chat
        db.session.delete(chat)
        db.session.commit()
        
        return {'message': 'Chat deleted successfully'}, 200
    
# Chat Messages API (/api/chat/<int:chat_id>/messages) - GET method
@chat_ns.route('/<int:chat_id>/messages')
class Messages(Resource):
        
        # Get chat messages by chat ID
        @chat_ns.doc(security='JWT', description='Get chat messages by chat ID', responses={200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found'})
        @chat_ns.marshal_list_with(chat_message_model)
        def get(self, chat_id):
            # Get the chat by ID
            chat = ChatModel.query.filter_by(id=chat_id, user_id=current_user.id).first()
            
            # Check if chat exists
            if not chat:
                chat_ns.abort(404, 'Chat not found')
            
            # Get the chat messages
            chat_messages = ChatMessages.query.filter_by(chat_id=chat_id).all()
            
            for chat_message in chat_messages:
                try:
                    decrypted_data = fernet.decrypt(chat_message.data).decode()
                    chat_message.data = json.loads(decrypted_data)
                except Exception as e:
                    print(e)
                    chat_ns.abort(400, 'Error decrypting chat message')
            
            # Return the chat messages
            return chat_messages, 200

# Email Generation API (/api/chat/generate) - POST methods
@chat_ns.route('/generate')
class EmailGeneration(Resource):
    
    # Generate an email from Post request
    @chat_ns.expect(chat_email_generate_model, validate=True)
    @chat_ns.doc(security='JWT', description='Generate an email', responses={200: 'Success', 400: 'Missing required fields'})
    def post(self):
        # get the form data
        data = request.get_json()

        # get the contact details
        contacts = data['contacts']
        
        # Get Oauth ID
        oauth_id = data['oauth_id']
        
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first()
        
        if not oauth:
            chat_ns.abort(404, 'Email Authentication not found.')
            
        ai = data['ai'] if 'ai' in data else 'workersai'
                        
        # generate the email
        email_data = ChatAssistant.generate_email(
            contacts=contacts,
            instruction=data['instruction'],
            language_tone=data['language_tone'],
            length=data['length'],
            oauth=oauth,
            ai=ai
        )

        # return the email data
        return email_data
    
    # Modify an email from Put request
    @chat_ns.expect(chat_email_modify_model, validate=True)
    @chat_ns.doc(security='JWT', description='Modify an email', responses={200: 'Success', 400: 'Missing required fields'})
    def put(self):
        # get the form data
        data = request.get_json()

        # get the contact details
        contacts = data['contacts']
        
        ai = data['ai'] if 'ai' in data else 'workersai'
        
        # modify the email
        email_data = ChatAssistant.modify_email(
            contacts=contacts,
            chat_id=data['chat_id'],
            instruction=data['instruction'],
            language_tone=data['language_tone'],
            length=data['length'],
            ai=ai
        )
        
        # return the email data
        return email_data

# Email Send API (/api/chat/send) - POST methods
@chat_ns.route('/send')
class EmailSend(Resource):
    
    # Send an email from Post request
    @chat_ns.expect(chat_email_send_model, validate=True)
    @chat_ns.doc(security='JWT', description='Send an email', responses={200: 'Success', 400: 'Missing required fields', 401: 'Unauthorized', 404: 'User not found'})
    def post(self):
        data = request.get_json()

        # get the contact details
        contacts = data['contacts']
        subject = data['subject']
        body = data['body']
        chat_id = data['chat_id']
        oauth_id = data['oauth_id']
        
        # If any of the fields are missing, return an error
        if not contacts:
            return {'message': 'Contacts are required'}, 400
        
        if not subject:
            return {'message': 'Subject is required'}, 400
        
        if not body:
            return {'message': 'Body is required'}, 400
        
        if not chat_id:
            return {'message': 'Chat ID is required'}, 400
        
        if not oauth_id:
            return {'message': 'Oauth ID is required'}, 400
        
        send = ChatAssistant.send_email(
            contacts=contacts,
            subject=subject,
            body=body,
            chat_id=chat_id,
            oauth_id=oauth_id
        )
        
        if send:
            return {'message': 'Email sent successfully'}, 200
        
        return {'message': 'Email not sent'}, 400
    
# Get Paraphrase API (/api/chat/paraphrase/<int:message_id>) - PUT methods
@chat_ns.route('/paraphrase/<int:message_id>')
class SetParaphrase(Resource):
    
    # Paraphrase a text from Post request
    @chat_ns.doc(security='JWT', description='Paraphrase a text', responses={200: 'Success', 400: 'Missing required fields', 401: 'Unauthorized', 404: 'User not found'})
    def post(self, message_id):
        data = request.get_json()
        
        text = data['text'] if 'text' in data else None
        type = data['type'] if 'type' in data else None
        position = data['position'] if 'position' in data else None
        ai = data['ai'] if 'ai' in data else 'workersai'
               
        if not text:
            return {'message': 'Text is required'}, 400
        
        if not type:
            return {'message': 'Type is required'}, 400
        
        if not position:
            return {'message': 'Position is required'}, 400
        
        fromPosition = position['from'] if 'from' in position else None
        toPosition = position['to'] if 'to' in position else None
        leadingSpace = position['leadingSpace'] if 'leadingSpace' in position else None
        trailingSpace = position['trailingSpace'] if 'trailingSpace' in position else None
        leadingNewline = position['leadingNewline'] if 'leadingNewline' in position else None
        trailingNewline = position['trailingNewline'] if 'trailingNewline' in position else None
        
        if fromPosition == toPosition:
            return {'message': 'From and To positions cannot be the same'}, 400
        
        if fromPosition is None or toPosition is None or leadingSpace is None or trailingSpace is None or leadingNewline is None or trailingNewline is None:
            return {'message': 'Position fields are required'}, 400
        
        message = ChatMessages.query.filter_by(id=message_id, user_id=current_user.id).first()
        
        if not message:
            return {'message': 'Message not found'}, 404
            
        paraphrase = ChatAssistant.paraphrase_text(
            text=text,
            ai=ai
            )
        
        if not paraphrase:
            return {'message': 'Error paraphrasing text'}, 400
        
        response = {
            'original': text,
            'paraphrase': paraphrase,
            'type': type,
            'position': position
        }
        
        redis.setex(f'paraphrase_{message_id}', 60, json.dumps(response))
        # redis.set(f'paraphrase_{message_id}', json.dumps(response))
            
        return response, 200
    
    # Get the paraphrase from message ID
    @chat_ns.doc(security='JWT', description='Get the paraphrase from message ID', responses={200: 'Success', 400: 'Missing required fields', 401: 'Unauthorized', 404: 'User not found'})
    def put(self, message_id):
        paraphrase = redis.get(f'paraphrase_{message_id}')
        
        if not paraphrase:
            return {'message': 'Paraphrase not found'}, 404
        
        paraphrase_data = json.loads(paraphrase)
        
        message = ChatMessages.query.filter_by(id=message_id, user_id=current_user.id).first()
        
        if not message:
            return {'message': 'Message not found'}, 404
        
        try:
            decrypted_data = fernet.decrypt(message.data).decode()
            data = json.loads(decrypted_data)
            
            type = paraphrase_data['type']
            position = paraphrase_data['position']
            fromPosition = position['from']
            toPosition = position['to'] - 1 if position['trailingSpace'] else position['to']
            paraphrase = paraphrase_data['paraphrase']
            
            data[type] = data[type][:fromPosition] + paraphrase + data[type][toPosition:]
            if position['leadingSpace']:
                data[type] = ' ' + data[type]
            if position['trailingSpace']:
                data[type] = data[type] + ' '
            if position['leadingNewline']:
                data[type] = '\n' + data[type]
            if position['trailingNewline']:
                data[type] = data[type] + '\n'
            
            message.data = fernet.encrypt(json.dumps(data).encode()).decode()
            
            db.session.commit()
            redis.delete(f'paraphrase_{message_id}')
            
            return data, 200
        
        except Exception as e:
            print(e)
            return {'message': 'Error setting paraphrase'}, 400
        
# Smart Reply API (/api/chat/reply) - POST methods
@chat_ns.route('/reply')
class SmartReply(Resource):
    
    # Generate a smart reply from Post request
    @chat_ns.doc(security='JWT', description='Generate a smart reply', responses={200: 'Success', 400: 'Missing required fields', 401: 'Unauthorized', 404: 'User not found'})
    def post(self):
        data = request.get_json()
        
        subject = data['subject'] if 'subject' in data else None
        body = data['body'] if 'body' in data else None
        sender = data['sender'] if 'sender' in data else None
        instruction = data['instruction'] if 'instruction' in data else None
        oauth_id = data['oauth_id'] if 'oauth_id' in data else None
        ai = data['ai'] if 'ai' in data else 'workersai'
        
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first()
        
        if not oauth:
            return {'message': 'Email Authentication not found'}, 404
        
        if not subject:
            return {'message': 'Subject is required'}, 400
        
        if not body:
            return {'message': 'Body is required'}, 400
        
        if not instruction:
            return {'message': 'Instructions are required'}, 400
        
        if not sender:
            return {'message': 'Sender is required'}, 400
        
        reply = ChatAssistant.smart_reply(
            subject=subject,
            body=body,
            sender=sender,
            instruction=instruction,
            oauth=oauth,
            ai=ai
            )
        
        response = {
            'reply': reply
        }
        
        if not reply:
            return {'message': 'Error generating smart reply'}, 400
        
        return response, 200
