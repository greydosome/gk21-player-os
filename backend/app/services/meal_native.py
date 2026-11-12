"""Project confirmed meal ledger into existing diary food controls, without overwriting edits."""
import json
import re
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from sqlalchemy import text
from fastapi import HTTPException
from app.core.config import settings

FIELDS = ('protein_items', 'carb_items', 'fat_items', 'general_food_items')
CATALOG = {
    '달걀': ('protein', '개', 100), '참치 마일드': ('protein', 'g', 1.26),
    '닭가슴살': ('protein', 'g', 1), '닭가슴살스팸': ('protein', 'g', 1.7),
    '햇반': ('carb', 'g', 1.5), '생고구마': ('carb', 'g', 1.2), '감자': ('carb', 'g', .8),
    '아보카도': ('fat', 'g', 1.6), '브로콜리': ('fat', 'g', .3),
}
MEALS = {'breakfast': '아침', 'lunch': '점심', 'dinner': '저녁'}

def rounded(n):
    return int(Decimal(str(n)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def identity(raw):
    if raw.startswith('CUSTOM|'):
        p = raw.split('|')
        name = re.sub(r' \(.*\)$', '', p[1])
        name = {'더덕양념무침':'더덕무침'}.get(name,name)
        return 'custom:' + name + ':' + (p[6] if len(p)>6 else '')
    return re.sub(r' [\d.]+(?:g|개)(?=@|$)', '', raw)

def project(entries):
    result = {f: [] for f in FIELDS}
    counts = defaultdict(float)
    for entry in entries:
        payload = entry['payload']; meal = MEALS.get(payload['meal_type'], '')
        for food in payload['foods']:
            name = food['name'].replace('|', '')
            name = {'닭가슴살 스팸':'닭가슴살스팸'}.get(name,name)
            quantity = food.get('quantity') or ''
            # Only exact catalog names and explicit quantities map to catalog buttons.
            item = CATALOG.get(name)
            if name in ('닭가슴살스팸','참치 마일드'):
                can = re.fullmatch(r'(\d+)(?:/(\d+))?캔',quantity)
                if can and (not can[2] or int(can[2])>0):
                    grams=(200 if name=='닭가슴살스팸' else 90)*int(can[1])/int(can[2] or 1)
                    quantity=f'{grams:.3f}g'
            if quantity.replace(' ','')=='반개':quantity='0.5개'
            match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(g|개)\s*', quantity)
            if item and match and match[2] == item[1]:
                counts[(name, meal)] += float(match[1]); continue
            match = re.search(r'총\s*(\d+(?:\.\d+)?)\s*(g|개|인분)', quantity) or re.search(r'(\d+(?:\.\d+)?)\s*(g|개|인분)', quantity)
            amount = match[1] if match else ''
            unit = 'g' if match and match[2] == 'g' else 'count'
            # Preserve unstructured quantities in the name; never invent a numeric amount.
            if quantity and not match:
                name += ' (' + quantity.replace('|','') + ')'
            kcal = food.get('kcal')
            result['general_food_items'].append('|'.join(['CUSTOM', name, amount, unit,
                '' if kcal is None else str(kcal), 'general', meal]))
    for (name, meal), amount in counts.items():
        category, unit, _ = CATALOG[name]
        result[category+'_items'].append(f'{name} {amount:g}{unit}' + ('@'+meal if meal else ''))
    return result

def revision(conn, day):
    if not settings.MEAL_CONVERSATION_ENABLED: return None
    return conn.execute(text('SELECT revision FROM meal_native_sync WHERE record_date=:d'), {'d':day}).scalar()

def protect_form(conn, req):
    current = revision(conn, req.record_date)
    if current and current != req.meal_record_revision:
        raise HTTPException(409, '새 식단이 반영되었습니다. 새로고침 후 다시 입력해주세요.')

def sync(conn, day):
    conn.execute(text('SELECT pg_advisory_xact_lock(2101,:d)'), {'d':day.toordinal()})
    entries = conn.execute(text('SELECT payload FROM meal_conversation_entry WHERE record_date=:d AND NOT deleted ORDER BY meal_key,conversation_id'), {'d':day}).mappings().all()
    desired = project(entries)
    old = conn.execute(text('SELECT state FROM meal_native_sync WHERE record_date=:d FOR UPDATE'), {'d':day}).scalar() or {}
    day_id = conn.execute(text('INSERT INTO day_record(record_date) VALUES (:d) ON CONFLICT(record_date) DO UPDATE SET record_date=EXCLUDED.record_date RETURNING day_record_id'), {'d':day}).scalar_one()
    row = conn.execute(text('SELECT * FROM body_record WHERE day_record_id=:id FOR UPDATE'), {'id':day_id}).mappings().first()
    row = dict(row) if row else {}
    state = {}; values = {}; conflicts = []
    for field in FIELDS:
        current = list(row.get(field) or [])
        previous = old.get(field, {}).get('managed', [])
        blocked = set(old.get(field, {}).get('blocked', []))
        # A manually edited or removed imported item stays under the user's control.
        for raw in previous:
            if raw in current: current.remove(raw)
            else: blocked.add(identity(raw))
        managed = []
        for raw in desired[field]:
            key = identity(raw)
            if key in blocked or any(identity(x)==key for x in current):
                blocked.add(key); conflicts.append(key); continue
            current.append(raw); managed.append(raw)
        values[field] = current
        state[field] = {'managed':managed, 'blocked':sorted(blocked)}
    for category in ('protein','carb','fat'):
        # Preserve existing manual kcal and adjust only the managed catalog contribution.
        def kcal(items):
            total=0
            for raw in items:
                m=re.fullmatch(r'(.*) ([\d.]+)(g|개)(?:@.*)?',raw)
                if m and m[1] in CATALOG:total+=rounded(float(m[2])*CATALOG[m[1]][2])
            return total
        field=category+'_items'
        removed=[x for x in old.get(field,{}).get('managed',[]) if x in (row.get(field) or [])]
        values[category+'_kcal']=max(0,(row.get(category+'_kcal') or 0)-kcal(removed)+kcal(state[field]['managed']))
    params={'id':day_id,**{k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in values.items()}}
    columns=list(values)
    conn.execute(text('INSERT INTO body_record(day_record_id,'+','.join(columns)+') VALUES (:id,'+','.join('CAST(:'+k+' AS jsonb)' if k in FIELDS else ':'+k for k in columns)+') ON CONFLICT(day_record_id) DO UPDATE SET '+','.join(k+'=EXCLUDED.'+k for k in columns)+',updated_at=now()'),params)
    conn.execute(text('INSERT INTO meal_native_sync(record_date,state,revision) VALUES (:d,CAST(:s AS jsonb),:r) ON CONFLICT(record_date) DO UPDATE SET state=EXCLUDED.state,revision=EXCLUDED.revision'),{'d':day,'s':json.dumps(state),'r':str(uuid4())})
    return conflicts
