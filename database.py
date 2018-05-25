"""Simple object-oriented database wrapper around the models."""

from models import Event, HttpRequest, HttpHeader, Value, Entry, initiate_data_definitions
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker

import datetime

from contextlib import contextmanager


def _engine_from_configuration(configuration_obj):
    assert 'DATABASE_FILE' in configuration_obj
    return create_engine('sqlite:///' + configuration_obj['DATABASE_FILE'])


class Database:
    def __init__(self, configuration_obj):
        self.engine = _engine_from_configuration(configuration_obj)
        self.session_maker = sessionmaker(bind=self.engine)

        # Populate the database with the models
        initiate_data_definitions(self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


    def lookup_entry(self, session, key):
        """Lookup an existing entry in the data store."""
        return session.query(Entry)\
                      .filter(Entry.key == key)\
                      .one_or_none()


    def insert_or_replace(self, session, key, value):
        entry = self.lookup_entry(session, key)
        
        if entry:
            # Update existing entry
            entry.value = Value(blob=value)
        else:
            # Create new entry.
            entry = Entry(key=key, value=Value(blob=value))
            session.add(entry)


    def value_for(self, session, key):
        entry = self.lookup_entry(session, key)

        if entry:
            return entry.value.blob
        return None


    def remove(self, session, key):
        entry = self.lookup_entry(session, key)
        if entry:
            session.delete(entry)
    

    def log_event(self, session, action, request, key, value_before, value_after):
        """Log a request to the database."""
        # Process headers
        def lookup_or_create_header(key, value):
            """Checks whether the specified header is already present in the
            database. If so, re-uses the existing definition. Otherwise creates
            a new HttpHeader object."""
            existing = session\
                .query(HttpHeader)\
                .filter(and_(HttpHeader.key == key, HttpHeader.value == value))\
                .one_or_none()

            return existing if existing else HttpHeader(key = key, value = value)

        headers = [lookup_or_create_header(k, v) for (k, v) in request.headers.items()]
        # Assuming the request was sent now
        request_time = datetime.datetime.now()
        # Handle case where server operates behind proxy server
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR')\
                or request.environ.get('REMOTE_ADDR')

        req = HttpRequest(timestamp = request_time, 
                          sender    = client_ip, 
                          headers   = headers)

        event = Event(action        = action,
                      request       = req,
                      key           = key,
                      value_before  = value_before,
                      value_after   = value_after)

        session.add(event)
