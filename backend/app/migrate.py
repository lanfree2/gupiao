"""轻量迁移：为已有 SQLite/PostgreSQL 库补齐新列与新表。"""

import logging

from sqlalchemy import inspect, text

from app.database import engine

logger = logging.getLogger(__name__)


def _has_column(table: str, column: str) -> bool:
    return column in {c["name"] for c in inspect(engine).get_columns(table)}


def _bool_column_def() -> str:
    """PostgreSQL 要求 BOOLEAN 默认值为 false，不能用 0。"""
    if engine.dialect.name == "postgresql":
        return "BOOLEAN DEFAULT false"
    return "BOOLEAN DEFAULT 0"


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
            if not _has_column("users", "can_view_invitee_channels"):
                conn.execute(text(f"ALTER TABLE users ADD COLUMN can_view_invitee_channels {_bool_column_def()}"))
                logger.info("migration: users.can_view_invitee_channels added")

        if "user_periods" in tables:
            if not _has_column("user_periods", "unit"):
                conn.execute(text("ALTER TABLE user_periods ADD COLUMN unit VARCHAR(16) DEFAULT 'trading_day'"))
                logger.info("migration: user_periods.unit added")
            rows = conn.execute(text("SELECT id, label, days, unit FROM user_periods")).fetchall()
            for row in rows:
                pid, label, days, unit = row[0], row[1] or "", row[2] or 1, row[3]
                from app.services.period_calc import infer_unit_from_label, normalize_period_unit, suggest_label

                new_label = label
                if label.endswith("日") and not label.endswith("交易日"):
                    new_label = label[:-1] + "交易日"
                elif label.endswith("天"):
                    new_label = label[:-1] + "交易日"
                norm_days, norm_unit = normalize_period_unit(new_label, int(days), unit if unit else None)
                if not unit or unit == "trading_day":
                    norm_unit = infer_unit_from_label(new_label) if "周" in new_label or "月" in new_label else norm_unit
                if norm_unit == "natural_week" and norm_days == int(days) and int(days) >= 7:
                    norm_days = int(days) // 7
                if norm_unit == "natural_month" and int(days) in (30, 60, 90):
                    norm_days = {30: 1, 60: 2, 90: 3}[int(days)]
                if new_label != label or norm_days != days or (unit or "") != norm_unit:
                    conn.execute(
                        text("UPDATE user_periods SET label = :l, days = :d, unit = :u WHERE id = :id"),
                        {"l": new_label or suggest_label(norm_unit, norm_days), "d": norm_days, "u": norm_unit, "id": pid},
                    )
                    logger.info("migration: period %s -> %s unit=%s days=%s", label, new_label, norm_unit, norm_days)

        if "tracking_nodes" in tables:
            if not _has_column("tracking_nodes", "sort_order"):
                conn.execute(text("ALTER TABLE tracking_nodes ADD COLUMN sort_order INTEGER DEFAULT 0"))
                logger.info("migration: tracking_nodes.sort_order added")
            period_rows = conn.execute(
                text("SELECT user_id, label, sort_order FROM user_periods ORDER BY user_id, sort_order")
            ).fetchall()
            period_order = {(uid, lbl): so for uid, lbl, so in period_rows}
            rec_rows = conn.execute(
                text(
                    "SELECT r.id, r.user_id, n.id, n.label, n.due_date "
                    "FROM recommendations r "
                    "JOIN tracking_nodes n ON n.recommendation_id = r.id "
                    "ORDER BY r.id, n.due_date, n.id"
                )
            ).fetchall()
            for rec_id, user_id, node_id, node_label, _due in rec_rows:
                so = period_order.get((user_id, node_label))
                if so is None:
                    so = 0
                conn.execute(
                    text("UPDATE tracking_nodes SET sort_order = :so WHERE id = :nid"),
                    {"so": so, "nid": node_id},
                )
            logger.info("migration: tracking_nodes.sort_order backfilled")

        if "invitee_notes" not in tables:
            pass
