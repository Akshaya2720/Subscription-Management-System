"""add_currency_and_notes_to_invoices_and_is_default_to_tax_rules

Revision ID: a35f4150388e
Revises: 716f12bb5710
Create Date: 2026-10-31 15:53:01.761955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a35f4150388e'
down_revision: Union[str, Sequence[str], None] = '716f12bb5710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'users' in tables:
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        with op.batch_alter_table('users') as batch_op:
            if 'updated_at' not in user_cols:
                batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    if 'tax_rules' in tables:
        tax_cols = [c['name'] for c in inspector.get_columns('tax_rules')]
        with op.batch_alter_table('tax_rules') as batch_op:
            if 'is_default' not in tax_cols:
                batch_op.add_column(sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'))

    if 'invoices' in tables:
        inv_cols = [c['name'] for c in inspector.get_columns('invoices')]
        with op.batch_alter_table('invoices') as batch_op:
            if 'currency' not in inv_cols:
                batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'))
            if 'notes' not in inv_cols:
                batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))

    if 'payments' in tables:
        pay_cols = [c['name'] for c in inspector.get_columns('payments')]
        with op.batch_alter_table('payments') as batch_op:
            if 'notes' not in pay_cols:
                batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'invoices' in tables:
        inv_cols = [c['name'] for c in inspector.get_columns('invoices')]
        with op.batch_alter_table('invoices') as batch_op:
            if 'notes' in inv_cols:
                batch_op.drop_column('notes')
            if 'currency' in inv_cols:
                batch_op.drop_column('currency')

    if 'users' in tables:
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        with op.batch_alter_table('users') as batch_op:
            if 'updated_at' not in user_cols:
                batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    if 'tax_rules' in tables:
        tax_cols = [c['name'] for c in inspector.get_columns('tax_rules')]
        with op.batch_alter_table('tax_rules') as batch_op:
            if 'is_default' in tax_cols:
                batch_op.drop_column('is_default')
