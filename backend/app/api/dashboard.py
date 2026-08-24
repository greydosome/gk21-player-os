from datetime import date

from fastapi import APIRouter, Query

from app.crud.dashboard import get_active_goal, get_dashboard, get_day_detail
from app.crud.ai_analysis import get_daily_ai_analysis
from app.db.session import engine
from app.services.mission import build_today_missions
from app.services.philosophy import get_daily_philosophy

router = APIRouter()


@router.get("/api/dashboard")
def api_get_dashboard(record_date: date | None = Query(default=None)):
    target = record_date or date.today()

    # AI 코칭 대기 중 3초마다 폴링되는 엔드포인트라, 호출마다 커넥션을 4개씩
    # 따로 여는 대신 하나의 커넥션을 공유해서 풀 부담을 줄인다.
    with engine.connect() as conn:
        dashboard = get_dashboard(target, conn=conn)
        ai = get_daily_ai_analysis(target, conn=conn)
        detail = get_day_detail(target, conn=conn)
        goal = get_active_goal(conn=conn)

    missions = build_today_missions(dashboard)

    day_no = dashboard.get("day_no") if dashboard else 1
    philosophy = get_daily_philosophy(day_no)

    return {
        "success": True,
        "record_date": str(target),
        "dashboard": dashboard,
        "ai": ai,
        "missions": missions,
        "philosophy": philosophy,
        "detail": detail,
        "goal": goal,
    }
