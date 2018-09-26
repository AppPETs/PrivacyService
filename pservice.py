"""Main application module.
Defines the supported API (GET, POST, DELETE) and their behaviour. Interfaces
with the database to persist data."""

from bottle import error, get, post, hook, request, run, Bottle, HTTPError, HTTPResponse, static_file

import unittest
import sys
import os
import argparse
import json

from database import Database
import config

from http import HTTPStatus
from database import Database

app = application = Bottle()
app.db = Database()


class HttpHeader:
    Host = 'Host'
    ContentLength = 'Content-Length'
    ContentType = 'Content-Type'


class MimeType:
    class Application:
        OctetStream = 'application/octet-stream'


def key_filter(conf):
    KEY_LENGTH_IN_BYTES = config.KEY_SIZE_IN_BITS / 8
    regexp = r'([\da-f]{%d})' % int(KEY_LENGTH_IN_BYTES * 2)

    def to_python(s):
        return s

    def to_url(key):
        return key

    return regexp, to_python, to_url

app.router.add_filter('key', key_filter)


def sanitize_request_headers(allowed_headers):
    """Function decorator that sanitizes request headers.
    Supports a parameter to indicate which headers are allowed."""
    def sanitize_decorator(function):
        def wrapper(*args, **kwargs):
            # Check if any non-essential headers were submitted.
            superfluous_headers = set(request.headers) - allowed_headers
            if superfluous_headers:
                return HTTPResponse(
                    status = HTTPStatus.BAD_REQUEST,
                    body = 'Superfluous headers are not allowed, they could be used for fingerprinting attacks: "%s"' %
                    '", "'.join(sorted(list(superfluous_headers)))
                )
            return function(*args, **kwargs)

        # Only hook function if superfluous headers are not allowed
        if config.SUPERFLUOUS_HEADERS_ALLOWED:
            return function
        else:
            return wrapper
    return sanitize_decorator


def provide_db_session():
    """This decorator transparently adds a db_session kwarg to the function."""
    def provide_db_session_decorator(function):
        def wrapper(*args, **kwargs):
            if 'db_session' not in kwargs:
                with app.db.session_scope() as session:
                    kwargs['db_session'] = session

                    return function(*args, **kwargs)
            else:
                return function(*args, **kwargs)

        return wrapper
    return provide_db_session_decorator


def should_log_request(req):
    tracking_value = req.headers.get('X-AppPETs-BadProvider', None)
    return tracking_value is not None and tracking_value is not '0'


def log_request(action):
    """Decorator for request functions that get a single `key` argument.
    This decorator transparently logs the requests, if logging is enabled."""
    def log_request_decorator(function):
        def wrapper(*args, **kwargs):
            """The wrapper function 
            a) creates a database session,
            b) queries the existing value for a key, 
            c) invokes the
            request handler, 
            d) queries the value for a key after
            invoking the handler and 
            e) logs the event before returning
            the function's response"""
            if not should_log_request(request):
                return function(*args, **kwargs)

            session = kwargs['db_session']
            key = kwargs['key']

            # Lookup value before invoking the function
            value_before = getattr(
                app.db.lookup_entry(session, key), 
                'value', None)

            response = function(*args, **kwargs)

            # Lookup value after invoking the function
            value_after = getattr(app.db.lookup_entry(session, key),
                'value', None)

            app.db.log_event(session, action, request, key, value_before, value_after)

            return response

        # Enable request logging globally. Requests are only tracked if the caller
        # explicitly allows this using the header 'X-AppPETs-BadProvider' and a non 0 value.
        if config.REQUEST_LOGGING:
            return wrapper
        else:
            return function
    return log_request_decorator


@app.get('/storage/v1/<key:key>')
@sanitize_request_headers({ HttpHeader.Host })
@provide_db_session()
@log_request('Retrieve')
def retrieve_value(key, db_session=None):
    value = app.db.value_for(db_session, key)

    if not value:
        return HTTPResponse(
            status = HTTPStatus.NOT_FOUND, 
            body = 'The requested entry does not exist.'
        )

    return HTTPResponse(
        status = HTTPStatus.OK,
        headers = {
            HttpHeader.ContentType: MimeType.Application.OctetStream
        },
        body = value
    )


@app.post('/storage/v1/<key:key>')
@sanitize_request_headers({
    HttpHeader.Host,
    HttpHeader.ContentType,
    HttpHeader.ContentLength
})
@provide_db_session()
@log_request('Update')
def update_value(key, db_session=None):
    try:
        contentLength = int(request.content_length)
    except ValueError:
        return HTTPResponse(
            status = HTTPStatus.BAD_REQUEST, 
            body = '"%s" is not a valid value for the HTTP "%s" header.' 
            % (request.headers[HttpHeader.ContentLength], HttpHeader.ContentLength)
        )

    value = request.body.read(contentLength)
    app.db.insert_or_replace(db_session, key, value)


@app.delete('/storage/v1/<key:key>')
@sanitize_request_headers({ HttpHeader.Host })
@provide_db_session()
@log_request('Delete')
def delete_entry(key, db_session=None):
    app.db.remove(db_session, key)

    return HTTPResponse(status = HTTPStatus.OK)


@app.get('/storage/v1/dump')
@provide_db_session()
def json_dump(db_session=None):
    """Returns a JSON representation of the database
    for use by the visualisation code.

    ATTENTION / TODO: This API can be called by _everyone_ and is not secured by
    access control. An attacker can use this API to retrieve a list of keys
    with which then to delete data en masse.
    """
    return app.db.dump(db_session)


# Visualisation-related code
@app.get('/visualisation/v1/<path:path>')
def visualisation_resource(path):
    return static_file(path, root = config.VISUALISATION_STATIC_FILES_ROOT)


# Error-handling
@app.error(HTTPStatus.NOT_FOUND)
def invalid_endpoint(error):
    return HTTPResponse(
        status = HTTPStatus.NOT_FOUND,
        body = 'The URL is not a valid service endpoint.'
    )

if __name__ == '__main__':
    run(app, 
        host=config.SERVER_CONFIGURATION['ADDRESS'], 
        port=config.SERVER_CONFIGURATION['PORT'])
