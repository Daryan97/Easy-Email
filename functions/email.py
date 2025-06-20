import re
from bs4 import BeautifulSoup
from flask_mail import Message
from flask import render_template
from init import mail, env, create_logger

from email_validator import validate_email, caching_resolver

logger = create_logger(__name__)

class Email:
    def send_email(subject, recipients, context, cc=None, bcc=None, sender=env.get('MAIL_DEFAULT_SENDER'), template='email-template.html'):
        try:
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                html=render_template(template_name_or_list=template, **context)
            )
            mail.send(msg)
            
            return True
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
    
    def send_verification_email(recipients, context):
        try:
            return Email.send_email(
                subject=f'[Easy-Email] {context["verification_type"]}',
                recipients=[recipients],
                context=context,
                template='email-verification.html'
            )
        except Exception as e:
            logger.error('{} at line {}'.format(e, e.__traceback__.tb_lineno))
            return False
        
    # Define validate email method
    def validate_email(email, check_deliverability=False):
        try:
            dns_resolver = caching_resolver(timeout=10)
            
            validate = validate_email(email, check_deliverability=check_deliverability, dns_resolver=dns_resolver)
            
            return validate
        except Exception as e:
            return str(e)
        
    # Define extract text from html method
    def extract_text_from_html(html):
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract text and separate different elements with a newline
            text = soup.get_text(separator='\n').strip()

            # Replace multiple spaces or newlines with a single space or newline
            cleaned_text = re.sub(r'\s+', ' ', text)  # Convert multiple spaces to a single space
            cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Reduce multiple line breaks to a single newline
            cleaned_text = re.sub(r' +', ' ', cleaned_text)  # Convert multiple spaces to a single space

            # Optionally, remove non-breaking spaces (\u200b) if needed
            cleaned_text = re.sub(r'\u200b', '', cleaned_text)

            return cleaned_text
        except Exception as e:
            return str(e)