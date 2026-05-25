"""
初始迁移 - 创建所有表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 UUID 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # 用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('status', sa.SmallInteger, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # API Key 表
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(100)),
        sa.Column('permissions', postgresql.JSONB),
        sa.Column('rate_limit', sa.Integer),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
    )
    
    # 会话表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(200)),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('status', sa.SmallInteger, default=1),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # 消息表
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tokens', sa.Integer),
        sa.Column('model', sa.String(50)),
        sa.Column('provider', sa.String(50)),
        sa.Column('latency_ms', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # 模型配置表
    op.create_table(
        'model_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider', sa.String(50), nullable=False, index=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('api_endpoint', sa.String(500)),
        sa.Column('api_key_encrypted', sa.Text),
        sa.Column('rate_limit', sa.Integer),
        sa.Column('cost_per_1k_tokens', sa.DECIMAL(10, 6)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('weight', sa.Integer, default=1),
        sa.Column('config', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 使用记录表
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id')),
        sa.Column('model', sa.String(50)),
        sa.Column('provider', sa.String(50)),
        sa.Column('prompt_tokens', sa.Integer),
        sa.Column('completion_tokens', sa.Integer),
        sa.Column('total_tokens', sa.Integer),
        sa.Column('cost', sa.DECIMAL(10, 6)),
        sa.Column('status', sa.SmallInteger),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('usage_records')
    op.drop_table('model_configs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('api_keys')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
