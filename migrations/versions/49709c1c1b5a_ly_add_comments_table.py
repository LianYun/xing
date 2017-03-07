"""ly: add comments table

Revision ID: 49709c1c1b5a
Revises: 17c417d64da4
Create Date: 2015-12-20 17:54:58.498944

"""

# revision identifiers, used by Alembic.
revision = '49709c1c1b5a'
down_revision = '17c417d64da4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('body_html', sa.Text(), nullable=True),
    sa.Column('time_stamp', sa.DateTime(), nullable=True),
    sa.Column('disabled', sa.Boolean(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('conference_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['conference_id'], ['conferences.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_time_stamp'), 'comments', ['time_stamp'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_comments_time_stamp'), table_name='comments')
    op.drop_table('comments')
    ### end Alembic commands ###
