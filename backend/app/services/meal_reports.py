import json
from sqlalchemy import text
from app.core.config import settings

def save_report(conn, report):
    if not settings.MEAL_CONVERSATION_ENABLED:
        raise ValueError('Integration disabled')
    if report.kind not in ('consumed','correction','delete') or not report.confirmed_by_user:
        return {'success': True, 'status': 'skipped_not_confirmed_consumption'}
    # One small owner ledger; serialize both message and meal keys to prevent race duplicates.
    conn.execute(text('SELECT pg_advisory_xact_lock(2103, 1)'))
    payload = report.model_dump(mode='json')
    params = dict(c=report.conversation_id, m=report.message_id, k=report.meal_key,
                  day=report.record_date, p=json.dumps(payload), deleted=report.kind=='delete')
    old = conn.execute(text('SELECT payload FROM meal_conversation_event WHERE conversation_id=:c AND message_id=:m AND meal_key=:k'), params).scalar()
    if old is not None:
        if old != payload:
            raise ValueError('Message content conflict')
        return {'success':True, 'status':'unchanged'}
    current = conn.execute(text('SELECT revision,deleted FROM meal_conversation_entry WHERE conversation_id=:c AND meal_key=:k'),params).mappings().first()
    revision = current['revision'] if current else 0
    if revision != report.expected_revision:
        raise ValueError('Revision conflict; read current state before correcting')
    if (current and report.kind == 'consumed') or (not current and report.kind != 'consumed'):
        raise ValueError('Explicit correction of existing meal required')
    params['revision'] = revision+1
    conn.execute(text('INSERT INTO meal_conversation_event (conversation_id,message_id,meal_key,payload) VALUES (:c,:m,:k,CAST(:p AS jsonb))'),params)
    conn.execute(text("""INSERT INTO meal_conversation_entry
        (conversation_id,meal_key,record_date,revision,deleted,payload) VALUES (:c,:k,:day,:revision,:deleted,CAST(:p AS jsonb))
        ON CONFLICT(conversation_id,meal_key) DO UPDATE SET record_date=excluded.record_date,
        revision=excluded.revision,deleted=excluded.deleted,payload=excluded.payload,updated_at=now()"""),params)
    return {'success':True,'status':'processed','revision':revision+1}

def read_meals(conn, day, include_deleted=False):
    if not settings.MEAL_CONVERSATION_ENABLED:
        return {'enabled':False,'entries':[]}
    rows=conn.execute(text('SELECT conversation_id,meal_key,revision,deleted,payload FROM meal_conversation_entry WHERE record_date=:day AND (:all OR NOT deleted) ORDER BY updated_at,meal_key LIMIT 256'), {'day':day,'all':include_deleted}).mappings()
    return {'enabled':True,'entries':[dict(r) for r in rows]}
