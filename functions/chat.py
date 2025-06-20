import re
from functions.oauth import Google, Microsoft
from init import openai, workersai, db, fernet, create_logger
from flask import jsonify, make_response, render_template
from flask_jwt_extended import current_user
from flask_restx import abort
from datetime import datetime
from models.chat import Chat, ChatMessages
from models.contact import Contact
from functions.email import Email

import json

from models.oauth import Oauth

logger = create_logger(__name__)

backslash_n = "\n"
model = "pai-001"
temperature = 0.6
max_tokens = 200

max_history = 5

today_date_time = datetime.now().strftime("%A, %d %B %Y")

system_prompt = f"""You are an email generator AI. Your task is to generate an email based on the provided sender, recipient details, instruction, tone, and length. Output only the email content without any explanations or meta-comments.

Output format:
Subject: [subject]
Body: [body]

Ensure:
- The email is concise and follows the given instruction.
- No placeholders (e.g., "[your name]") are included.
- If the user requests edits, apply only the specified changes without altering the rest of the email.

Today's date is {today_date_time}."""

class ChatAssistant:
    # Format the contact details
    def format_contact(contacts, type="To"):
        contact_number = 1
        contacts_len = len(contacts)
        contact_list = ""
        contact_list += f"{type}: {backslash_n}"
        if contacts_len == 0:
            return None
        for contact in contacts:
            contact_list += f"Contact {contact_number}:{backslash_n}"
            contact_list += f"{'Name: ' + contact['name'] + (backslash_n) if contact.get('name') else ''}"
            contact_list += f"Email: {contact['email']}{backslash_n}"
            contact_list += f"{'Company: ' + contact['company'] + ' - ' + (contact['work_title'] or '') + (backslash_n) if contact.get('company') else ''}"
            contact_list += f"{'College: ' + contact['college'] + ' - ' + contact['major'] + (backslash_n) if contact.get('college') else ''}"
            contact_list += f"{'Phone: ' + contact['phone_code'] + contact['phone_number'] if contact.get('phone_number') and contact.get('phone_code') else ''}"
            if contact_number < contacts_len:
                contact_list += f"{backslash_n}"
            contact_number += 1
        
        return contact_list

    # Seperate the contacts into to, cc, and bcc
    def seperate_contacts(contacts):
        # create a list of contacts
        contact_to = []
        contact_cc = []
        contact_bcc = []
        # iterate through the contacts
        for contact_type in contacts:
            if 'to' in contact_type:
                for contact in contact_type['to']:
                    if 'id' in contact:
                        contact_id = contact['id']
                        # get the contact details
                        contact = Contact.query.filter_by(id=contact_id).first()
                        
                        if contact_id not in [c.id for c in current_user.contacts]:
                            abort(400, 'Contact {} not found'.format(contact_id))

                        contact_name = contact.name
                        contact_email = contact.email
                        contact_company = contact.company if contact.company else None
                        contact_work_title = contact.work_title if contact.work_title else None
                        contact_college = contact.college if contact.college else None
                        contact_major = contact.major if contact.major else None
                        contact_phone_code = contact.phone_code if contact.phone_code else None
                        contact_phone_number = contact.phone_number if contact.phone_number else None
                    elif 'email' in contact:
                        contact_name = contact['name'] if 'name' in contact else None
                        contact_email = contact['email']
                        contact_company = contact['company'] if 'company' in contact else None
                        contact_work_title = contact['work_title'] if 'work_title' in contact else None
                        contact_college = contact['college'] if 'college' in contact else None
                        contact_major = contact['major'] if 'major' in contact else None
                        contact_phone_code = contact['phone_code'] if 'phone_code' in contact else None
                        contact_phone_number = contact['phone_number'] if 'phone_number' in contact else None
                    else:
                        abort(400, 'You must provide either contact IDs or emails')
                    
                    contact_to.append({
                        'name': contact_name,
                        'email': contact_email,
                        'company': contact_company,
                        'work_title': contact_work_title,
                        'college': contact_college,
                        'major': contact_major,
                        'phone_code': contact_phone_code,
                        'phone_number': contact_phone_number
                    })
            if 'cc' in contact_type:
                for contact in contact_type['cc']:
                    if 'id' in contact:
                        contact_id = contact['id']
                        # get the contact details
                        contact = Contact.query.filter_by(id=contact_id).first()

                        if contact_id not in [c.id for c in current_user.contacts]:
                            abort(400, 'Contact {} not found'.format(contact_id))

                        contact_name = contact.name
                        contact_email = contact.email
                        contact_company = contact.company if contact.company else None
                        contact_work_title = contact.work_title if contact.work_title else None
                        contact_college = contact.college if contact.college else None
                        contact_major = contact.major if contact.major else None
                        contact_phone_code = contact.phone_code if contact.phone_code else None
                        contact_phone_number = contact.phone_number if contact.phone_number else None
                    elif 'email' in contact:
                        contact_name = contact['name'] if 'name' in contact else None
                        contact_email = contact['email']
                        contact_company = contact['company'] if 'company' in contact else None
                        contact_work_title = contact['work_title'] if 'work_title' in contact else None
                        contact_college = contact['college'] if 'college' in contact else None
                        contact_major = contact['major'] if 'major' in contact else None
                        contact_phone_code = contact['phone_code'] if 'phone_code' in contact else None
                        contact_phone_number = contact['phone_number'] if 'phone_number' in contact else None
                    else:
                        abort(400, 'You must provide either contact IDs or emails')

                    contact_cc.append({
                        'name': contact_name,
                        'email': contact_email,
                        'company': contact_company,
                        'work_title': contact_work_title,
                        'college': contact_college,
                        'major': contact_major,
                        'phone_code': contact_phone_code,
                        'phone_number': contact_phone_number
                    })
            if 'bcc' in contact_type:
                for contact in contact_type['bcc']:
                    if 'id' in contact:
                        contact_id = contact['id']
                        # get the contact details
                        contact = Contact.query.filter_by(id=contact_id).first()
    
                        if contact_id not in [c.id for c in current_user.contacts]:
                            abort(400, 'Contact {} not found'.format(contact_id))
    
                        contact_name = contact.name
                        contact_email = contact.email
                        contact_company = contact.company if contact.company else None
                        contact_work_title = contact.work_title if contact.work_title else None
                        contact_college = contact.college if contact.college else None
                        contact_major = contact.major if contact.major else None
                        contact_phone_code = contact.phone_code if contact.phone_code else None
                        contact_phone_number = contact.phone_number if contact.phone_number else None
                    elif 'email' in contact:
                        contact_name = contact['name'] if 'name' in contact else None
                        contact_email = contact['email']
                        contact_company = contact['company'] if 'company' in contact else None
                        contact_work_title = contact['work_title'] if 'work_title' in contact else None
                        contact_college = contact['college'] if 'college' in contact else None
                        contact_major = contact['major'] if 'major' in contact else None
                        contact_phone_code = contact['phone_code'] if 'phone_code' in contact else None
                        contact_phone_number = contact['phone_number'] if 'phone_number' in contact else None
                    else:
                        abort(400, 'You must provide either contact IDs or emails')
                        
                    contact_bcc.append({
                        'name': contact_name,
                        'email': contact_email,
                        'company': contact_company,
                        'work_title': contact_work_title,
                        'college': contact_college,
                        'major': contact_major,
                        'phone_code': contact_phone_code,
                        'phone_number': contact_phone_number
                    })
                    
        return contact_to, contact_cc, contact_bcc
    
    # Get the chat history
    def get_chat_history(chat_id):
        chat = Chat.query.filter_by(id=chat_id).first()
        
        if not chat:
            abort(404, 'Chat not found')
        
        chat_history = ChatMessages.query.filter_by(chat_id=chat_id).order_by(ChatMessages.id.desc()).limit(max_history).all()
        
        db.session.close()
        
        for message in chat_history:
            try:
                message.data = fernet.decrypt(message.data.encode()).decode()
                message.data = json.loads(message.data)
            except Exception as e:
                abort(400, 'Error decrypting chat messages')
            
        chat_data = []
        for message in chat_history:
            if message.chat_type == "assistant":
                chat_data.append({
                    "role": "assistant",
                    "content": (
                    f"Subject: {message.data['subject']}{backslash_n}"
                    f"Body: {message.data['body']}{backslash_n}"
                    )
                })
            else:
                contact_to, contact_cc, contact_bcc = ChatAssistant.seperate_contacts(message.data['contacts'])
                chat_data.append({
                    "role": "user",
                    "content": (
                    f"To: {ChatAssistant.format_contact(contact_to)}{backslash_n}"
                    f"CC: {ChatAssistant.format_contact(contact_cc)}{backslash_n}"
                    f"BCC: {ChatAssistant.format_contact(contact_bcc)}{backslash_n}"
                    f"Instruction: {message.data['instruction']}{backslash_n}"
                    f"Language Tone: {message.data['language_tone']}{backslash_n}"
                    f"Length: {message.data['length']}{backslash_n}"
                    )
                })

        return chat_data
    
    # Create a chat
    def create_chat(oauth):
        user = current_user
        chat = Chat(
            user_id = user.id,
            name = "New Chat",
            oauth_id = oauth.id
        )
        
        db.session.add(chat)
        db.session.commit()
        
        
        return chat
    
    # Generate an email
    def generate_email(contacts, instruction, language_tone, length, oauth, ai="openai"):
        user = current_user
        
        chat = ChatAssistant.create_chat(oauth)
        
        chat_id = chat.id
        
        contact_to, contact_cc, contact_bcc = ChatAssistant.seperate_contacts(contacts)
        
        email_length = f"Short (50-125 words)" if length == "short" else f"Medium (125-250 words)" if length == "medium" else f"Long (250-500 words)" if length == "long" else f"Extra Long (500+ words)" if length == "extra_long" else "Unknown"
        
        input_data = {
            "contacts": contacts,
            "instruction": instruction,
            "language_tone": language_tone,
            "length": email_length
        }
        
        email_to = ChatAssistant.format_contact(contact_to, "To")
        email_cc = ChatAssistant.format_contact(contact_cc, "Cc") if contact_cc else None
        email_bcc = ChatAssistant.format_contact(contact_bcc, "Bcc") if contact_bcc else None
        
        email_instruction = f"Instruction: {instruction}"
        email_language_tone = f"Language Tone: {language_tone}"
        email_length = f"Email Length: {email_length}"
        
        email_sender = f"""Full Name: {oauth.first_name} {oauth.last_name or ""}
Email: {oauth.email}
{f"Phone: {user.phone_code} {user.phone_number}" if user.phone_code and user.phone_number else ""}
{f"Company: {user.company}, {user.work_title}" if user.company and user.work_title else ""}
{f"College: {user.college}, {user.major}" if user.college and user.major else ""}"""

        user_prompt = f"""{email_sender}
Recipient(s) Details:
{email_to or ""}
{email_cc or ""}
{email_bcc or ""}
Email Details:
{email_instruction}
{email_language_tone}
{email_length}"""

        messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]

        if ai == "openai":
            response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            )
        elif ai == "workersai":
            response = workersai.chat(messages)
        else:
            abort(400, 'Unsupported AI service')
        
        if ai == "workersai":
            if response['success'] == False and response['error'][0]['message'] == "Rate limited":
                abort(400, 'Rate limited. Please try again later.')
            elif response['success'] == False:
                abort(400, 'Error generating email')
                # Delete the chat
                db.session.delete(chat)
                db.session.commit()
        
        try:
            generated_text = response.choices[0].message.content if ai == "openai" else response['result']['response']
        except Exception as e:
            abort(400, 'Error generating email')
            # Delete the chat
            db.session.delete(chat)
            db.session.commit()
        
        if "Body:" in generated_text:
            split = generated_text.split("Subject: ")[1].split("Body:")
        else:
            split = generated_text.split("Subject: ")[1].split("\n", 1)
            
            
        subject = split[0]
        body = split[1] if not split[1].startswith("\n") else split[1][1:]
        
        response_data = {
            "subject": subject,
            "body": body
        }
        
        chat.name = subject
        
        
        encrypted_data = fernet.encrypt(json.dumps(input_data).encode()).decode()
        chat_message = ChatMessages(
            user_id = user.id,
            chat_id = chat_id,
            data = encrypted_data,
            chat_type = "user"
        )
        db.session.add(chat_message)
        
        encrypted_response_data = fernet.encrypt(json.dumps(response_data).encode()).decode()
        response_chat = ChatMessages(
            user_id = user.id,
            chat_id = chat_id,
            data = encrypted_response_data,
            chat_type = "assistant"
        )
        db.session.add(response_chat)
        
        db.session.commit()
        
        json_data = jsonify(
            chat_id=chat_id,
            assistant_message_id=response_chat.id,
            user_message_id=chat_message.id,
            contacts=contacts,
            user={
                "id": user.id,
                "first_name": oauth.first_name,
                "last_name": oauth.last_name,
                "email": user.email,
                "phone_code": user.phone_code,
                "phone_number": user.phone_number,
                "company": user.company,
                "work_title": user.work_title,
                "college": user.college,
                "major": user.major,
                },
            input=input_data,
            output=response_data
        )
        
        return make_response(json_data, 200)
    
    def modify_email(chat_id, contacts, instruction, language_tone, length, ai="openai"):
        user = current_user
        
        chat = Chat.query.filter_by(id=chat_id).first()
        
        oauth = Oauth.query.filter_by(id=chat.oauth_id).first()
        
        if not oauth:
            abort(404, 'Email Authentication not found.')
        
        contact_to, contact_cc, contact_bcc = ChatAssistant.seperate_contacts(contacts)
        
        if not chat:
            abort(404, 'Chat not found')
        
        email_length = f"Short (50-125 words)" if length == "short" else f"Medium (125-250 words)" if length == "medium" else f"Long (250+ words)" if length == "long" else "Unknown"
        
        input_data = {
            "contacts": contacts,
            "instruction": instruction,
            "language_tone": language_tone,
            "length": email_length
        }
        
        email_to = ChatAssistant.format_contact(contact_to)
        email_cc = ChatAssistant.format_contact(contact_cc) if contact_cc else None
        email_bcc = ChatAssistant.format_contact(contact_bcc) if contact_bcc else None
        
        email_instruction = f"New Intruction: {instruction}"
        email_language_tone = f"Language Tone: {language_tone}"
        email_length = f"Email Length: {email_length}"
        
        email_sender = f"""Sender Details:
Full Name: {oauth.first_name} {oauth.last_name or ''}
Email: {oauth.email}
{f"Phone: {user.phone_code} {user.phone_number}" if user.phone_code and user.phone_number else ""}
{f"Company: {user.company} - {user.work_title}" if user.company and user.work_title else ""}
{f"College: {user.college} - {user.major}" if user.college and user.major else ""}"""

        user_prompt = f"""{email_sender}
Recipient(s) Details:
{email_to or ""}
{email_cc or ""}
{email_bcc or ""}
Email Details:
{email_instruction}
{email_language_tone}
{email_length}"""

        pervious_chats = ChatAssistant.get_chat_history(chat_id)
        
        messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                *pervious_chats,
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        ) if ai == "openai" else workersai.chat(messages)
        
        if ai == "workersai":
            if response['success'] == False and response['error'][0]['message'] == "Rate limited":
                abort(400, 'Rate limited. Please try again later.')
            elif response['success'] == False:
                abort(400, 'Error generating email')
                
        try:
            generated_text = response.choices[0].message.content if ai == "openai" else response['result']['response']
        except Exception as e:
            abort(400, 'Error generating email')
        
        if "Body:" in generated_text:
            split = generated_text.split("Subject: ")[1].split("Body:")
        else:
            split = generated_text.split("Subject: ")[1].split("\n", 1)
            
            
        subject = split[0]
        body = split[1] if not split[1].startswith("\n") else split[1][1:]
        
        response_data = {
            "subject": subject,
            "body": body
        }
        
        encrypted_data = fernet.encrypt(json.dumps(input_data).encode()).decode()
        chat_message = ChatMessages(
            user_id = user.id,
            chat_id = chat_id,
            data = encrypted_data,
            chat_type = "user"
        )
        db.session.add(chat_message)
        
        encrypted_response_data = fernet.encrypt(json.dumps(response_data).encode()).decode()
        response_chat = ChatMessages(
            user_id = user.id,
            chat_id = chat_id,
            data = encrypted_response_data,
            chat_type = "assistant"
        )
        db.session.add(response_chat)
        
        db.session.commit()
        
        json_data = jsonify(
            chat_id=chat_id,
            contacts=contacts,
            assistant_message_id=response_chat.id,
            user_message_id=chat_message.id,
            user={
                "id": user.id,
                "first_name": oauth.first_name,
                "last_name": oauth.last_name,
                "email": oauth.email,
                "phone_code": user.phone_code,
                "phone_number": user.phone_number,
                "company": user.company,
                "work_title": user.work_title,
                "college": user.college,
                "major": user.major,
                },
            input=input_data,
            output=response_data
        )
        
        return make_response(json_data, 200)
    
    def send_email(contacts, subject, body, chat_id, oauth_id):
        
        chat = Chat.query.filter_by(id=chat_id).first()
        
        if not chat or chat.user_id != current_user.id:
            abort(404, 'Chat not found')
            
        if chat.is_sent:
            abort(400, 'Email already sent')
            
        
        oauth = Oauth.query.filter_by(id=oauth_id, user_id=current_user.id).first()
        if not oauth:
            abort(404, 'Email Authentication not found.')
            
        if oauth_id != chat.oauth_id:
            chat.oauth_id = oauth_id
            db.session.commit()
        
        # seperate the contacts
        contact_to, contact_cc, contact_bcc = ChatAssistant.seperate_contacts(contacts)
        
        # get email of each contact_to, contact_cc, contact_bcc in the dictionary
        contact_to = [contact['email'] for contact in contact_to]
        contact_cc = [contact['email'] for contact in contact_cc] if contact_cc else None
        contact_bcc = [contact['email'] for contact in contact_bcc] if contact_bcc else None
        
        if oauth.service == "google":
            oauth_data = fernet.decrypt(oauth.data.encode()).decode()
            oauth_data_dict = json.loads(oauth_data.replace("'", "\""))
            sender = f"{oauth.first_name} {oauth.last_name or ''} <{oauth.email}>"
            google = Google(oauth_data_dict)
            
            rendered_body = render_template("email-template.html", body=body, watermark=True)
            
            send = google.send_email(sender=sender, to=contact_to, subject=subject, message=rendered_body, cc=contact_cc, bcc=contact_bcc)
            if send:
                chat.is_sent = True
                db.session.commit()
                return True
        elif oauth.service == "microsoft":
            oauth_data = fernet.decrypt(oauth.data.encode()).decode()
            oauth_data_dict = json.loads(oauth_data.replace("'", "\""))
            sender = f"{oauth.first_name} {oauth.last_name or ''} <{oauth.email}>"
            rendered_body = render_template("email-template.html", body=body, watermark=True)
            # send the email using Microsoft
            microsoft = Microsoft(oauth_data_dict)
            send = microsoft.send_email(sender=sender, to=contact_to, subject=subject, body=rendered_body, cc=contact_cc, bcc=contact_bcc)
            if send:
                chat.is_sent = True
                db.session.commit()
                return True
            
        else:
            # send the email using SMTP
            pass
        
        return False
    
    def paraphrase_text(text, ai="openai"):
        
        messages = [
                {
                    "role": "system",
                    "content": "You are a simple paraphraser. Rephrase the input text while keeping its meaning intact and short. Your response should be concise and directly related to the original input. Do not add unrelated content, instructions, or prompts. Avoid including anything such as \"here is the rephrased text\" or placeholders like [your name]."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            # max_tokens=max_tokens
        ) if ai == "openai" else workersai.chat(messages)
        
        if ai == "workersai":
            if response['success'] == False and response['error'][0]['message'] == "Rate limited":
                abort(400, 'Rate limited. Please try again later.')
            elif response['success'] == False:
                abort(400, 'Error generating email')
                
        try:
            generated_text = response.choices[0].message.content if ai == "openai" else response['result']['response']
            
            # Pattern to match the punctuation at the end of the text
            pattern = r'[\W_]*$'
            
            # Get the original punctuation
            original_punctuation = re.search(pattern, text)
            original_punctuation_char = original_punctuation.group() if original_punctuation else ""
            
            # Remove the punctuation from the generated text
            generated_text = re.sub(pattern, '', generated_text)
            # Add the original punctuation to the generated text
            generated_text += original_punctuation_char
            
            return generated_text
        except Exception as e:
            abort(400, 'Error generating email')
            return None
        
    def smart_reply(subject, body, sender, instruction, oauth, ai="openai"):
        
        body = Email.extract_text_from_html(body)
        
        text = f"Subject: {subject}{backslash_n}Body: {body}"
        
        email_instruction = f"Instruction: {instruction}"
        
        email_sender = f"""Full Name: {oauth.first_name} {oauth.last_name or ""}
Email: {oauth.email}"""

        user_prompt = f"""My Details:
{email_sender}

Recipient(s) Details:
{sender}

Instruction:
{email_instruction}"""
        
        messages = [
                {
                    "role": "system",
                    "content": f"""You are an email generator. Based on the provided details, generate a concise and relevant draft reply. Ensure the reply aligns with the original email’s tone and context. Include appropriate greetings (e.g., \"Dear,\" \"Hello\") and a closing signature (e.g., \"Best regards,\" \"Sincerely\") based on the tone. Do not include introductory phrases, placeholders (e.g., \"[your name]\"), unrelated content, or a subject line. Focus solely on generating the reply content. Today's date is {today_date_time}."""
                },
                {
                    "role": "user",
                    "content": text
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            # max_tokens=max_tokens
        ) if ai == "openai" else workersai.chat(messages)
        
        if ai == "workersai":
            if response['success'] == False and response['error'][0]['message'] == "Rate limited":
                abort(400, 'Rate limited. Please try again later.')
            elif response['success'] == False:
                abort(400, 'Error generating email')
                
        try:
            generated_text = response.choices[0].message.content if ai == "openai" else response['result']['response']
            return generated_text
        except Exception as e:
            abort(400, 'Error generating email')
            return None