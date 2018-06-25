"""Simple object-oriented database wrapper around the models."""

from models import Event, HttpRequest, HttpHeader, Value, Entry, initiate_data_definitions
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker

import datetime
from hashlib import blake2b

from contextlib import contextmanager
import config

def make_engine():
    if config.DATABASE['ENGINE'] == 'sqlite':
        return create_engine('sqlite:///' + config.DATABASE['DATABASE_FILE'])
    elif config.DATABASE['ENGINE'] == 'postgresql':
        return create_engine('{}://{}:{}@{}/{}'.format(
            config.DATABASE['ENGINE'],
            config.DATABASE['USER'],
            config.DATABASE['PASSWORD'],
            config.DATABASE['ADDRESS'],
            config.DATABASE['NAME']))

    assert(false and 'Unsupported configuration specified.')

class Database:
    def __init__(self):
        self.engine = make_engine()
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

    def hash_value(self, value):
        """Returns a hash of `value`"""
        # Blake2 is used here, because it can be configured using different
        # digest output sizes. It is also faster than SHA1
        # https://research.kudelskisecurity.com/2017/03/06/why-replace-sha-1-with-blake2/
        h = blake2b(digest_size=config.DIGEST_SIZE)
        h.update(value)
        return h.digest()

    def lookup_value(self, session, value):
        """Lookup an existing entry in the data store."""
        return session.query(Value)\
                      .filter(Value.hash == self.hash_value(value))\
                      .one_or_none()


    def insert_or_replace(self, session, key, value):
        entry = self.lookup_entry(session, key)
        
        if entry:
            # Update existing entry
            entry.value = self.lookup_value(session, value) or Value(hash=self.hash_value(value), blob=value)
        else:
            # Create new entry.
            entry = Entry(key=key, value=self.lookup_value(session, value) or Value(hash=self.hash_value(value), blob=value))
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