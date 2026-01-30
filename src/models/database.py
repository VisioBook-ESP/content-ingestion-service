# src/models/database.py

import uuid
from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


class GUID(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class JSONType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Content(Base):
    __tablename__ = "content"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    content_metadata = Column(JSONType, nullable=True)
