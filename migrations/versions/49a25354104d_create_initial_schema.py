"""create_initial_schema

Revision ID: 49a25354104d
Revises:
Create Date: 2026-05-17 18:38:19.999853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "49a25354104d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the runtime schema used by the application."""
    op.create_table(
        "locations",
        sa.Column("id_location", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country_code", sa.String(length=45), nullable=False),
        sa.Column("city", sa.String(length=45), nullable=False),
        sa.Column("latitude", sa.DECIMAL(9, 6), nullable=False),
        sa.Column("longitude", sa.DECIMAL(9, 6), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id_location"),
        mysql_engine="InnoDB",
    )

    op.create_table(
        "users",
        sa.Column("id_user", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("email_verified_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id_user"),
        sa.UniqueConstraint("email"),
        mysql_engine="InnoDB",
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id_email_verification_token", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_user", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("consumed_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_user"],
            ["users.id_user"],
            name="fk_email_verification_tokens_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_email_verification_token"),
        sa.UniqueConstraint("token_hash", name="uq_email_verification_tokens_token_hash"),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_email_verification_tokens_user_created",
        "email_verification_tokens",
        ["id_user", "created_at"],
    )

    op.create_table(
        "shipments",
        sa.Column("id_shipment", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dhl_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=45), nullable=False),
        sa.Column("weight", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("initial_location", sa.Integer(), nullable=False),
        sa.Column("end_location", sa.Integer(), nullable=False),
        sa.Column("current_location", sa.Integer(), nullable=True),
        sa.Column("id_user", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["initial_location"], ["locations.id_location"], name="fk_shipments_locations"),
        sa.ForeignKeyConstraint(["end_location"], ["locations.id_location"], name="fk_shipments_locations1"),
        sa.ForeignKeyConstraint(["current_location"], ["locations.id_location"], name="fk_shipments_locations2"),
        sa.ForeignKeyConstraint(["id_user"], ["users.id_user"], name="fk_shipments_users1"),
        sa.PrimaryKeyConstraint("id_shipment"),
        sa.UniqueConstraint("dhl_id"),
        mysql_engine="InnoDB",
    )

    op.create_table(
        "shipment_history",
        sa.Column("id_shipment_history", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_timestamp", sa.TIMESTAMP(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("id_shipment", sa.Integer(), nullable=False),
        sa.Column("id_location", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_location"],
            ["locations.id_location"],
            name="fk_shipment_history_locations1",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        sa.ForeignKeyConstraint(
            ["id_shipment"],
            ["shipments.id_shipment"],
            name="fk_shipment_history_shipments1",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        sa.PrimaryKeyConstraint("id_shipment_history"),
        sa.UniqueConstraint(
            "id_shipment",
            "event_timestamp",
            "status",
            "id_location",
            name="uq_shipment_history_event",
        ),
        mysql_engine="InnoDB",
    )


def downgrade() -> None:
    """Drop the runtime schema in dependency order."""
    op.drop_table("shipment_history")
    op.drop_table("shipments")
    op.drop_index("ix_email_verification_tokens_user_created", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("users")
    op.drop_table("locations")
