"""Run via the existing host scheduler. No scheduling side effects on import."""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.services.health_coaching import run_health_coaching


def main():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    if now.hour < 11:
        print("not_due")
        return
    status = run_health_coaching(now.date())
    print(status)  # No payloads or secrets in scheduler logs.
    if status in {"failed", "retry_limit"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
