import datetime
from functools import wraps
from flask_jwt_extended import current_user, jwt_required, verify_jwt_in_request
from flask_restx import abort
from flask import redirect, url_for, flash, request
from init import env

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_admin = current_user.has_role('admin')
        
        if not is_admin:
            if "api" in request.url:
                abort(403, 'Forbidden request')
            else:
                flash('Forbidden request', category=403)
                return redirect(url_for('main.error'))
        
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_premium = current_user.has_role('premium')
        
        if not is_premium:
            if "api" in request.url:
                abort(403, 'This feature is only available for premium users')
            else:
                flash('This feature is only available for premium users', category='Premium')
                return redirect(url_for('main.error'))
        
        return f(*args, **kwargs)
    return decorated_function

terms_date = datetime.datetime.strptime(env.get('TERMS_OF_SERVICE_DATE', ''), '%Y-%m-%d')
privacy_date = datetime.datetime.strptime(env.get('PRIVACY_POLICY_DATE', ''), '%Y-%m-%d')

def terms_accepted_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        
        last_terms_accepted = current_user.terms_accepted_at
        
        if not last_terms_accepted or last_terms_accepted < terms_date:
            if "api" in request.url:
                abort(403, 'Please accept the terms of service')
            else:
                return redirect(url_for('main.terms'))
        
        return f(*args, **kwargs)
    return decorated_function

def privacy_accepted_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        last_privacy_accepted = current_user.privacy_accepted_at
        
        if not last_privacy_accepted or last_privacy_accepted < privacy_date:
            if "api" in request.url:
                abort(403, 'Please accept the privacy policy')
            else:
                return redirect(url_for('main.privacy'))
        
        return f(*args, **kwargs)
    return decorated_function