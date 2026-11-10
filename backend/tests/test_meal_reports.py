from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.schemas.meal_report import MealReport
from app.services.meal_reports import save_report, read_meals

@pytest.fixture(autouse=True)
def setup_meals(monkeypatch):
    monkeypatch.setattr(settings,'MEAL_CONVERSATION_ENABLED',True)
    with engine.begin() as c:
        c.exec_driver_sql((Path(__file__).parents[2]/'sql/migrations/2026-11-10_meal_conversation.sql').read_text().replace('BEGIN;','').replace('COMMIT;',''))
        c.exec_driver_sql('TRUNCATE meal_conversation_entry,meal_conversation_event')

def report(**kw):
    now=datetime.now(ZoneInfo('Asia/Seoul'))
    data=dict(conversation_id='test',message_id='one',reported_at=now,record_date=now.date(),kind='consumed',confirmed_by_user=True,meal_key='lunch-1',foods=[{'name':'rice'}])
    data.update(kw)
    return MealReport(**data)

@pytest.mark.parametrize('kind',['plan','recommendation','question'])
def test_skip(kind):
    with engine.begin() as c:
        assert save_report(c,report(kind=kind))['status'].startswith('skipped')
        assert not read_meals(c,report().record_date)['entries']

def test_duplicate_correction_delete():
    r=report()
    with engine.begin() as c:
        assert save_report(c,r)['revision']==1
        assert save_report(c,r)['status']=='unchanged'
        with pytest.raises(ValueError):save_report(c,r.model_copy(update={'foods':[]}))
        correction=report(message_id='two',kind='correction',expected_revision=1,foods=[{'name':'rice','quantity':'half bowl'}])
        assert save_report(c,correction)['revision']==2
        with pytest.raises(ValueError):save_report(c,report(message_id='stale',kind='correction',expected_revision=1))
        assert save_report(c,report(message_id='three',kind='delete',expected_revision=2,foods=[]))['revision']==3
        assert not read_meals(c,r.record_date)['entries']
        assert save_report(c,r)['status']=='unchanged'
        assert not read_meals(c,r.record_date)['entries']
        assert read_meals(c,r.record_date,True)['entries'][0]['deleted']

def test_unconfirmed_and_unknown_nutrition():
    with engine.begin() as c:
        assert save_report(c,report(confirmed_by_user=False))['status'].startswith('skipped')
    with pytest.raises(ValueError):report(foods=[{'name':'rice','kcal':200}])
    r=report(foods=[{'name':'rice','kcal':200,'nutrition_source':'user label','nutrition_basis':'label','estimated':False}])
    assert r.foods[0].kcal==200

def test_auth_and_api(monkeypatch):
    import hashlib
    token='synthetic-meal-upload-token-12345'
    monkeypatch.setattr(settings,'APPLE_HEALTH_TOKEN_SHA256',hashlib.sha256(token.encode()).hexdigest())
    client=TestClient(app,base_url='https://testserver')
    r=report()
    url='/api/integrations/meal-reports'
    assert client.post(url,json=r.model_dump(mode='json')).status_code==401
    headers={'Authorization':'Bearer '+token}
    assert client.post(url,json=r.model_dump(mode='json'),headers=headers).status_code==200
    response=client.get('/api/consumed-meals',params={'record_date':str(r.record_date)})
    assert len(response.json()['entries'])==1
    monkeypatch.setattr(settings,'MEAL_CONVERSATION_ENABLED',False)
    assert client.post(url,json=r.model_dump(mode='json'),headers=headers).status_code==404

def test_one_message_can_report_two_meals_and_manual_data_survives():
    r=report()
    with engine.begin() as c:
        c.execute(text("INSERT INTO day_record(record_date,memo) VALUES (:day,'manual note')"),{'day':r.record_date})
        save_report(c,r)
        breakfast=report(reported_at=r.reported_at,meal_key='breakfast-1',meal_type='breakfast')
        save_report(c,breakfast)
        assert len(read_meals(c,r.record_date)['entries'])==2
        assert c.execute(text('SELECT memo FROM day_record WHERE record_date=:day'),{'day':r.record_date}).scalar()=='manual note'
        assert c.execute(text('SELECT count(*) FROM meal_conversation_event')).scalar()==2
        assert save_report(c,breakfast)['status']=='unchanged'

def test_rejected_http_transport_limits_and_provenance(monkeypatch):
    import hashlib
    token='synthetic-meal-upload-token-12345'
    monkeypatch.setattr(settings,'APPLE_HEALTH_TOKEN_SHA256',hashlib.sha256(token.encode()).hexdigest())
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
    url='/api/integrations/meal-reports'
    assert TestClient(app,base_url='http://testserver').post(url,json=report().model_dump(mode='json'),headers=headers).status_code==403
    client=TestClient(app,base_url='https://testserver')
    assert client.post(url,content=b'x'*32769,headers=headers).status_code==413
    assert client.post(url,json=report().model_dump(mode='json'),headers={**headers,'Origin':'https://elsewhere.test'}).status_code==403
    for food in ({'name':'x','kcal':float('nan')},{'name':'x','nutrition_basis':'estimate','estimated':False}):
        with pytest.raises(ValueError):report(foods=[food])
    with engine.connect() as c:
        assert c.execute(text('SELECT count(*) FROM meal_conversation_event')).scalar()==0
