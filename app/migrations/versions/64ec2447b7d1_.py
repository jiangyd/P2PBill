"""empty message

Revision ID: 64ec2447b7d1
Revises: 17cc87e3e47b
Create Date: 2017-10-23 12:30:42.408827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64ec2447b7d1'
down_revision = '17cc87e3e47b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('loginlog', sa.Column('mfa_status', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('mfa_status', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('secret', sa.String(length=16), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'secret')
    op.drop_column('user', 'mfa_status')
    op.drop_column('loginlog', 'mfa_status')
    # ### end Alembic commands ###