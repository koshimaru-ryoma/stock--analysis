"""seed tickers mitsubishi corp

Revision ID: seed_tickers_mitsubishi_corp
Revises: seed_tickers
Create Date: 2026-03-05 00:01:00.000000

"""
from typing import Sequence, Union

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = 'seed_tickers_mitsubishi_corp'
down_revision: Union[str, Sequence[str], None] = 'seed_tickers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tickers_table = sa.table(
    'tickers',
    sa.column('ticker', sa.String),
    sa.column('name', sa.String),
    sa.column('is_active', sa.Boolean),
    sa.column('created_at', sa.DateTime(timezone=True)),
    sa.column('updated_at', sa.DateTime(timezone=True)),
)

SEED_DATA = [
    {'ticker': '8058.T', 'name': '三菱商事'},
]


def upgrade() -> None:
    """Seed 三菱商事."""
    now = datetime.now(timezone.utc)
    op.execute(
        insert(tickers_table).values(
            [{'is_active': True, 'created_at': now, 'updated_at': now, **row} for row in SEED_DATA]
        ).on_conflict_do_nothing(index_elements=['ticker'])
    )


def downgrade() -> None:
    """Remove 三菱商事."""
    tickers = [row['ticker'] for row in SEED_DATA]
    op.execute(
        tickers_table.delete().where(tickers_table.c.ticker.in_(tickers))
    )
