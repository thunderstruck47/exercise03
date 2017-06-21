"""empty message

Revision ID: 819f88815e08
Revises: eb9db9d49bc4
Create Date: 2017-06-21 16:27:06.265926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '819f88815e08'
down_revision = 'eb9db9d49bc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('addresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('country', sa.String(length=50), nullable=True),
    sa.Column('county', sa.String(length=80), nullable=True),
    sa.Column('city', sa.String(length=80), nullable=True),
    sa.Column('postcode', sa.String(length=16), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('adresses')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('adresses',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('country', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('county', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('city', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('postcode', sa.VARCHAR(length=16), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='adresses_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='adresses_pkey')
    )
    op.drop_table('addresses')
    # ### end Alembic commands ###
