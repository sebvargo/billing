"""sent status

Revision ID: d638cb522607
Revises: 9323fcfcb584
Create Date: 2024-04-27 18:28:18.300816

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd638cb522607'
down_revision = '9323fcfcb584'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sent', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.drop_column('sent')

    # ### end Alembic commands ###
