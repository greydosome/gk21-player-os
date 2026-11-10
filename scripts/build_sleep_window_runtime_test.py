"""Replace only Health I/O to exercise sleep window boundaries in Shortcuts.

Expected midnight: Core60, REM100, Deep0; noon: Core100, REM0, Deep0.
The 23:59 interval and exact-noon interval test start-time attribution.
"""
import copy,importlib.util,json,plistlib,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('build_sleep_window_audit.py'))
d=importlib.util.module_from_spec(s); s.loader.exec_module(d); b=d.b
rows=[('Core','2026-11-03T23:59:40+09:00','2026-11-04T00:00:20+09:00'),('Core','2026-11-04T01:00:00+09:00','2026-11-04T01:01:00+09:00'),('REM','2026-11-04T12:00:00+09:00','2026-11-04T12:01:40+09:00'),('Deep','2026-11-05T06:00:00+09:00','2026-11-05T06:01:00+09:00')]
w=copy.deepcopy(d.workflow); actions=[]
for a in w['WFWorkflowActions']:
 name,p=a['WFWorkflowActionIdentifier'],a['WFWorkflowActionParameters']; ident=p['UUID']
 if name.endswith('filter.health.quantity'):
  stage=p['WFContentItemFilter']['Value']['WFActionParameterFilterTemplates'][2]['Values']['String']
  a={'WFWorkflowActionIdentifier':'is.workflow.actions.list','WFWorkflowActionParameters':{'UUID':ident,'WFItems':[json.dumps({'Start Date':start,'End Date':end}) for kind,start,end in rows if kind==stage]}}
 elif name.endswith('properties.health.quantity'):
  parsed=str(uuid.uuid4()).upper(); actions.append({'WFWorkflowActionIdentifier':'is.workflow.actions.detect.dictionary','WFWorkflowActionParameters':{'UUID':parsed,'WFInput':p['WFInput']}})
  a={'WFWorkflowActionIdentifier':'is.workflow.actions.getvalueforkey','WFWorkflowActionParameters':{'UUID':ident,'WFGetDictionaryValueType':'Value','WFDictionaryKey':p['WFContentItemPropertyName'],'WFInput':b.attachment(b.output(parsed,'Dictionary'))}}
 elif name.endswith('showresult'):
  a={'WFWorkflowActionIdentifier':'is.workflow.actions.gettext','WFWorkflowActionParameters':{'UUID':ident,'WFTextActionText':p['Text']}}
 actions.append(a)
w['WFWorkflowActions']=actions
(b.OUT / 'GK21-Window-Runtime-Test.unsigned.shortcut').write_bytes(plistlib.dumps(w))
print('Expected midnight Core60 REM100 Deep0; noon Core100 REM0 Deep0. Boundary start at noon excluded.')
