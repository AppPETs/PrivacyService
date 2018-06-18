"""Classes used by the application. This module contains only their definitions.
To actually map these classes to their database equivalent, database.py is used,
which creates a database and initialises these definitions used here (via 
initiate_data_definitions)"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Table, UniqueConstraint, Integer, String, LargeBinary, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


class Value(Base):
    __tablename__ = 'values'

    id       = Column(Integer, primary_key=True, unique=True)
    blob     = Column(LargeBinary, unique=True)

    @property
    def size_in_bytes(self):
        return len(self.blob)

    def __repr__(self):
        return '<Value: length=%d>' % (len(self.blob))


class Entry(Base):
    __tablename__ = 'entries'

    id    = Column(Integer, primary_key=True, unique=True)
    # Key sizes are not enforced in the database. This is not necessary,
    # because the application itself enforces only legal keys are ever
    # saved in the database and because this would complicate the data
    # definitions here significantly and would create duplicate lots of
    # code.
    key   = Column(String(255), unique=True)

    value_id = Column(Integer, ForeignKey('values.id'))
    value = relationship('Value')

    def __repr__(self):
        return '<Entry(key=%s, len(value)=%d>' % (self.key, self.value.size_in_bytes)

# Metadata for many-to-many association between HttpRequest and HttpHeader
association_table = Table('association', Base.metadata,
    Column('request_id', Integer, ForeignKey('http_requests.id')),
    Column('header_id',  Integer, ForeignKey('http_headers.id'))
)

class HttpHeader(Base):
    __tablename__ = 'http_headers'

    id      = Column(Integer, primary_key=True, unique=True)
    key     = Column(String(255))
    value   = Column(String)

    __table_args__ = (UniqueConstraint('key', 'value', name = 'header_pair_unique'), )

    def __repr__(self):
        return '<HTTPHeader(key=%s, value=%s)>' % (self.key, self.value)


class HttpRequest(Base):
    __tablename__ = 'http_requests'

    id          = Column(Integer, primary_key = True, unique = True)
    timestamp   = Column(DateTime)
    sender      = Column(String(255))

    headers     = relationship('HttpHeader', secondary = association_table)

    def __repr__(self):
        return '<HTTPRequest(timestamp=%s, sender=%s, headers=%s>' % (
            self.timestamp,
            self.sender,
            self.headers)


class Event(Base):
    __tablename__ = 'events'

    id          = Column(Integer, primary_key=True, unique=True)
    action      = Column(Enum('Update', 'Retrieve', 'Delete',
                  name = 'action_enum', nullable = False))
    
    request_id  = Column(Integer, ForeignKey('http_requests.id'))
    request     = relationship('HttpRequest')

    # See above, correct key format is enforced by the application.
    key         = Column(String(255))

    value_before_id = Column(Integer, ForeignKey('values.id'), nullable=True)
    value_before    = relationship('Value', foreign_keys=value_before_id)

    value_after_id  = Column(Integer, ForeignKey('values.id'), nullable=True)
    value_after     = relationship('Value', foreign_keys=value_after_id)


def initiate_data_definitions(engine):
    """Initiates the database.
    To be called from database.py to finish initialisation"""
    Base.metadata.create_all(engine)

