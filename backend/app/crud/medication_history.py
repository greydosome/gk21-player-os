from sqlalchemy import text

from app.db.session import engine


def get_medication_history():
    # 복용한 약({name, category}) 목록을 최근 기록일 순으로 모아 반환한다.
    # general_food_items와 같은 관례: 백엔드는 내용을 해석하지 않고 그대로 flatten해서 넘긴다.
    sql = text("""
        SELECT medication_items
        FROM day_record
        WHERE medication_items IS NOT NULL
        ORDER BY record_date DESC
        LIMIT 200
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).scalars().all()

    items: list[dict] = []
    for row in rows:
        items.extend(row or [])

    return items
