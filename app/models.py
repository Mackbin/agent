"""
数据模型定义
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, SmallInteger, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(SmallInteger, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user")


class APIKey(Base):
    """API Key 表"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100))
    permissions = Column(JSONB)
    rate_limit = Column(Integer)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # 关系
    user = relationship("User", back_populates="api_keys")


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200))
    model = Column(String(50), nullable=False)
    status = Column(SmallInteger, default=1)  # 1: active, 0: archived
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens = Column(Integer)
    model = Column(String(50))
    provider = Column(String(50))
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class ModelConfig(Base):
    """模型配置表"""
    __tablename__ = "model_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    api_endpoint = Column(String(500))
    api_key_encrypted = Column(Text)
    rate_limit = Column(Integer)
    cost_per_1k_tokens = Column(DECIMAL(10, 6))
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    weight = Column(Integer, default=1)
    config = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UsageRecord(Base):
    """使用记录表"""
    __tablename__ = "usage_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    model = Column(String(50))
    provider = Column(String(50))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(DECIMAL(10, 6))
    status = Column(SmallInteger)  # 1: success, 0: failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="usage_records")
