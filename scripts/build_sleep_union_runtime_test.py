"""Native executable fixtures for overlap, midnight, sessions and missing data."""
import copy
from datetime import datetime, timedelta
import importlib.util
import json
from pathlib import Path
import plistlib
import uuid
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location('union', Path(__file__).with_name('build_sleep_union_shortcut.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
b = u.b
midnight = datetime.combine(datetime.now(ZoneInfo('Asia/Seoul')).date(), datetime.min.time(), ZoneInfo('Asia/Seoul'))


def row(stage, start_minutes, end_minutes):
    return {'stage': stage, 'Start Date': (midnight + timedelta(minutes=start_minutes)).isoformat(),
            'End Date': (midnight + timedelta(minutes=end_minutes)).isoformat()}


rows = [row('Core', -840, -780), row('Core', -60, 30), row('Core', -60, 30),
        row('Deep', 15, 60), row('REM', 60, 90), row('Core', 600, 630)]
for label, samples in {'mixed': rows, 'empty': []}.items():
    wf = copy.deepcopy(u.wf)
    actions = []
    for a in wf['WFWorkflowActions']:
        name, p = a['WFWorkflowActionIdentifier'], a['WFWorkflowActionParameters']
        identifier = p['UUID']
        if name.endswith('filter.health.quantity'):
            templates = p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates']
            stage = next((x['Values']['String'] for x in templates if x['Property'] == 'Value'), None)
            filtered = [r for r in samples if stage is None or r['stage'] == stage]
            filtered.sort(key=lambda r: r['Start Date'])
            a = {'WFWorkflowActionIdentifier': 'is.workflow.actions.list',
                 'WFWorkflowActionParameters': {'UUID': identifier, 'WFItems': [json.dumps(r) for r in filtered]}}
        elif name.endswith('properties.health.quantity'):
            parsed = str(uuid.uuid4()).upper()
            actions.append({'WFWorkflowActionIdentifier': 'is.workflow.actions.detect.dictionary',
                            'WFWorkflowActionParameters': {'UUID': parsed, 'WFInput': p['WFInput']}})
            a = {'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
                 'WFWorkflowActionParameters': {'UUID': identifier, 'WFGetDictionaryValueType': 'Value',
                     'WFDictionaryKey': p['WFContentItemPropertyName'],
                     'WFInput': b.attachment(b.output(parsed, 'Dictionary'))}}
        elif name.endswith('showresult'):
            a = {'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
                 'WFWorkflowActionParameters': {'UUID': identifier, 'WFTextActionText': p['Text']}}
        actions.append(a)
    wf.update(WFWorkflowActions=actions, WFWorkflowName='GK21 Union Test ' + label)
    destination = b.OUT / ('GK21-Union-Test-' + label + '.unsigned.shortcut')
    destination.write_bytes(plistlib.dumps(wf))
    print(destination)
print('Mixed expected: today 180 minutes; raw 345; union 240; 6 intervals')
