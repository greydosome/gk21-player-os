"""Normalize Health Auto Export v2 summaries; discard unrelated health fields.

Sources: healthyapps.dev export-format/{health-metrics,workouts}.
Configure one preferred sleep source, summarized daily sleep, no routes or
workout time-series. Preserve individual workout IDs for retry-safe ingestion.
"""
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.schemas.apple_health import AppleHealthRequest
from app.services.apple_health import read_health, save_health

KOREA = ZoneInfo("Asia/Seoul")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    try:
        result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("offset required")
    return result


def number(value, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("number required")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("number out of range")
    return float(value)


def normalize(payload, now):
    if not isinstance(payload, dict):
        raise ValueError("object required")
    data = payload.get("data", payload)
    if not isinstance(data, dict) or not ({"metrics", "workouts"} & data.keys()):
        raise ValueError("export data required")
    sleep, workouts = {}, {}
    for metric in data.get("metrics", []):
        if metric.get("name") != "sleep_analysis":
            continue
        if metric.get("units") != "hr":
            raise ValueError("sleep hours required")
        for item in metric.get("data", []):
            # Raw stage samples must not be summed here. Ambiguous sources fail
            # closed instead of reproducing the rolling-window overcount.
            if "totalSleep" not in item:
                raise ValueError("daily summarized sleep required")
            day = timestamp(item["date"]).astimezone(KOREA).date()
            hours = number(item["totalSleep"], 0, 24)
            if day in sleep:
                raise ValueError("one preferred sleep source per day required")
            sleep[day] = hours
    for item in data.get("workouts", []):
        identifier = item["id"]
        name = item["name"]
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128:
            raise ValueError("workout ID required")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
            raise ValueError("workout name required")
        start, end = timestamp(item["start"]), timestamp(item["end"])
        duration = number(item["duration"], 0.001, 86400)
        if end <= start or duration > (end - start).total_seconds() + 1:
            raise ValueError("invalid workout interval")
        if end > now + timedelta(minutes=5):
            raise ValueError("future workout")
        row = (name.strip(), start, end, duration)
        if identifier in workouts and workouts[identifier] != row:
            raise ValueError("conflicting workout ID")
        workouts[identifier] = row
    days = set(sleep)
    for _, start, end, _ in workouts.values():
        days.update(workout_days(start, end))
    today = now.astimezone(KOREA).date()
    if any(day < today - timedelta(days=30) or day > today for day in days):
        raise ValueError("export outside supported date range")
    return sleep, workouts


def workout_days(start, end):
    day = start.astimezone(KOREA).date()
    last = (end - timedelta(microseconds=1)).astimezone(KOREA).date()
    while day <= last:
        yield day
        day += timedelta(days=1)


def daily_workouts(rows, day):
    begin = datetime.combine(day, datetime.min.time(), KOREA)
    finish = begin + timedelta(days=1)
    result, seen = [], set()
    for row in rows:
        start, end = row["started_at"], row["ended_at"]
        overlap = (min(end, finish) - max(start, begin)).total_seconds()
        if overlap <= 0:
            continue
        identity = (row["workout_type"], start, end, row["duration_seconds"])
        if identity in seen:
            continue
        seen.add(identity)
        # Active duration can exclude pauses. Across midnight, allocate it in
        # proportion to elapsed time; the daily parts conserve the full duration.
        minutes = float(row["duration_seconds"]) * overlap / (end - start).total_seconds() / 60
        result.append({"workout_type": row["workout_type"], "minutes": minutes})
    return result


def save_export(conn, payload, now):
    sleep, workouts = normalize(payload, now)
    # Serialize read/aggregate/write, including multi-request export batches.
    conn.execute(text("SELECT pg_advisory_xact_lock(2102, 1)"))
    changed_days = set()
    for identifier, (name, start, end, duration) in workouts.items():
        changed_days.update(workout_days(start, end))
        old = conn.execute(text("SELECT * FROM apple_health_workout WHERE external_id=:id FOR UPDATE"), {"id": identifier}).mappings().first()
        if old and (old["workout_type"], old["started_at"], old["ended_at"], float(old["duration_seconds"])) == (name, start, end, duration):
            continue
        if old:
            changed_days.update(workout_days(old["started_at"], old["ended_at"]))
        conn.execute(text("""INSERT INTO apple_health_workout(external_id,workout_type,started_at,ended_at,duration_seconds)
            VALUES (:id,:name,:start,:end,:duration)
            ON CONFLICT(external_id) DO UPDATE SET workout_type=EXCLUDED.workout_type,
            started_at=EXCLUDED.started_at, ended_at=EXCLUDED.ended_at,
            duration_seconds=EXCLUDED.duration_seconds, received_at=now()"""),
            {"id": identifier, "name": name, "start": start, "end": end, "duration": duration})
    statuses = {}
    for day in sorted(set(sleep) | changed_days):
        summary = {}
        if sleep.get(day, 0) > 0:
            summary["sleep_hours"] = sleep[day]
        if day in changed_days:
            begin = datetime.combine(day, datetime.min.time(), KOREA)
            rows = conn.execute(text("SELECT * FROM apple_health_workout WHERE started_at < :finish AND ended_at > :begin ORDER BY started_at,external_id"),
                                {"begin": begin, "finish": begin + timedelta(days=1)}).mappings().all()
            summary["workouts"] = daily_workouts(rows, day)
        existing = read_health(conn, day).get("summary", {})
        if not summary or all(existing.get(key) == value for key, value in summary.items()):
            statuses[str(day)] = "unchanged"
            continue
        req = AppleHealthRequest(record_date=day, collected_at=now, summary=summary)
        statuses[str(day)] = save_health(conn, req)
    return {"success": True, "dates": statuses}
