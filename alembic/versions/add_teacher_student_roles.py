"""add teacher student roles

Revision ID: add_teacher_student
Revises: 3f8a9b2c1d5e
Create Date: 2026-04-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_teacher_student'
down_revision = '3f8a9b2c1d5e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to users table
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='student'))
    
    # Create course_enrollments table for student enrollment requests
    op.create_table('course_enrollments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, approved, rejected
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'student_id', name='unique_enrollment')
    )
    
    # Create index for faster queries
    op.create_index('ix_enrollments_course', 'course_enrollments', ['course_id'])
    op.create_index('ix_enrollments_student', 'course_enrollments', ['student_id'])
    op.create_index('ix_enrollments_status', 'course_enrollments', ['status'])


def downgrade() -> None:
    op.drop_index('ix_enrollments_status', table_name='course_enrollments')
    op.drop_index('ix_enrollments_student', table_name='course_enrollments')
    op.drop_index('ix_enrollments_course', table_name='course_enrollments')
    op.drop_table('course_enrollments')
    op.drop_column('users', 'role')
