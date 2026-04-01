"""Initial Migration

Revision ID: 465a82af37c9
Revises: 
Create Date: 2026-03-02 09:33:14.659607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '465a82af37c9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reset_code', sa.String(6), nullable=True),
        sa.Column('reset_code_expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feedback_level', sa.String(50), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=True, default=0),
        sa.Column('role_applied_for', sa.String(100), nullable=True),
    )
    op.create_index('idx_user_created_at', 'interviews', ['user_id', sa.text('created_at DESC')], unique=False)

    # Create question_answers table
    op.create_table(
        'question_answers',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('interview_id', sa.Integer(), sa.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('improvements', sa.Text(), nullable=True),
        sa.Column('suggestions', sa.Text(), nullable=True),
    )

    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('interview_id', sa.Integer(), sa.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_name', sa.String(150), nullable=False),
        sa.Column('category_score', sa.Integer(), nullable=True),
        sa.Column('total_questions_per_category', sa.Integer(), nullable=True, default=0),
    )

    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_name', sa.String(120), nullable=True),
        sa.Column('job_title', sa.String(120), nullable=True),
        sa.Column('location', sa.String(120), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_photo_url', sa.String(255), nullable=True),
        sa.Column('skills_json', sa.Text(), nullable=True),
        sa.Column('previous_role', sa.String(100), nullable=True),
        sa.Column('target_role', sa.String(100), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('user_profiles')
    op.drop_table('skills')
    op.drop_table('question_answers')
    op.drop_index('idx_user_created_at', table_name='interviews')
    op.drop_table('interviews')
    op.drop_table('users')
