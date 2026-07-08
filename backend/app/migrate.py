"""轻量迁移：为已有 SQLite/PostgreSQL 库补齐新列与新表。"""

import logging

from sqlalchemy import inspect, text

from app.database import engine

logger = logging.getLogger(__name__)


def _has_column(table: str, column: str) -> bool:
    return column in {c["name"] for c in inspect(engine).get_columns(table)}


def run_migrations() -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    with engine.begin() as conn:
        if "users" in tables:
            if not _has_column("users", "invite_code"):
                conn.execute(text("ALTER TABLE users ADD COLUMN invite_code VARCHAR(16)"))
                logger.info("migration: users.invite_code added")
            if not _has_column("users", "invited_by_id"):
                conn.execute(text("ALTER TABLE users ADD COLUMN invited_by_id INTEGER"))
                logger.info("migration: users.invited_by_id added")

        if "app_settings" not in tables:
            # create_all 会建表；此处仅兜底 SQLite 旧库
            pass
