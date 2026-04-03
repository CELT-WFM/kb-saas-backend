from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.sql import func
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_sub_id = Column(String)
    status = Column(String)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    s3_key = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))
    collection_id = Column(Integer, ForeignKey("collections.id"))
    file_type = Column(String)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    content = Column(Text)
    embedding = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)

class WebsiteSource(Base):
    __tablename__ = "website_sources"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    crawl_depth = Column(Integer, default=2)
    refresh_days = Column(Integer, default=3)
    last_crawled = Column(DateTime(timezone=True), nullable=True)
