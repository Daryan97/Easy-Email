from datetime import datetime, timezone, timedelta
from flask import jsonify, make_response, request, redirect, url_for, flash
from flask_jwt_extended import current_user, unset_jwt_cookies, unset_access_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from init import app, jwt, env, limiter
from models.user import RevokedTokens, User

class FlaskErrorLoaders:
    @app.errorhandler(404)
    def page_not_found(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Resource not found."
                ), 404)
        else:
            flash(message="Resource not found.", category=404)
            return redirect(url_for("main.error"))

    @app.errorhandler(500)
    def internal_server_error(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Internal server error."
                ), 500)
        else:
            flash(message="Internal server error.", category=500)
            return redirect(url_for("main.error"))

    @app.errorhandler(405)
    def method_not_allowed(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Method not allowed."
                ), 405)
        else:
            flash(message="Method not allowed.", category=405)
            return redirect(url_for("main.error"))

    @app.errorhandler(400)
    def bad_request(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Bad request."
                ), 400)
        else:
            flash(message="Bad request.", category=400)
            return redirect(url_for("main.error"))
        
    @app.errorhandler(401)
    def unauthorized(e):
        if "api" in request.url:
            return make_response(jsonify(
                message=e
                ), 401)
        else:
            flash(message=e, category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @app.errorhandler(403)
    def forbidden(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Forbidden request."
                ), 403)
        else:
            flash(message="Forbidden request.", category=403)
            return redirect(url_for("main.error"))

    @app.errorhandler(422)
    def unprocessable_entity(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Unprocessable entity."
                ), 422)
        else:
            flash(message="Unprocessable entity.", category=422)
            return redirect(url_for("main.error"))

    @app.errorhandler(429)
    def too_many_requests(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Too many requests."
                ), 429)
        else:
            flash(message="Too many requests.", category=429)
            return redirect(url_for("main.error"))

    @app.errorhandler(503)
    def service_unavailable(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Service unavailable."
                ), 503)
        else:
            flash(message="Service unavailable.", category=503)
            return redirect(url_for("main.error"))

    @app.errorhandler(504)
    def gateway_timeout(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Gateway timeout."
                ), 504)
        else:
            flash(message="Gateway timeout.", category=504)
            return redirect(url_for("main.error"))
        
    @app.errorhandler(505)
    def http_version_not_supported(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="HTTP version not supported."
                ), 505)
        else:
            flash(message="HTTP version not supported.", category=505)
            return redirect(url_for("main.error"))
        
    @app.errorhandler(415)
    def unsupported_media_type(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="Unsupported media type."
                ), 415)
        else:
            flash(message="Unsupported media type.", category=415)
            return redirect(url_for("main.error"))
        
    @app.errorhandler(NoAuthorizationError)
    def no_authorization_error(e):
        if "api" in request.url:
            return make_response(jsonify(
                message="No authorization token found."
                ), 401)
        else:
            flash(message="No authorization token found.", category=401)
            return redirect(url_for("main.error"))
    
class JWTErrorLoaders:
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if "api" in request.url:
            return jsonify({
                "message": "Your credentials have expired",
            }), 401
        else:
            flash(message="Your credentials have expired", category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(error)
        if "api" in request.url:
            return jsonify({
                "message": "Invalid credentials",
            }), 401
        else:
            flash(message="Invalid credentials", category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @jwt.unauthorized_loader
    def unauthorized_loader(error):
        if "api" in request.url:
            return jsonify({
                "message": "Session expired or unauthorized access"
            }), 401
        else:
            flash(message="Session expired or unauthorized access", category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_loader():
        if "api" in request.url:
            return jsonify({
                "message": "The credentials are not fresh"
            }), 401
        else:
            flash(message="The credentials are not fresh", category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @jwt.revoked_token_loader
    def revoked_token_loader():
        if "api" in request.url:
            return jsonify({
                "message": "The credentials have been revoked"
            }), 401
        else:
            flash(message="The credentials have been revoked", category=401)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response

    @jwt.user_lookup_error_loader
    def user_loader_error_callback(jwt_header, jwt_payload):
        if "api" in request.url:
            return jsonify({
                "message": "User not found"
            }), 404
        else:
            flash(message="User not found", category=404)
            response = redirect(url_for("main.login"))
            unset_jwt_cookies(response)
            unset_access_cookies(response)
            return response
    
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return RevokedTokens.query.filter_by(jti=jwt_payload["jti"]).first()
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        if "api" in request.url:
            return jsonify({
                "message": "The token has been revoked"
            }), 401
        else:
            flash(message="The token has been revoked", category=401)
            return redirect(url_for("main.login"))
        
class JWTUserCallbacks:
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        user = User.query.filter_by(id=identity).first()
        if not user is None:
            return user
        return None
    
local_tz = timezone(timedelta(hours=int(env.get('TIMEZONE_OFFSET'))))
class TemplateFilters:
    @app.template_filter("rfc822")
    def rfc822(value):
        if isinstance(value, datetime):
            return value.astimezone(local_tz).strftime('%a, %d %b %Y %H:%M:%S %z')
        return value
    
    