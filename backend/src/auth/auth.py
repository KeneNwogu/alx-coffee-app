import json
import os

import requests
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen

from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
APP_SECRET_KEY = os.environ.get('APP_SECRET_KEY')

ALGORITHMS = ['RS256']
API_AUDIENCE = 'dev'


# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''


def get_token_auth_header():
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        raise AuthError('No auth headers provided', 401)
    if len(auth_header.split('')) != 2:
        raise AuthError('Invalid Authorization format', 401)

    auth_type, auth_token = auth_header.split('')
    if auth_type.lower() != 'bearer':
        raise AuthError({
            'message': 'Bearer token was not provided',
            'success': False
        }, 401)

    return auth_token


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''


def check_permissions(permission, payload):
    if payload.get('scope'):
        for scope in payload['scope'].split():
            if permission == scope:
                return True
    raise AuthError({'message': 'Do not possess required permissions'}, 403)


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''


def verify_decode_jwt(token):
    auth0_verification = requests.get(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = auth0_verification.json()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key['kty'] = unverified_header['kty']
            rsa_key['kid'] = unverified_header['kid']
            rsa_key['use'] = unverified_header['use']
            rsa_key['n'] = unverified_header['n']
            rsa_key['e'] = unverified_header['e']
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({'success': False, 'message': 'Token has expired'}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({'success': False, 'message': 'Invalid token passed'}, 401)
        except Exception:
            raise AuthError({'success': False, 'message': 'Token could not be parsed'}, 401)
        return payload
    raise Exception('Not Implemented')


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
                payload = verify_decode_jwt(token)
                check_permissions(permission, payload)
                return f(payload, *args, **kwargs)
            except AuthError as e:
                abort(e.status_code, error_message=e.error)

        return wrapper

    return requires_auth_decorator
