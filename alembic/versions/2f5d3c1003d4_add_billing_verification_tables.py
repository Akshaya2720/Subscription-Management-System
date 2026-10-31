"""add billing verification tables

Revision ID: 2f5d3c1003d4
Revises: 127056ed81a1
Create Date: 2026-10-31 12:46:36.842426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f5d3c1003d4'
down_revision: Union[str, Sequence[str], None] = '127056ed81a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with all billing, financial verification, AI and audit tables."""
    # 1. Update invoices table
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('billing_period_start', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('billing_period_end', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'))
        batch_op.add_column(sa.Column('amount_paid', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('amount_due', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('invoice_type', sa.String(length=30), nullable=False, server_default='RECURRING'))
        batch_op.add_column(sa.Column('pdf_path', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        batch_op.create_unique_constraint('uq_invoice_sub_period_type', ['organization_id', 'subscription_id', 'billing_period_start', 'billing_period_end', 'invoice_type'])

    # 2. Update payments table
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column('payment_reference', sa.String(length=100), nullable=False, server_default='PAY-LEGACY'))
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.alter_column('invoice_id', existing_type=sa.Uuid(), nullable=True)
        batch_op.create_index(batch_op.f('ix_payments_customer_id'), ['customer_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_payments_payment_reference'), ['payment_reference'], unique=False)

    # 3. Create invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=True),
        sa.Column('variant_id', sa.Uuid(), nullable=True),
        sa.Column('description_snapshot', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('line_total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)

    # 4. Create billing_runs & billing_run_items
    op.create_table(
        'billing_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('run_reference', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('total_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('logs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_runs_organization_id'), 'billing_runs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_billing_runs_run_reference'), 'billing_runs', ['run_reference'], unique=True)

    op.create_table(
        'billing_run_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('billing_run_id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['billing_run_id'], ['billing_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_run_items_billing_run_id'), 'billing_run_items', ['billing_run_id'], unique=False)
    op.create_index(op.f('ix_billing_run_items_subscription_id'), 'billing_run_items', ['subscription_id'], unique=False)

    # 5. Create tax_rules
    op.create_table(
        'tax_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('tax_type', sa.String(length=50), nullable=False, server_default='GST'),
        sa.Column('inclusive_or_exclusive', sa.String(length=20), nullable=False, server_default='EXCLUSIVE'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_rules_organization_id'), 'tax_rules', ['organization_id'], unique=False)

    # 6. Create discounts & discount_redemptions
    op.create_table(
        'discounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('discount_name', sa.String(length=100), nullable=False),
        sa.Column('discount_code', sa.String(length=50), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('minimum_purchase', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('minimum_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('product_id', sa.Uuid(), nullable=True),
        sa.Column('subscription_wide', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discounts_organization_id'), 'discounts', ['organization_id'], unique=False)
    op.create_index(op.f('ix_discounts_discount_code'), 'discounts', ['discount_code'], unique=False)

    op.create_table(
        'discount_redemptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('discount_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('customer_id', sa.Uuid(), nullable=False),
        sa.Column('amount_applied', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discount_redemptions_discount_id'), 'discount_redemptions', ['discount_id'], unique=False)

    # 7. Create payment_allocations & payment_refunds
    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('amount_allocated', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('allocated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_allocations_payment_id'), 'payment_allocations', ['payment_id'], unique=False)
    op.create_index(op.f('ix_payment_allocations_invoice_id'), 'payment_allocations', ['invoice_id'], unique=False)

    op.create_table(
        'payment_refunds',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_id', sa.Uuid(), nullable=False),
        sa.Column('refund_reference', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('refund_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_refunds_payment_id'), 'payment_refunds', ['payment_id'], unique=False)
    op.create_index(op.f('ix_payment_refunds_refund_reference'), 'payment_refunds', ['refund_reference'], unique=True)

    # 8. Create reconciliation_runs & reconciliation_items
    op.create_table(
        'reconciliation_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('run_reference', sa.String(length=100), nullable=False),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matched_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unmatched_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discrepancy_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING_REVIEW'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_runs_organization_id'), 'reconciliation_runs', ['organization_id'], unique=False)

    op.create_table(
        'reconciliation_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('reconciliation_run_id', sa.Uuid(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('matched_payment_id', sa.Uuid(), nullable=True),
        sa.Column('matched_invoice_id', sa.Uuid(), nullable=True),
        sa.Column('match_status', sa.String(length=40), nullable=False, server_default='UNMATCHED'),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reconciliation_run_id'], ['reconciliation_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['matched_invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_items_reconciliation_run_id'), 'reconciliation_items', ['reconciliation_run_id'], unique=False)

    # 9. Create contracts & service verification tables
    op.create_table(
        'contracts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('contract_reference', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('document_reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_organization_id'), 'contracts', ['organization_id'], unique=False)
    op.create_index(op.f('ix_contracts_contract_reference'), 'contracts', ['contract_reference'], unique=True)

    op.create_table(
        'service_commitments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('contract_id', sa.Uuid(), nullable=False),
        sa.Column('commitment_type', sa.String(length=50), nullable=False),
        sa.Column('expected_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('measurement_unit', sa.String(length=30), nullable=False),
        sa.Column('verification_rule', sa.String(length=30), nullable=False, server_default='GREATER_OR_EQUAL'),
        sa.Column('penalty_rate_per_unit', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_commitments_contract_id'), 'service_commitments', ['contract_id'], unique=False)

    op.create_table(
        'service_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('commitment_id', sa.Uuid(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actual_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('evidence_reference', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='MONITORING_SYSTEM'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='VERIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['commitment_id'], ['service_commitments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_events_subscription_id'), 'service_events', ['subscription_id'], unique=False)

    op.create_table(
        'verification_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('contract_id', sa.Uuid(), nullable=False),
        sa.Column('run_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('overall_result', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_runs_subscription_id'), 'verification_runs', ['subscription_id'], unique=False)

    op.create_table(
        'verification_results',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('verification_run_id', sa.Uuid(), nullable=False),
        sa.Column('commitment_id', sa.Uuid(), nullable=False),
        sa.Column('expected_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('actual_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('variance', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evidence_reference', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['verification_run_id'], ['verification_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['commitment_id'], ['service_commitments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_results_verification_run_id'), 'verification_results', ['verification_run_id'], unique=False)

    op.create_table(
        'service_credits',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('verification_result_id', sa.Uuid(), nullable=False),
        sa.Column('proposed_credit', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('approved_credit', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PROPOSED'),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('approval_reason', sa.Text(), nullable=True),
        sa.Column('applied_invoice_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verification_result_id'], ['verification_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applied_invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_credits_subscription_id'), 'service_credits', ['subscription_id'], unique=False)

    # 10. Create invoice_anomalies & audit_events
    op.create_table(
        'invoice_anomalies',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('anomaly_type', sa.String(length=60), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('detected_value', sa.String(length=255), nullable=False),
        sa.Column('expected_value', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('detection_method', sa.String(length=50), nullable=False, server_default='RULE_BASED'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DETECTED'),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_anomalies_organization_id'), 'invoice_anomalies', ['organization_id'], unique=False)
    op.create_index(op.f('ix_invoice_anomalies_invoice_id'), 'invoice_anomalies', ['invoice_id'], unique=False)

    op.create_table(
        'audit_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('change_summary', sa.Text(), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('current_hash', sa.String(length=64), nullable=False),
        sa.Column('is_anchored', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('blockchain_tx_hash', sa.String(length=100), nullable=True),
        sa.Column('blockchain_network', sa.String(length=50), nullable=True),
        sa.Column('anchored_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_organization_id'), 'audit_events', ['organization_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('audit_events')
    op.drop_table('invoice_anomalies')
    op.drop_table('service_credits')
    op.drop_table('verification_results')
    op.drop_table('verification_runs')
    op.drop_table('service_events')
    op.drop_table('service_commitments')
    op.drop_table('contracts')
    op.drop_table('reconciliation_items')
    op.drop_table('reconciliation_runs')
    op.drop_table('payment_refunds')
    op.drop_table('payment_allocations')
    op.drop_table('discount_redemptions')
    op.drop_table('discounts')
    op.drop_table('tax_rules')
    op.drop_table('billing_run_items')
    op.drop_table('billing_runs')
    op.drop_table('invoice_items')
