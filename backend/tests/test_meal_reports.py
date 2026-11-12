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
        c.exec_driver_sql((Path(__file__).parents[2]/'sql/migrations/2026-11-12_meal_native.sql').read_text().replace('BEGIN;','').replace('COMMIT;',''))
        c.exec_driver_sql('CREATE TABLE IF NOT EXISTS body_record(day_record_id bigint PRIMARY KEY, protein_items jsonb,carb_items jsonb,fat_items jsonb,general_food_items jsonb,protein_kcal integer,carb_kcal integer,fat_kcal integer,updated_at timestamptz DEFAULT now())')
        c.exec_driver_sql('TRUNCATE meal_conversation_entry,meal_conversation_event,meal_native_sync,body_record')

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


def test_native_catalog_unknown_and_correction():
    r=report(foods=[{'name':'달걀','quantity':'2개'}, {'name':'샤인머스캣','quantity':'200g'}],meal_type='breakfast')
    with engine.begin() as c:
        save_report(c,r)
        row=c.execute(text('SELECT * FROM body_record')).mappings().one()
        assert row['protein_items']==['달걀 2개@아침']
        assert row['protein_kcal']==200
        assert row['general_food_items']==['CUSTOM|샤인머스캣|200|g||general|아침']
        save_report(c,report(message_id='fix',kind='correction',expected_revision=1,meal_type='breakfast',foods=[{'name':'달걀','quantity':'3개'}]))
        row=c.execute(text('SELECT * FROM body_record')).mappings().one()
        assert row['protein_items']==['달걀 3개@아침'] and row['protein_kcal']==300
        assert row['general_food_items']==[]
        save_report(c,report(message_id='del',kind='delete',expected_revision=2,foods=[]))
        row=c.execute(text('SELECT * FROM body_record')).mappings().one()
        assert row['protein_items']==[] and row['protein_kcal']==0


def test_native_preserves_manual_and_blocks_stale_form():
    from app.services.meal_native import sync,protect_form,revision
    from app.schemas.day import DayRecordRequest
    from fastapi import HTTPException
    r=report(foods=[{'name':'달걀','quantity':'2개'}])
    with engine.begin() as c:
        save_report(c,r)
        req=DayRecordRequest(record_date=r.record_date)
        with pytest.raises(HTTPException):protect_form(c,req)
        req.meal_record_revision=revision(c,r.record_date)
        protect_form(c,req)
        c.execute(text("UPDATE body_record SET protein_items='[\"달걀 4개\"]'::jsonb,protein_kcal=400"))
        sync(c,r.record_date)
        row=c.execute(text('SELECT * FROM body_record')).mappings().one()
        assert row['protein_items']==['달걀 4개'] and row['protein_kcal']==400
        save_report(c,report(message_id='del',kind='delete',expected_revision=1,foods=[]))
        assert c.execute(text('SELECT protein_kcal FROM body_record')).scalar()==400


def test_native_toast_retry_and_no_manual_collision():
    from app.services.meal_native import sync
    food={'name':'햄치즈 토스트','quantity':'1개','kcal':530,'nutrition_basis':'estimate','nutrition_source':'synthetic test source','estimated':True}
    r=report(foods=[food],meal_type='lunch')
    with engine.begin() as c:
        save_report(c,r);sync(c,r.record_date)
        assert c.execute(text('SELECT general_food_items FROM body_record')).scalar()==['CUSTOM|햄치즈 토스트|1|count|530.0|general|점심']
        assert save_report(c,r)['status']=='unchanged'
        c.execute(text("UPDATE body_record SET general_food_items='[]'::jsonb"))
        sync(c,r.record_date);sync(c,r.record_date)
        assert c.execute(text('SELECT general_food_items FROM body_record')).scalar()==[]


def test_native_quantity_and_existing_catalog():
    from app.services.meal_native import project
    result=project([{'payload':{'meal_type':'lunch','foods':[
        {'name':'꿀 스틱','quantity':'8g 2개 (총 16g)'},
        {'name':'닭가슴살 스팸','quantity':'2/3캔'},
        {'name':'사과','quantity':'반 개'}]}}])
    assert result['protein_items']==['닭가슴살스팸 133.333g@점심']
    assert 'CUSTOM|꿀 스틱|16|g||general|점심' in result['general_food_items']
    assert 'CUSTOM|사과|0.5|count||general|점심' in result['general_food_items']


def test_native_existing_food_alias_not_added_twice():
    r=report(foods=[{'name':'더덕양념무침','quantity':'조금'}],meal_type='dinner')
    with engine.begin() as c:
        day_id=c.execute(text('INSERT INTO day_record(record_date) VALUES (:d) RETURNING day_record_id'),{'d':r.record_date}).scalar()
        c.execute(text('INSERT INTO body_record(day_record_id,general_food_items) VALUES (:id,CAST(:items AS jsonb))'),{'id':day_id,'items':'["CUSTOM|더덕무침|100|g|160|general|저녁"]'})
        result=save_report(c,r)
        assert result['native_conflicts']
        assert len(c.execute(text('SELECT general_food_items FROM body_record')).scalar())==1
