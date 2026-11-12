"""Enrich an existing confirmed meal without inventing a new consumption report."""
import hashlib
import json
from sqlalchemy import text
from app.schemas.meal_report import MealReport
from app.services.meal_reports import save_report

FIELDS = {'kcal', 'protein_g', 'carbohydrate_g', 'fat_g', 'nutrition_source', 'nutrition_basis', 'estimated'}

def enrich(conn, conversation_id, meal_key, expected_revision, updates):
    operation = dict(conversation_id=conversation_id, meal_key=meal_key,
                     expected_revision=expected_revision, updates=updates)
    event_id = 'nutrition:' + hashlib.sha256(json.dumps(operation, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    conn.execute(text('SELECT pg_advisory_xact_lock(2103, 1)'))
    params = {'c': conversation_id, 'k': meal_key, 'm': event_id}
    if conn.execute(text('SELECT 1 FROM meal_conversation_event WHERE conversation_id=:c AND meal_key=:k AND message_id=:m'), params).scalar():
        return {'success': True, 'status': 'unchanged', 'message_id': event_id}
    row = conn.execute(text('SELECT payload,revision,deleted FROM meal_conversation_entry WHERE conversation_id=:c AND meal_key=:k'), params).mappings().one()
    if row['deleted'] or row['revision'] != expected_revision:
        raise ValueError('Revision conflict or deleted meal')
    payload = json.loads(json.dumps(row['payload']))
    for update in updates:
        if set(update) - {'index', 'name', *FIELDS}:
            raise ValueError('Only nutrition fields may change')
        index = update['index']
        if type(index) is not int or not 0 <= index < len(payload['foods']):
            raise ValueError('Invalid food index')
        food = payload['foods'][index]
        if food['name'] != update['name'] or update.get('kcal') is None:
            raise ValueError('Food mismatch or missing calories')
        food.update({k: v for k, v in update.items() if k in FIELDS})
    if not updates:
        raise ValueError('Nutrition updates required')
    payload.update(message_id=event_id, kind='correction', expected_revision=expected_revision)
    result = save_report(conn, MealReport(**payload))
    return {**result, 'message_id': event_id}
