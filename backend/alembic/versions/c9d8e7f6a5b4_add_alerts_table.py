"""add alerts table

Revision ID: c9d8e7f6a5b4
Revises: ba7534c97335
Create Date: 2026-07-20 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c9d8e7f6a5b4'
down_revision = 'ba7534c97335'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('bopa_match_id', sa.Integer(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('NEW', 'VIEWED', 'DISCARDED', name='alertstatus'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bopa_match_id'], ['bopa_matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bopa_match_id', name='uq_alert_bopa_match'),
    )
    op.create_index(op.f('ix_alerts_bopa_match_id'), 'alerts', ['bopa_match_id'], unique=False)
    op.create_index(op.f('ix_alerts_customer_id'), 'alerts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_alerts_user_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_customer_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_bopa_match_id'), table_name='alerts')
    op.drop_table('alerts')
    sa.Enum(name='alertstatus').drop(op.get_bind(), checkfirst=True)
