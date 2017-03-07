"""add poportrait support

Revision ID: 35b51cd6ef67
Revises: 49709c1c1b5a
Create Date: 2016-01-17 15:29:13.603227

"""

# revision identifiers, used by Alembic.
revision = '35b51cd6ef67'
down_revision = '49709c1c1b5a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('portrait_addr', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'portrait_addr')
    ### end Alembic commands ###
