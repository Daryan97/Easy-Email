import datetime
from flask import Blueprint, flash, render_template, redirect, request, session, url_for, get_flashed_messages
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_access_cookies, unset_jwt_cookies, verify_jwt_in_request, current_user

from init import create_logger, db # TODO: Remove DB import

from decorators import privacy_accepted_required, terms_accepted_required
from init import env

import google_auth_oauthlib
import json, requests
import msal

logger = create_logger(__name__)

# Create a blueprint for the main routes
main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

# Define the Google scopes
GOOGLE_SCOPES = env.get('GOOGLE_SCOPES').split(',')
MICROSOFT_SCOPES = env.get('MICROSOFT_SCOPES').split(',')

MICROSOFT_CLIENT_ID = env.get('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = env.get('MICROSOFT_CLIENT_SECRET')
MICROSOFT_AUTHORITY = env.get('MICROSOFT_AUTHORITY')

@main.route('/')
def index():
    # Check if the user is logged in
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        # Redirect to the dashboard
        return redirect(url_for('main.dashboard'))
    else:
        # Render the index template
        return redirect(url_for('main.login'))

# Define the dashboard route
@main.route('/dashboard')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def dashboard():
    # Check if current_user is logged in
    if current_user:
        # Check if the user has verified their email
        if not current_user.email_confirmed_at:
            # Redirect to the verify page
            return redirect(url_for('main.verify'))
        # Render the dashboard template
        return render_template('dashboard.html', user=current_user)

# Define the register route
@main.route('/register')
def register():
    # Check if the user is logged in
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        # Redirect to the dashboard
        return redirect(url_for('main.dashboard'))
    else:
        # Render the register template
        return render_template('register.html')

# Define the login route
@main.route('/login')
def login():
    # Check if the user is logged in
    verify_jwt_in_request(optional=True)
    if get_jwt_identity() is not None and current_user:
        # Redirect to the dashboard
        return redirect(url_for('main.dashboard'))
    else:
        # Get the flashed messages
        messages = get_flashed_messages(with_categories=True)
        if messages:
            type = messages[0][0]
            message = messages[0][1]
            return render_template('login.html', type=type, message=message)
        # Render the login template
        return render_template('login.html')

# Define the verify route
@main.route('/verify')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def verify():
    # Check if the user has verified their email
    if current_user.email_confirmed_at is not None:
        # Redirect to the dashboard
        return redirect(url_for('main.dashboard'))
    # Render the verify template
    return render_template('verify.html', user=current_user)

# Define the forgot password route
@main.route('/forgot-password')
def forgot_password():
    # Check if the user is logged in
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        # Render the template with the user's email
        return render_template('forgot.html', email=current_user.email)
    else:
        # Render the forgot password template
        return render_template('forgot.html')

# Define the link route
@main.route('/profile/link')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def link():
    # Check if the user has verified their email
    if not current_user.email_confirmed_at:
        # Redirect to the verify page
        return redirect(url_for('main.verify'))
    
    # Get the flashed messages
    messages = get_flashed_messages(with_categories=True)
    # Check if there are messages
    if messages:
        # Get the message and the category
        type = messages[0][0]
        message = messages[0][1]
        # Render the link template with the message
        return render_template('link.html', user=current_user, type=type, message=message)
    else:
        # Render the link template
        return render_template('link.html', user=current_user)

# Define the profile route
@main.route('/profile')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def profile():
    # Check if the user has verified their email
    if not current_user.email_confirmed_at:
        # Redirect to the verify page
        return redirect(url_for('main.verify'))
    # Render the profile template
    return render_template('profile.html', user=current_user)

# Define the contacts route
@main.route('/profile/contacts')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def contacts():
    # Check if the user has verified their email
    if not current_user.email_confirmed_at:
        # Redirect to the verify page
        return redirect(url_for('main.verify'))
    # Render the contacts template
    return render_template('contacts.html', user=current_user)

# Define the error route
@main.route('/error')
def error():
    # Get the flashed messages
    messages = get_flashed_messages(with_categories=True)
    # Check if there are messages
    if messages:
        # Get the message and the category
        code = messages[0][0]
        message = messages[0][1]
    else:
        # Redirect to the dashboard
        return redirect(url_for('main.dashboard'))
    
    # Render the error template
    return render_template('error.html', code=code, message=message)

# Define the link service route
@main.route('/link/<string:service>')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def link_account(service):
    if service == 'google':
        # Create a Google OAuth flow
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=GOOGLE_SCOPES)

        # Set the redirect URI
        flow.redirect_uri = url_for('main.link_callback', service=service, _external=True)
        

        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true')

        # Save the state
        session['state'] = state
        # Redirect to the authorization URL
        return redirect(authorization_url)
    elif service == 'microsoft':
        # Create a Microsoft OAuth flow
        msal_app = msal.ConfidentialClientApplication(
            MICROSOFT_CLIENT_ID,
            authority= MICROSOFT_AUTHORITY,
            client_credential= MICROSOFT_CLIENT_SECRET
        )
        
        # Generate the authorization URL
        authorization_url = msal_app.get_authorization_request_url(
            scopes=MICROSOFT_SCOPES,
            redirect_uri=url_for('main.link_callback', service=service, _external=True)
        )
        
        # Redirect to the authorization URL
        return redirect(authorization_url)
        
    
    return redirect(url_for('main.link'))

# Define the link service callback route
@main.route('/auth/<string:service>/callback')
@terms_accepted_required
@privacy_accepted_required
@jwt_required()
def link_callback(service):
    if service == 'google':
        try:
            # Get the state
            state = session.pop('state', None)
            if state is None or state != request.args.get('state'):
                flash(category='danger', message='Invalid state parameter.')
                return redirect(url_for('main.link'))

            # Create a Google OAuth flow
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                'client_secret.json',
                scopes=GOOGLE_SCOPES,
                state=state)

            # Set the redirect URI
            flow.redirect_uri = url_for('main.link_callback', service=service, _external=True)

            # Fetch the token
            authorization_response = request.url
            flow.fetch_token(authorization_response=authorization_response)

            # Get the credentials
            credentials = flow.credentials

            # Convert the credentials to a dictionary
            creds_json = json.loads(credentials.to_json())

            # Get the API URL
            api_url = url_for('api.link_o_auth', service=service, _external=True).replace('?service=', '/')

            # Get the JWT access token
            jwt_access_token = request.cookies.get('access_token_cookie')
            
            # Send the data to the API
            response = requests.post(api_url, json=creds_json, headers={'Authorization': f'Bearer {jwt_access_token}'})

            response_data = response.json()
            # Check if the response is successful
            if response.status_code == 200:
                flash(category='success', message=response_data['message'])
            else:
                # Flash the error message
                flash(category='danger', message=response_data['message'])

            # Redirect to the link page
            return redirect(url_for('main.link'))

        # Handle exceptions
        except Exception as e:
            logger.error(e)
            # Check if the scope has changed
            if 'Scope has changed from' in str(e):
                # Flash the error message
                flash(category='danger', message='You did not granted the required permissions')
            else:
                # Flash the error message
                flash(category='danger', message='Linking account failed.')
        
    elif service == 'microsoft':
        try:
            # Microsoft callback logic using MSAL
            msal_app = msal.ConfidentialClientApplication(
                MICROSOFT_CLIENT_ID,
                authority= MICROSOFT_AUTHORITY,
                client_credential= MICROSOFT_CLIENT_SECRET
            )
            
            # Get the authorization code
            code = request.args.get('code')
            
            # Fetch the token
            result = msal_app.acquire_token_by_authorization_code(
                code,
                scopes=MICROSOFT_SCOPES,
                redirect_uri=url_for('main.link_callback', service=service, _external=True)
            )
            
            
            if 'access_token' in result:
                # Extract the access token and user information
                creds_json = json.dumps(result)
                
                # Get the API URL
                api_url = url_for('api.link_o_auth', service=service, _external=True).replace('?service=', '/')
                
                # Get the JWT access token
                jwt_access_token = request.cookies.get('access_token_cookie')
                
                # Send the data to the API
                response = requests.post(api_url, json=creds_json, headers={'Authorization': f'Bearer {jwt_access_token}'})
                
                response_data = response.json()
                
                # Check if the response is successful
                if response.status_code == 200:
                    flash(category='success', message=response_data['message'])
                else:
                    # Flash the error message
                    flash(category='danger', message=response_data['message'])
                    
            else:
                # Flash the error message
                flash(category='danger', message='Linking account failed.')
                
        except Exception as e:
            logger.error(e)
            # Flash the error message
            flash(category='danger', message='Linking account failed.')

    # Redirect to the link page
    return redirect(url_for('main.link'))


terms_date = datetime.datetime.strptime(env.get('TERMS_OF_SERVICE_DATE', ''), '%Y-%m-%d')
privacy_date = datetime.datetime.strptime(env.get('PRIVACY_POLICY_DATE', ''), '%Y-%m-%d')

@main.route('/terms')
@jwt_required()
def terms():
    if current_user.terms_accepted_at and current_user.terms_accepted_at > terms_date:
        return redirect(url_for('main.dashboard'))
    current_user.terms_accepted_at = datetime.datetime.now()
    db.session.commit()
    return {'message': 'Debug: Terms of service accepted'}

@main.route('/privacy')
@jwt_required()
def privacy():
    if current_user.privacy_accepted_at and current_user.privacy_accepted_at > privacy_date:
        return redirect(url_for('main.dashboard'))
    current_user.privacy_accepted_at = datetime.datetime.now()
    db.session.commit()
    return {'message': 'Debug: Privacy policy accepted'}

@main.route('/dashboard/inbox')
@jwt_required()
def inbox():
    return render_template('inbox.html', user=current_user)