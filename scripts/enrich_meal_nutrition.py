#!/usr/bin/env python3
"""Run as the app account with its environment; input contains nutrition only.

Usage: backend/.venv/bin/python scripts/enrich_meal_nutrition.py /private/input.json
Input: [{conversation_id, meal_key, expected_revision, updates: [{index,name,
kcal,nutrition_source,nutrition_basis,estimated}]}]. No network or model calls.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.db.session import engine
from app.services.meal_nutrition import enrich

def main():
    operations = json.loads(Path(sys.argv[1]).read_text())
    with engine.begin() as conn:
        results = [enrich(conn, **operation) for operation in operations]
    print(json.dumps(results, ensure_ascii=False))

if __name__ == '__main__':
    main()
