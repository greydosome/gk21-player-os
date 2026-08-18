from sqlalchemy import text

from app.db.session import engine


def get_general_food_history():
    # 일반식(직접입력) 항목을 최근 기록일 순으로 모아 반환한다.
    # 인코딩 포맷("CUSTOM|이름|수량|단위|칼로리")은 프론트엔드 전용 표현이라
    # 백엔드는 내용을 해석하지 않고 그대로 flatten해서 넘긴다 (protein_items 등과 동일한 관례).
    sql = text("""
        SELECT br.general_food_items
        FROM body_record br
        JOIN day_record dr ON br.day_record_id = dr.day_record_id
        WHERE br.general_food_items IS NOT NULL
        ORDER BY dr.record_date DESC
        LIMIT 200
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).scalars().all()

    items: list[str] = []
    for row in rows:
        items.extend(row or [])

    return items
