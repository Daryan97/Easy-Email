import base64
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from email.mime.text import MIMEText
import json

import requests

from init import create_logger, env, fernet, db

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .email import Email

import msal

from models.oauth import Oauth

logger = create_logger(__name__)


# Define the Google class
class Google:
    # Google API variables
    SCOPES = env.get('GOOGLE_SCOPES').split(',')
    
    # Google API Initialization
    def __init__(self, credentials):
        self.credentials = credentials
        self.authenticate()
        
    # Define the authenticate method
    def authenticate(self):
        try:
            # Create the credentials object
            self.creds = Credentials.from_authorized_user_info(self.credentials, self.SCOPES)
        except Exception as e:
            # Print the error
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            # Set the credentials to None
            self.creds = None
        
        # Check if the credentials are valid
        if not self.creds or not self.creds.valid:
            # Check if the credentials are expired and refresh them
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    # Refresh the credentials
                    self.creds.refresh(Request())
                    
                    # Update the database with the new credentials
                    creds_json = self.creds.to_json()
                    profile = self.fetch_user_profile()
                    email = profile['email']
                    oauth = Oauth.query.filter_by(email=email).first()
                    if not oauth:
                        return False
                    
                    oauth.data = fernet.encrypt(str(creds_json).encode()).decode()
                    
                    db.session.commit()
                except Exception as e:
                    # Print the error
                    logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
                    # Set the credentials to None
                    self.creds = None
        
        # Check if the credentials are still None
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
        except Exception as e:
            # Print the error
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            # Set the service to None
            self.service = None
        
    # Define the fetch user profile method
    def fetch_user_profile(self):
        try:
            # Create people service
            people_service = build('people', 'v1', credentials=self.creds)
            profile = people_service.people().get(resourceName='people/me', personFields='names,emailAddresses').execute()
            
            # Get the names
            names = profile.get('names', [])
            # Extract the first and last name
            first_name = names[0].get('givenName') if names else None
            last_name = names[0].get('familyName') if names else None
            
            # Get the email addresses
            email_addresses = profile.get('emailAddresses', [])
            
            # Extract the email address
            email = email_addresses[0].get('value') if email_addresses else None
            
            return {'first_name': first_name, 'last_name': last_name, 'email': email}
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to fetch user profile'}
        
    # Define the send_email method
    def send_email(self, sender, to, subject, message, cc=None, bcc=None, attachments=None):
        # Create the message
        msg = MIMEMultipart()
        msg['To'] = ', '.join(to)
        msg['From'] = sender
        msg['Subject'] = subject
        msg['Cc'] = ', '.join(cc) if cc else None
        msg['Bcc'] = ', '.join(bcc) if bcc else None

        # Attach the message body
        msg.attach(MIMEText(message, 'html'))  # 'html' for HTML content, 'plain' for plain text

        # Attach any files
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['data'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={attachment["filename"]}',
                )
                msg.attach(part)

        try:
            # Convert the message to a raw string
            message_bytes = msg.as_bytes()
            raw_message = base64.urlsafe_b64encode(message_bytes).decode('utf-8')

            # Send the email using the Gmail API
            send = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            )
            
            # Execute the send request
            send.execute()

            return True  # Success
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False  # Failure

    # Define the reply_email method
    def reply_email(self, sender, message_id, reply_message, cc=None, bcc=None, attachments=None):
        try:
            # Get the original message using the message ID
            original_message = self.service.users().messages().get(userId='me', id=message_id).execute()
            

            # Extract the necessary fields from the original message
            original_subject = original_message['payload']['headers'][0]['value']
            thread_id = original_message['threadId']
            original_from = next(header for header in original_message['payload']['headers'] if header['name'] == 'From')['value']
            og_msg = self.get_message(message_id)
            original_body = og_msg['body']
            date = og_msg['date']
            

            # Modify the subject to include "Re:"
            subject = f"Re: {original_subject}"
            
            # Create the message
            msg = MIMEMultipart()
            msg['To'] = original_from  # Reply to the sender
            msg['From'] = sender
            msg['Subject'] = subject
            msg['Cc'] = ', '.join(cc) if cc else None
            msg['Bcc'] = ', '.join(bcc) if bcc else None
            
            backslash_n = '\n'

            # Add the reply message
            reply_message_body = f"{reply_message}<hr>{backslash_n}On {date}, {original_from} wrote:{backslash_n}{backslash_n}{original_body}"

            # Attach the message body
            msg.attach(MIMEText(reply_message_body, 'html'))

            # Attach any files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}',
                    )
                    msg.attach(part)

            # Convert the message to a raw string
            message_bytes = msg.as_bytes()
            raw_message = base64.urlsafe_b64encode(message_bytes).decode('utf-8')

            # Send the reply using the Gmail API, ensuring it's part of the same thread
            send = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message, 'threadId': thread_id}  # Specify the threadId
            )
            
            # Execute the send request
            send.execute()

            return True  # Success
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False  # Failure


    
    # Define the list_messages method
    def list_messages(self, query='', next_page=None, max_results=5, folder_name=None):
        try:
            all_messages = []
            
            folder_info = self.get_folder(folder_name.upper() if not folder_name is None else None)
            
            # List the messages
            messages = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_results,
                pageToken=next_page,
                labelIds=[folder_info['id']] if not folder_info is None else []
                ).execute()
            
            total_results = messages.get('resultSizeEstimate', 0)
            
            total_pages = (total_results // max_results) + (1 if total_results % max_results != 0 else 0)
            
            get_messages = messages.get('messages', [])
            for message in get_messages:
                message_id = message['id']
                thread_id = message['threadId']
                message = self.get_message(message_id)
                all_messages.append(
                    {
                    'id': message_id,
                    'thread_id': thread_id,
                    'message': message
                    }
                )
                
            next_page_token = messages.get('nextPageToken', None)    
            
            data = {
                'messages': all_messages,
                'total_results': total_results,
                'total_pages': total_pages,
                'next_page': next_page_token
            }
            
            return data
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to list messages'}
    
    # Define the get_message method
    def get_message(self, message_id):
        try:
            # Get the message
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            
            header = message.get('payload', {}).get('headers', [])
            subject = next((i['value'] for i in header if i['name'] == 'Subject'), None)
            from_email = next((i['value'] for i in header if i['name'] == 'From'), None)
            to_email = next((i['value'] for i in header if i['name'] == 'To'), None)
            date = next((i['value'] for i in header if i['name'] == 'Date'), None)
            cc = next((i['value'] for i in header if i['name'] == 'Cc'), None)
            bcc = next((i['value'] for i in header if i['name'] == 'Bcc'), None)
            attachments = []
            
            labels = message.get('labelIds', [])
            is_read = 'UNREAD' not in labels

            
            # Get the full message body
            parts = message.get('payload', {}).get('parts', [])
            body = ''
            # Get HTML body
            for part in parts:
                mime_type = part.get('mimeType')
                if mime_type == 'text/html':
                    attachment_data = part['body'].get('data')
                    if attachment_data:
                        body = base64.urlsafe_b64decode(attachment_data).decode('utf-8')
                        break  # Prefer HTML, so break if found
                elif mime_type == 'multipart/alternative':
                    for subpart in part.get('parts', []):
                        sub_mime_type = subpart.get('mimeType')
                        if sub_mime_type == 'text/html':
                            attachment_data = subpart['body'].get('data')
                            if attachment_data:
                                body = base64.urlsafe_b64decode(attachment_data).decode('utf-8')
                                break  # Prefer HTML, so break if found
                elif mime_type == 'multipart/mixed':
                    for subpart in part.get('parts', []):
                        sub_mime_type = subpart.get('mimeType')
                        if sub_mime_type == 'text/html':
                            attachment_data = subpart['body'].get('data')
                            if attachment_data:
                                body = base64.urlsafe_b64decode(attachment_data).decode('utf-8')
                                break  # Prefer HTML, so break if found
                        elif sub_mime_type == 'application/pdf':
                            attachment_id = subpart['body']['attachmentId']
                            attachment = self.get_attachment(message_id, attachment_id)
                            attachments.append(attachment)
                elif mime_type == 'application/pdf':
                    attachment_id = part['body']['attachmentId']
                    attachment = self.get_attachment(message_id, attachment_id)
                    attachments.append(attachment)
                elif mime_type == 'text/plain' and not body:
                    attachment_data = part['body'].get('data')
                    if attachment_data:
                        body = base64.urlsafe_b64decode(attachment_data).decode('utf-8')
                elif mime_type == 'multipart/related':
                    for subpart in part.get('parts', []):
                        sub_mime_type = subpart.get('mimeType')
                        if sub_mime_type == 'text/html':
                            attachment_data = subpart['body'].get('data')
                            if attachment_data:
                                body = base64.urlsafe_b64decode(attachment_data).decode('utf-8')
                                break
                        elif sub_mime_type == 'application/pdf':
                            attachment_id = subpart['body']['attachmentId']
                            attachment = self.get_attachment(message_id, attachment_id)
                            attachments += attachment
                            
            attachments = []
            for part in parts:
                if part.get('filename'):
                    content_id = part.get('headers', [{}])[0].get('value')
                    file_name = part['filename']
                    attachment_id = part['body']['attachmentId']
                    mime_type = part['mimeType']
                    size = round(part['body']['size'] / 1024, 2)
                    attachment = {
                        'filename': file_name,
                        'attachment_id': attachment_id,
                        'mime_type': mime_type,
                        'has_content_id': bool(content_id),
                        'size': size
                    }
                    
                    if content_id:
                        for header in part.get('headers', []):
                            if header.get('name') == 'Content-ID':
                                content_id = header.get('value').replace('<', '').replace('>', '')
                                attachment_data = self.get_attachment_base64(message_id, attachment_id)
                                if f'cid:{content_id}' not in body:
                                    attachments.append(attachment)
                                else:
                                    body = body.replace(f'cid:{content_id}', f'data:{mime_type};base64,{attachment_data}')
            
            msg = {
                'subject': subject,
                'from': from_email,
                'to': to_email,
                'cc': cc,
                'bcc': bcc,
                'date': date,
                'body': body,
                'text': Email.extract_text_from_html(body),
                'attachments': attachments,
                'isRead': is_read
            }
            
            return msg
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to get message'}
            
    # Define mark_as_read method
    def read_message(self, message_id):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    # Define mark_as_unread method
    def unread_message(self, message_id):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    # Define delete_message method
    def delete_message(self, message_id):
        try:
            self.service.users().messages().delete(userId='me', id=message_id).execute()
            return True
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
    
    # Define the get_attachment method
    def get_attachment(self, message_id, attachment_id):
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            
            return file_data
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to get attachment'}
    
    def attachment_data(self, message_id, attachment_id):
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            
            return file_data
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return None

    def get_attachment_base64(self, message_id, attachment_id):
        try:
            attachment_data = self.attachment_data(message_id, attachment_id)  # Ensure correct method call
            base64_string = base64.b64encode(attachment_data).decode('utf-8')  # Return the base64 string
            return base64_string
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return None
    
    def list_folders(self):
        try:
            folders = self.service.users().labels().list(userId='me').execute()
            folder_counts = []
            
            for folder in folders.get('labels', []):
                label_id = folder['id']
                
                # Get label details including message count, unread count, and visibility
                label_details = self.service.users().labels().get(userId='me', id=label_id).execute()
                
                # Determine if the label is hidden based on labelListVisibility
                is_hidden = label_details.get('labelListVisibility') == 'labelHide'
                
                # Store folder information with counts and visibility
                folder_info = {
                    'id': label_id,
                    'name': label_details['name'].lower().capitalize(),
                    'messageCount': label_details.get('messagesTotal', 0),
                    'unreadCount': label_details.get('messagesUnread', 0),
                    'isHidden': is_hidden
                }
                folder_counts.append(folder_info)
            
            return folder_counts
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to list folders'}
    
    def get_folder(self, folder_name):
        try:
            folders = self.list_folders()
            
            for folder in folders:
                if folder.get('name').lower() == folder_name.lower():
                    return folder
            return None
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return None
    
    
class Microsoft:
    SCOPES = env.get('MICROSOFT_SCOPES').split(',')
    CLIENT_ID = env.get('MICROSOFT_CLIENT_ID')
    CLIENT_SECRET = env.get('MICROSOFT_CLIENT_SECRET')
    AUTHORITY = env.get('MICROSOFT_AUTHORITY')
    
    def __init__(self, credentials):
        self.credentials = credentials
        self.authenticate()
        
    def authenticate(self):
        self.access_token = self.credentials.get('access_token')
        self.refresh_token = self.credentials.get('refresh_token')
        
        self.app = msal.ConfidentialClientApplication(
            self.CLIENT_ID, authority=self.AUTHORITY,
            client_credential=self.CLIENT_SECRET
        )
        
        code = self.app.acquire_token_by_refresh_token(self.refresh_token, scopes=self.SCOPES)
        
        if 'error' in code:
            return False
        
        email = self.credentials.get('id_token_claims').get('preferred_username')
        
        oauth = Oauth.query.filter_by(email=email).first()
        
        if not oauth:
            return False
        
        oauth.data = fernet.encrypt(str(code).encode()).decode()
        
        db.session.commit()
        
        self.access_token = code['access_token']
        
    def send_email(self, sender, to, subject, body, cc=None, bcc=None, attachments=None):
        # Create the message
        msg = MIMEMultipart()
        msg['To'] = ', '.join(to)
        msg['From'] = sender
        msg['Subject'] = subject
        msg['Cc'] = ', '.join(cc) if cc else None
        msg['Bcc'] = ', '.join(bcc) if bcc else None
        
        # Attach the message body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach any files
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['data'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={attachment["filename"]}',
                )
                msg.attach(part)
                
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML',
                        'content': body
                    },
                    'toRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in to
                    ],
                    'ccRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in cc or []
                    ],
                    'bccRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in bcc or []
                    ],
                    'attachments': []
                }
            }
            
            if attachments:
                for attachment in attachments:
                    data['message']['attachments'].append({
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': attachment['filename'],
                        'contentBytes': base64.b64encode(attachment['data']).decode('utf-8')
                    })
                    
            graph_endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
            
            response = requests.post(graph_endpoint, headers=headers, data=json.dumps(data))
            
            if response.status_code == 202:
                return True
            else:
                return False
        
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    # Define the reply_email method
    def reply_email(self, sender, message_id, reply_message, cc=None, bcc=None, attachments=None):
        try:
            # Get the original message using the message ID
            original_message = self.get_message(message_id)
            
            # Extract the necessary fields from the original message
            original_subject = original_message['subject']
            original_from = original_message['from'].split(', ')
            original_to = original_message['to'].split(', ')
            original_cc = original_message['cc'].split(', ') if original_message['cc'] else None
            original_bcc = original_message['bcc'].split(', ') if original_message['bcc'] else None
            original_body = original_message['body']
            date = original_message['date']
            
            # Modify the subject to include "Re:"
            subject = f"Re: {original_subject}"
            
            # Create the message
            msg = MIMEMultipart()
            msg['To'] = ', '.join(original_from)
            msg['From'] = sender
            msg['Subject'] = subject
            msg['Cc'] = ', '.join(cc) if cc else None
            msg['Bcc'] = ', '.join(bcc) if bcc else None
            
            # Add the reply message
            reply_message_body = f"{reply_message}"
            
            # Attach the message body
            msg.attach(MIMEText(reply_message_body, 'html'))
            
            # Attach any files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}',
                    )
                    msg.attach(part)
                    
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML',
                        'content': reply_message_body
                    },
                    'toRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in original_from
                    ],
                    'ccRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in original_cc or []
                    ],
                    'bccRecipients': [
                        {
                            'emailAddress': {
                                'address': email
                            }
                        } for email in original_bcc or []
                    ],
                    'attachments': []
                }
            }
            
            if attachments:
                for attachment in attachments:
                    data['message']['attachments'].append({
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': attachment['filename'],
                        'contentBytes': base64.b64encode(attachment['data']).decode('utf-8')
                    })
                    
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/reply"
            
            response = requests.post(graph_endpoint, headers=headers, data=json.dumps(data))
            
            if response.status_code == 202:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    def list_messages(self, query='', next_page=None, max_results=5, folder_name=None):
        all_messages = []
        
        folder_info = self.get_folder(folder_name)
        
        if not folder_info:
            return None
        
        folder_id = folder_info.get('id', None)

        graph_endpoint = "https://graph.microsoft.com/v1.0/me/messages" if not folder_name else f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages"

        # Set up headers with the access token
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Handle pagination or first request
        if next_page:
            graph_endpoint = next_page
        else:
            # Properly format query and append to the endpoint
            if query:
                graph_endpoint += f"?$search={requests.utils.quote(query)}&$top={max_results}&$count=true"
            else:
                graph_endpoint += f"?$top={max_results}&$count=true"

        try:
            # Send the request to Microsoft Graph API
            response = requests.get(graph_endpoint, headers=headers)

            if response.status_code == 200:
                messages = response.json()

                total_results = messages.get('@odata.count', 0)
                
                total_pages = (total_results // max_results) + (1 if total_results % max_results != 0 else 0)

                # Process each message
                for message in messages.get('value', []):
                    message_id = message['id']
                    message_content = self.get_message(message_id)
                    all_messages.append(
                        {
                            'id': message_id,
                            'message': message_content
                        }
                    )

                # Return the collected data
                data = {
                    'messages': all_messages,
                    'total_results': total_results,
                    'total_pages': total_pages,
                    'next_page': messages.get('@odata.nextLink', None)
                }

                return data
            else:
                logger.error(f"Failed to retrieve messages: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
    def get_message(self, message_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(graph_endpoint, headers=headers)
            
            # Check if the response status is successful
            if response.status_code == 200:
                message = response.json()
                
                # Check if the message is in the Junk folder or has issues
                if 'folderId' in message and message['folderId'] == 'junk':
                    logger.warning(f"Message with ID {message_id} is in the Junk folder. Some fields may be different.")
                
                subject = message.get('subject', None)
                from_email = message.get('from', {}).get('emailAddress', {}).get('address', None)
                to_email = message.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address', None) if message.get('toRecipients') else None
                date = message.get('receivedDateTime', None)
                cc = ', '.join([i.get('emailAddress', {}).get('address', None) for i in message.get('ccRecipients', [])])
                bcc = ', '.join([i.get('emailAddress', {}).get('address', None) for i in message.get('bccRecipients', [])])
                has_attachments = message.get('hasAttachments', False)
                attachments = []
                body = message.get('body', {}).get('content', None)
                
                is_read = message.get('isRead', False) 
                
                if has_attachments:
                    attachments = self.get_attachments(message_id)
                    
                msg = {
                    'subject': subject,
                    'from': from_email,
                    'to': to_email,
                    'date': date,
                    'cc': cc,
                    'bcc': bcc,
                    'body': body,
                    'text': Email.extract_text_from_html(body),
                    'attachments': attachments,
                    'isRead': is_read
                }
                
                return msg
            else:
                logger.error(f"Failed to fetch message. Status code: {response.status_code}, Response: {response.text}")
                return {'message': 'Failed to get message'}
        
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return {'message': 'Failed to get message'}

    def read_message(self, message_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'isRead': True
            }
            
            response = requests.patch(graph_endpoint, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    def unread_message(self, message_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'isRead': False
            }
            
            response = requests.patch(graph_endpoint, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    def delete_message(self, message_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(graph_endpoint, headers=headers)
            
            if response.status_code == 204:
                return True
            else:
                return False
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
            
    def get_attachments(self, message_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(graph_endpoint, headers=headers)
            
            if response.status_code == 200:
                all_attachments = []
                attachments = response.json()
                
                for attachment in attachments.get('value', []):
                    attachment_id = attachment['id']
                    attachment_name = attachment['name']
                    
                    all_attachments.append(
                        {
                            'id': attachment_id,
                            'filename': attachment_name,
                        }
                    )
                    
                
                return all_attachments
            else:
                return []
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return []
    
    def get_attachment(self, message_id, attachment_id):
        try:
            graph_endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{attachment_id}/$value"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(graph_endpoint, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                return None
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return None
    
    def list_folders(self):
        try:
            folder_endpoint = 'https://graph.microsoft.com/v1.0/me/mailFolders'
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(folder_endpoint, headers=headers)
            
            folder_counts = []
            
            if response.status_code == 200:
                folders = response.json().get('value', [])
                
                for folder in folders:
                    folder_info = {
                        'id': folder.get('id'),
                        'name': folder.get('displayName').lower().capitalize(),
                        'messageCount': folder.get('totalItemCount', 0),
                        'unreadCount': folder.get('unreadItemCount', 0),
                        'isHidden': folder.get('isHidden', False)
                    }
                    folder_counts.append(folder_info)
                    
                return folder_counts
            else:
                return []
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return []

    def get_folder(self, folder_name):
        try:
            folders = self.list_folders()
            
            if folders:
                for folder in folders:
                    if folder.get('name').lower() == folder_name.lower():
                        return folder
            return None
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return None