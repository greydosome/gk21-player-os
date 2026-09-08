from sqlalchemy import text

from app.db.session import engine


def get_cached_medication_info(name: str):
    sql = text("""
        SELECT known, efficacy, side_effects, caution
        FROM medication_info
        WHERE name = :name
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, {"name": name}).mappings().first()

    return dict(row) if row else None


def save_medication_info(name: str, known: bool, efficacy: str | None, side_effects: str | None, caution: str | None):
    sql = text("""
        INSERT INTO medication_info (name, known, efficacy, side_effects, caution)
        VALUES (:name, :known, :efficacy, :side_effects, :caution)
        ON CONFLICT (name) DO UPDATE SET
            known = EXCLUDED.known,
            efficacy = EXCLUDED.efficacy,
            side_effects = EXCLUDED.side_effects,
            caution = EXCLUDED.caution
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "name": name,
                "known": known,
                "efficacy": efficacy,
                "side_effects": side_effects,
                "caution": caution,
            },
        )
