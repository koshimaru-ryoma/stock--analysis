"""seed tickers

Revision ID: seed_tickers
Revises: 48b9ce647bd9
Create Date: 2026-03-05 00:00:00.000000

"""
from typing import Sequence, Union

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = 'seed_tickers'
down_revision: Union[str, Sequence[str], None] = '48b9ce647bd9'
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
    {'ticker': '8001.T', 'name': '伊藤忠商事'},
    {'ticker': '8002.T', 'name': '丸紅'},
    {'ticker': '7011.T', 'name': '三菱重工業'},
    {'ticker': '5016.T', 'name': 'JX金属'},
    {'ticker': '7013.T', 'name': 'IHI'},
]


def upgrade() -> None:
    """Seed tickers master data."""
    now = datetime.now(timezone.utc)
    op.execute(
        insert(tickers_table).values(
            [{'is_active': True, 'created_at': now, 'updated_at': now, **row} for row in SEED_DATA]
        ).on_conflict_do_nothing(index_elements=['ticker'])
    )


def downgrade() -> None:
    """Remove seeded tickers."""
    tickers = [row['ticker'] for row in SEED_DATA]
    op.execute(
        tickers_table.delete().where(tickers_table.c.ticker.in_(tickers))
    )
