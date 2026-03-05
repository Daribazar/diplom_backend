"""Add pgvector extension and embeddings table

Revision ID: 20260305_214321
Revises: 
Create Date: 2026-03-05 21:43:21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '20260305_214321'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create lecture_embeddings table
    op.create_table(
        'lecture_embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('lecture_id', sa.String(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_lecture_embeddings_lecture_id', 'lecture_embeddings', ['lecture_id'])
    
    # Create foreign key
    op.create_foreign_key(
        'fk_lecture_embeddings_lecture_id',
        'lecture_embeddings',
        'lectures',
        ['lecture_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_table('lecture_embeddings')
    op.execute('DROP EXTENSION IF EXISTS vector')
