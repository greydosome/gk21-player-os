"""Health-I/O-only fixtures for the fixed-day scalar rounding audit."""
import copy
import importlib.util
import json
from pathlib import Path
import plistlib
import uuid
s=importlib.util.spec_from_file_location('direct',Path(__file__).with_name('build_sleep_rounding_direct.py'))
d=importlib.util.module_from_spec(s); s.loader.exec_module(d); b=d.b
rows=[{'stage':'Core','Start Date':'2026-11-04T05:00:00+09:00','End Date':'2026-11-04T05:00:40+09:00'},
      {'stage':'Core','Start Date':'2026-11-04T06:00:00+09:00','End Date':'2026-11-04T06:00:40+09:00'},
      {'stage':'REM','Start Date':'2026-11-04T06:10:00+09:00','End Date':'2026-11-04T06:10:20+09:00'},
      {'stage':'Deep','Start Date':'2026-11-05T06:10:00+09:00','End Date':'2026-11-05T06:11:01+09:00'}]
wf=copy.deepcopy(d.wf); actions=[]
for a in wf['WFWorkflowActions']:
    name,p=a['WFWorkflowActionIdentifier'],a['WFWorkflowActionParameters']; ident=p['UUID']
    if name.endswith('filter.health.quantity'):
        stage=p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates'][2]['Values']['String']
        a={'WFWorkflowActionIdentifier':'is.workflow.actions.list','WFWorkflowActionParameters':{'UUID':ident,'WFItems':[json.dumps(r) for r in rows if r['stage']==stage]}}
    elif name.endswith('properties.health.quantity'):
        parsed=str(uuid.uuid4()).upper()
        actions.append({'WFWorkflowActionIdentifier':'is.workflow.actions.detect.dictionary','WFWorkflowActionParameters':{'UUID':parsed,'WFInput':p['WFInput']}})
        a={'WFWorkflowActionIdentifier':'is.workflow.actions.getvalueforkey','WFWorkflowActionParameters':{'UUID':ident,'WFGetDictionaryValueType':'Value','WFDictionaryKey':p['WFContentItemPropertyName'],'WFInput':b.attachment(b.output(parsed,'Dictionary'))}}
    elif name.endswith('showresult'):
        a={'WFWorkflowActionIdentifier':'is.workflow.actions.gettext','WFWorkflowActionParameters':{'UUID':ident,'WFTextActionText':p['Text']}}
    actions.append(a)
wf['WFWorkflowActions']=actions
p=b.OUT/'GK21-Direct-Rounding-Test.unsigned.shortcut'; p.write_bytes(plistlib.dumps(wf)); print(p)
print('Expected Core 80 seconds/2 minutes, REM 20/0, Deep 0/0 (next day excluded).')
