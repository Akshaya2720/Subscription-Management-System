"""normalize_3nf_billing_tax_discounts_and_verification

Revision ID: 716f12bb5710
Revises: 127056ed81a1
Create Date: 2026-10-31 15:17:33.157701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '716f12bb5710'
down_revision: Union[str, Sequence[str], None] = '127056ed81a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Organization Settings
    if 'organization_settings' not in tables:
        op.create_table(
            'organization_settings',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('default_currency', sa.String(length=10), nullable=False, server_default='USD'),
            sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
            sa.Column('dunning_max_retries', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('dunning_retry_interval_days', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', name='uq_org_settings_organization_id')
        )
        op.create_index(op.f('ix_organization_settings_organization_id'), 'organization_settings', ['organization_id'], unique=True)

    # 2. Customer Addresses & Contacts
    if 'customer_addresses' not in tables:
        op.create_table(
            'customer_addresses',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('customer_id', sa.Uuid(), nullable=False),
            sa.Column('address_type', sa.String(length=20), nullable=False, server_default='BILLING'),
            sa.Column('street', sa.String(length=255), nullable=False),
            sa.Column('city', sa.String(length=100), nullable=False),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('postal_code', sa.String(length=20), nullable=False),
            sa.Column('country', sa.String(length=100), nullable=False, server_default='United States'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_customer_addresses_customer_id'), 'customer_addresses', ['customer_id'], unique=False)

    if 'customer_contacts' not in tables:
        op.create_table(
            'customer_contacts',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('customer_id', sa.Uuid(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('designation', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_customer_contacts_customer_id'), 'customer_contacts', ['customer_id'], unique=False)

    # 3. Security Tokens (Password Reset & Refresh Tokens)
    if 'password_reset_tokens' not in tables:
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'], unique=True)
        op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)
        op.create_index(op.f('ix_password_reset_tokens_expires_at'), 'password_reset_tokens', ['expires_at'], unique=False)

    if 'refresh_tokens' not in tables:
        op.create_table(
            'refresh_tokens',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('token_hash', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
        op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
        op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)

    # 4. Tax Rules & Discounts
    if 'tax_rules' not in tables:
        op.create_table(
            'tax_rules',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('tax_type', sa.String(length=50), nullable=False, server_default='VAT'),
            sa.Column('rate_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('country_code', sa.String(length=10), nullable=False, server_default='US'),
            sa.Column('state_or_province', sa.String(length=100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'name', name='uq_org_tax_rule_name'),
            sa.CheckConstraint('rate_percentage >= 0 AND rate_percentage <= 100', name='ck_tax_rate_percent_range')
        )
        op.create_index('ix_tax_rules_org_active', 'tax_rules', ['organization_id', 'is_active'], unique=False)

    if 'discounts' not in tables:
        op.create_table(
            'discounts',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('discount_type', sa.String(length=20), nullable=False, server_default='PERCENTAGE'),
            sa.Column('discount_value', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('min_purchase_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('min_quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('max_uses', sa.Integer(), nullable=True),
            sa.Column('times_used', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('product_id', sa.Uuid(), nullable=True),
            sa.Column('applies_to_subscription', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'code', name='uq_org_discount_code'),
            sa.CheckConstraint('discount_value >= 0', name='ck_discount_value_nonneg'),
            sa.CheckConstraint('min_purchase_amount >= 0', name='ck_discount_min_purchase_nonneg'),
            sa.CheckConstraint('min_quantity >= 1', name='ck_discount_min_qty_pos'),
            sa.CheckConstraint('times_used >= 0', name='ck_discount_times_used_nonneg'),
            sa.CheckConstraint('max_uses IS NULL OR max_uses > 0', name='ck_discount_max_uses_pos'),
            sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_discount_date_order')
        )
        op.create_index('ix_discounts_org_code_active', 'discounts', ['organization_id', 'code', 'is_active'], unique=False)

    # 5. Quotation Templates
    if 'quotation_templates' not in tables:
        op.create_table(
            'quotation_templates',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('plan_id', sa.Uuid(), nullable=False),
            sa.Column('default_valid_days', sa.Integer(), nullable=False, server_default='30'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'name', name='uq_org_quotation_template_name'),
            sa.CheckConstraint('default_valid_days > 0', name='ck_template_valid_days_pos')
        )
        op.create_index(op.f('ix_quotation_templates_organization_id'), 'quotation_templates', ['organization_id'], unique=False)

    if 'quotation_template_items' not in tables:
        op.create_table(
            'quotation_template_items',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('template_id', sa.Uuid(), nullable=False),
            sa.Column('product_id', sa.Uuid(), nullable=False),
            sa.Column('variant_id', sa.Uuid(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['template_id'], ['quotation_templates.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.CheckConstraint('quantity > 0', name='ck_template_item_qty_pos')
        )
        op.create_index(op.f('ix_quotation_template_items_template_id'), 'quotation_template_items', ['template_id'], unique=False)

    # 6. Invoice Line Items & Status History
    if 'invoice_items' not in tables:
        op.create_table(
            'invoice_items',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('invoice_id', sa.Uuid(), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.CheckConstraint('quantity > 0', name='ck_inv_item_qty_pos'),
            sa.CheckConstraint('unit_price >= 0', name='ck_inv_item_unit_price_nonneg'),
            sa.CheckConstraint('line_total >= 0', name='ck_inv_item_line_total_nonneg')
        )
        op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)

    if 'invoice_status_history' not in tables:
        op.create_table(
            'invoice_status_history',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('invoice_id', sa.Uuid(), nullable=False),
            sa.Column('from_status', sa.String(length=50), nullable=True),
            sa.Column('to_status', sa.String(length=50), nullable=False),
            sa.Column('changed_by_user_id', sa.Uuid(), nullable=True),
            sa.Column('reason', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_invoice_status_history_invoice_id'), 'invoice_status_history', ['invoice_id'], unique=False)

    # 7. Verification Contracts & Audit Trail
    if 'verification_contracts' not in tables:
        op.create_table(
            'verification_contracts',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('contract_number', sa.String(length=50), nullable=False),
            sa.Column('subscription_id', sa.Uuid(), nullable=False),
            sa.Column('service_name', sa.String(length=255), nullable=False),
            sa.Column('sla_commitment_description', sa.String(length=255), nullable=False),
            sa.Column('target_uptime_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='99.99'),
            sa.Column('actual_recorded_telemetry', sa.String(length=255), nullable=False),
            sa.Column('breach_detected', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('proposed_credit_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING_REVIEW'),
            sa.Column('adjudicated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('adjudicated_by', sa.Uuid(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['adjudicated_by'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'contract_number', name='uq_org_contract_number'),
            sa.CheckConstraint('target_uptime_percentage >= 0 AND target_uptime_percentage <= 100', name='ck_verification_uptime_range'),
            sa.CheckConstraint('proposed_credit_amount >= 0', name='ck_proposed_credit_nonneg')
        )
        op.create_index('ix_verification_org_breach_status', 'verification_contracts', ['organization_id', 'breach_detected', 'status'], unique=False)

    if 'audit_logs' not in tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('organization_id', sa.Uuid(), nullable=False),
            sa.Column('sequence_number', sa.Integer(), nullable=False),
            sa.Column('previous_hash', sa.String(length=64), nullable=False),
            sa.Column('current_hash', sa.String(length=64), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.String(length=100), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('actor_email', sa.String(length=255), nullable=False),
            sa.Column('payload_json', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'sequence_number', name='uq_org_audit_seq')
        )
        op.create_index('ix_audit_org_entity', 'audit_logs', ['organization_id', 'entity_type', 'entity_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_current_hash'), 'audit_logs', ['current_hash'], unique=False)

    # 8. Schema Upgrades & Indexing on Existing Tables
    def has_index(table_name, index_name):
        try:
            return any(idx['name'] == index_name for idx in inspector.get_indexes(table_name))
        except Exception:
            return False

    def has_uq(table_name, uq_name):
        try:
            return any(uq['name'] == uq_name for uq in inspector.get_unique_constraints(table_name))
        except Exception:
            return False

    # Customers
    cust_cols = [c['name'] for c in inspector.get_columns('customers')]
    with op.batch_alter_table('customers') as batch_op:
        if 'shipping_address' not in cust_cols:
            batch_op.add_column(sa.Column('shipping_address', sa.String(length=500), nullable=True))
        if not has_index('customers', 'ix_customers_org_status'):
            batch_op.create_index('ix_customers_org_status', ['organization_id', 'status'], unique=False)

    # Invoices
    inv_cols = [c['name'] for c in inspector.get_columns('invoices')]
    with op.batch_alter_table('invoices') as batch_op:
        if 'period_start' not in inv_cols:
            batch_op.add_column(sa.Column('period_start', sa.Date(), nullable=True))
        if 'period_end' not in inv_cols:
            batch_op.add_column(sa.Column('period_end', sa.Date(), nullable=True))
        if 'sla_credit_amount' not in inv_cols:
            batch_op.add_column(sa.Column('sla_credit_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        if 'amount_paid' not in inv_cols:
            batch_op.add_column(sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        if 'amount_due' not in inv_cols:
            batch_op.add_column(sa.Column('amount_due', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        if not has_index('invoices', 'ix_invoices_org_status_due'):
            batch_op.create_index('ix_invoices_org_status_due', ['organization_id', 'status', 'due_date'], unique=False)
        if not has_uq('invoices', 'uq_invoice_subscription_period'):
            batch_op.create_unique_constraint('uq_invoice_subscription_period', ['subscription_id', 'period_start', 'period_end'])

    # Subscription Plans
    plan_cols = [c['name'] for c in inspector.get_columns('subscription_plans')]
    with op.batch_alter_table('subscription_plans') as batch_op:
        if 'is_auto_close_at_end' not in plan_cols:
            batch_op.add_column(sa.Column('is_auto_close_at_end', sa.Boolean(), nullable=False, server_default='0'))
        if 'is_closable_early' not in plan_cols:
            batch_op.add_column(sa.Column('is_closable_early', sa.Boolean(), nullable=False, server_default='1'))
        if 'is_pausable' not in plan_cols:
            batch_op.add_column(sa.Column('is_pausable', sa.Boolean(), nullable=False, server_default='1'))
        if 'is_renewable' not in plan_cols:
            batch_op.add_column(sa.Column('is_renewable', sa.Boolean(), nullable=False, server_default='1'))
        if not has_index('subscription_plans', 'ix_plans_org_status'):
            batch_op.create_index('ix_plans_org_status', ['organization_id', 'status'], unique=False)

    # Subscriptions
    sub_cols = [c['name'] for c in inspector.get_columns('subscriptions')]
    with op.batch_alter_table('subscriptions') as batch_op:
        if 'recurring_amount' not in sub_cols:
            batch_op.add_column(sa.Column('recurring_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        if not has_index('subscriptions', 'ix_subscriptions_billing_due'):
            batch_op.create_index('ix_subscriptions_billing_due', ['organization_id', 'next_billing_date', 'status'], unique=False)
        if not has_index('subscriptions', 'ix_subscriptions_org_status'):
            batch_op.create_index('ix_subscriptions_org_status', ['organization_id', 'status'], unique=False)

    # Users
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    with op.batch_alter_table('users') as batch_op:
        if 'password_hash' not in user_cols:
            batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=False, server_default='default_hash'))
        if 'customer_id' not in user_cols:
            batch_op.add_column(sa.Column('customer_id', sa.Uuid(), nullable=True))
        if 'is_verified' not in user_cols:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='1'))
        if not has_index('users', 'ix_users_org_role'):
            batch_op.create_index('ix_users_org_role', ['organization_id', 'role'], unique=False)


def downgrade() -> None:
    pass
