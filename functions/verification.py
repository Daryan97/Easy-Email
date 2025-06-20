import re
from models.user import User, UserOTPs
from functions.email import Email

from werkzeug.security import generate_password_hash

from init import db, create_logger

from datetime import datetime, timedelta
import random

logger = create_logger(__name__)

# Define the Verification class
class EmailVerification:
    # Define the set_email_otp method
    def set_email_otp(user_id):
        try:
            # Get the user by the user_id
            user = User.query.get(user_id)
            
            # Check if the user exists
            if not user:
                return False
            
            # Delete all the user OTPs
            UserOTPs.query.filter_by(user_id=user.id, otp_type='email_verification').delete()

            # Generate a random 6-digit OTP
            otp = random.randint(100000, 999999)

            # Add the OTP to the database
            db.session.add(
                UserOTPs(
                    user_id=user.id,
                    otp=otp,
                    otp_type='email_verification',
                    expired_at=datetime.now() + timedelta(minutes=10)
                )
            )

            # Commit the changes to the database
            db.session.commit()

            # Send email confirmation email
            Email.send_verification_email(
                recipients=user.email,
                context={
                    'user_fullname': f'{user.first_name} {user.last_name}',
                    'verification_code': otp,
                    'verification_type': 'Email Confirmation'
                }
            )

            return True
        except Exception as e:
            logger.error(e)
            return False
        
    # Define the verify_email_otp method
    def verify_email_otp(user_id, otp):
        try:
            # Get the user OTP by the user_id and OTP
            user_otp = UserOTPs.query.filter_by(user_id=user_id, otp=otp, otp_type='email_verification').order_by(UserOTPs.id.desc()).first()

            # Check if the user OTP exists
            if user_otp:
                # Check if the OTP is expired
                if user_otp.expired_at > datetime.now():
                    user = User.query.get(user_id)
                    user.email_confirmed_at = datetime.now()
                    # Delete the user OTP
                    db.session.delete(user_otp)
                    # Commit the changes to the database
                    db.session.commit()

                    return True
            return False
        except Exception as e:
            logger.error(e)
            return False

# Define the Password class
class Password:
    # Define the password validation method
    def validate_password(password):
        # Check if the password is at least 8 characters long, contains a lowercase letter, an uppercase letter, a number, a special character
        if (len(password)<=8) or re.search('[a-z]', password) is None or re.search('[A-Z]', password) is None or re.search('[0-9]', password) is None or re.search('[!@#$%^&*()_+]', password) is None:
            return False
        else:
            return True
        
    # Define the reset_password_otp method
    def reset_password_otp(user_id):
        try:
            # Get the user by the user_id
            user = User.query.get(user_id)
            
            # Check if the user exists
            if not user:
                return False
            
            # Delete all the user OTPs
            UserOTPs.query.filter_by(user_id=user.id, otp_type='reset_password').delete()
            
            # Generate a random 6-digit OTP
            otp = random.randint(100000, 999999)
            
            # Add the OTP to the database
            db.session.add(
                UserOTPs(
                    user_id=user.id,
                    otp=otp,
                    otp_type='reset_password',
                    expired_at=datetime.now() + timedelta(minutes=10)
                )
            )
            
            # Commit the changes to the database
            db.session.commit()
            
            # Send reset password email
            Email.send_verification_email(
                recipients=user.email,
                context={
                    'user_fullname': f'{user.first_name} {user.last_name}',
                    'verification_code': otp,
                    'verification_type': 'Reset Password'
                }
            )
            
            return True
        except Exception as e:
            logger.error(e)
            return False

    # Define the verify_reset_password_otp method
    def reset_password(user_id, otp, new_password):
        try:
            # Get the user OTP by the user_id and OTP
            user_otp = UserOTPs.query.filter_by(user_id=user_id, otp=otp, otp_type='reset_password').order_by(UserOTPs.id.desc()).first()
            
            # Check if the user OTP exists
            if user_otp:
                # Check if the OTP is expired
                if user_otp.expired_at > datetime.now():
                    user = User.query.get(user_id)
                    user.password = generate_password_hash(new_password)
                    # Delete the user OTP
                    db.session.delete(user_otp)
                    # Commit the changes to the database
                    db.session.commit()
                    
                    return True
            return False
        except Exception as e:
            logger.error(e)
            return False