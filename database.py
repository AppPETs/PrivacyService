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

    def active_keys(self, session):
        """Return a list of keys current active in the PrivacyService"""
        existing_keys = session.query(Entry.key).all()
        for x in existing_keys:
            yield x.key

    def dump(self, session):
        """Introspection API: return a dump of the database

        This function returns a dictionary mapping database keys
        to dictionaries of the following structure:
        k: {
            'current': {
                'timestamp': ...,
                'headers': [ { 'key': x, 'value': y } ],
                'ip': 127.0.0.1,
                'size': 41
            }
            'history': [{
                'timestamp': ...,
            }, ...]
        }

        The 'current' key maps to a dictionary containing information
        about the value currently associated with the key, or None (null)
        if the value was recently deleted.

        The 'history' key maps to a list of dictionaries each containing
        information of past states associated with the key in question.
        """
        # Obtain set of currently active keys. Used to differentiate between
        # current and past items
        existing_keys = set(self.active_keys(session))

        # Obtain all relevant events, along with the associated value and HttpRequest.
        # Ignores 'Retrieve' events, as they do not change the associated value.
        events = session.query(Event, Value, HttpRequest)\
                         .filter(Event.action != 'Retrieve')\
                         .join(Value, Value.id == Event.value_after_id)\
                         .join(HttpRequest)

        raw_infos = dict()

        # Collect information for every event associated with a particular key
        for event, value, request in events:
            info = {
                'timestamp': str(request.timestamp),
                'headers': [
                    { 'key': header.key, 'value': header.value }
                    for header
                    in request.headers
                ],
                # TODO Header fingerprint
                'ip': request.sender,
                'size': value.size_in_bytes
            }

            entry = raw_infos.get(event.key, [])
            entry.append(info)

            raw_infos[event.key] = entry

        results = dict()

        # Build up final results dict. Sort events in descending order based on timestamp.
        for k in raw_infos.keys():
            entries = sorted(raw_infos[k],
                key=lambda i: i['timestamp'],
                reverse=True)

            if k in existing_keys:
                # The last event that touched the value associated with key `k` is located
                # at the front of the sorted entries list!
                result = {
                    'current': { **entries[0] },
                    'history': entries[1:]
                }
            else:
                result = {
                    'current': None,
                    'history': entries
                }

            results[k] = result

        return results


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
