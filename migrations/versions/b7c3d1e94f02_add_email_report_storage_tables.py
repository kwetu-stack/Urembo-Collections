"""Add email report storage tables

Revision ID: b7c3d1e94f02
Revises: a4af274f9be0
Create Date: 2026-08-07 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7c3d1e94f02"
down_revision = "a4af274f9be0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("rows_imported", sa.Integer(), nullable=True),
        sa.Column("rows_updated", sa.Integer(), nullable=True),
        sa.Column("import_status", sa.String(length=50), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_reports_gmail_message_id"),
        "email_reports",
        ["gmail_message_id"],
        unique=False,
    )

    op.create_table(
        "processed_email_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=False),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("imported", sa.Integer(), nullable=True),
        sa.Column("updated", sa.Integer(), nullable=True),
        sa.Column("skipped", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_processed_email_messages_gmail_message_id"),
        "processed_email_messages",
        ["gmail_message_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_processed_email_messages_gmail_message_id"),
        table_name="processed_email_messages",
    )
    op.drop_table("processed_email_messages")
    op.drop_index(
        op.f("ix_email_reports_gmail_message_id"),
        table_name="email_reports",
    )
    op.drop_table("email_reports")
