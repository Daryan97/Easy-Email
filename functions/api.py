from flask_restx import fields
from datetime import datetime, timezone, timedelta
from init import env
from flask_jwt_extended import verify_jwt_in_request, current_user
from flask_limiter.util import get_remote_address

# Local timezone offset
local_tz = timezone(timedelta(hours=int(env.get('TIMEZONE_OFFSET'))))

# Custom DateTime field
class DateTime(fields.Raw):
    # Format value
    def format(self, value):
        # Convert to local timezone if value is a datetime object
        if isinstance(value, datetime):
            # Return formatted date
            return value.astimezone(local_tz).strftime('%a, %d %b %Y %H:%M:%S %z')
        # Return value
        return value


# Rate limit key function
def rate_limit_key():
    # Check if user is authenticated
    verify_jwt_in_request(optional=True)
    # Get user id or remote address
    key = current_user.id if current_user else get_remote_address()
    
    # Return key
    return key

# Bypass role function
def role_bypass(role_name):
    # Check if user has role
    return current_user.has_role(role_name) if current_user else False